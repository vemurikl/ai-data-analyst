"""
Auto-dashboard generator.
Produces business and quality charts directly from a DataFrame
without going through the ReAct agent.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,250,252,0.8)",
    font_color="#64748b",
    title_font_color="#0f172a",
    title_font_size=14,
    margin=dict(l=16, r=16, t=40, b=16),
    colorway=["#2563eb", "#16a34a", "#7c3aed", "#d97706", "#dc2626", "#0891b2"],
)

_AXIS = dict(
    gridcolor="rgba(226,232,240,0.8)",
    linecolor="rgba(226,232,240,0.8)",
    tickfont_color="#94a3b8",
)


def _smart_cols(df: pd.DataFrame):
    """Return (cat_cols, num_cols, date_cols) in order of interest."""
    cat  = [c for c in df.columns if df[c].dtype == object and 1 < df[c].nunique() <= 60]
    num  = df.select_dtypes(include="number").columns.tolist()
    date = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    # Also check object cols that look like dates
    for c in df.select_dtypes(include="object").columns:
        try:
            pd.to_datetime(df[c].dropna().head(50), infer_datetime_format=True)
            if c not in date:
                date.append(c)
                if c in cat:
                    cat.remove(c)
        except Exception:
            pass
    return cat, num, date


# ── Business Charts ──────────────────────────────────────────────────────────

def build_business_dashboard(df: pd.DataFrame) -> list[go.Figure]:
    cat, num, date = _smart_cols(df)
    charts = []

    # 1. KPI summary cards (top numeric stats as big-number chart)
    if num:
        kpi_cols = num[:6]
        stats = {c: df[c].dropna() for c in kpi_cols}
        fig = go.Figure()
        for i, c in enumerate(kpi_cols):
            s = stats[c]
            fig.add_trace(go.Indicator(
                mode="number+delta",
                value=round(s.mean(), 2),
                title={"text": c.replace("_", " ").title(), "font": {"size": 12, "color": "#94a3b8"}},
                number={"font": {"size": 26, "color": "#60a5fa"}},
                delta={"reference": s.median(), "relative": False,
                       "increasing": {"color": "#22c55e"}, "decreasing": {"color": "#f87171"}},
                domain={"row": i // 3, "column": i % 3},
            ))
        rows = (len(kpi_cols) + 2) // 3
        fig.update_layout(
            title="KPI Summary — Mean vs Median",
            grid={"rows": rows, "columns": 3, "pattern": "independent"},
            height=180 * rows,
            **_DARK,
        )
        charts.append(("KPI Summary", fig))

    # 2. Top category bar charts (first 2 cat cols)
    for col in cat[:2]:
        vc = df[col].value_counts().head(15)
        fig = px.bar(
            x=vc.values, y=vc.index, orientation="h",
            title=f"Top Values — {col.replace('_',' ').title()}",
            labels={"x": "Count", "y": col},
            color=vc.values,
            color_continuous_scale="Blues",
        )
        fig.update_layout(**_DARK)
        fig.update_xaxes(**_AXIS)
        fig.update_yaxes(**_AXIS)
        fig.update_coloraxes(showscale=False)
        charts.append((col.replace("_", " ").title(), fig))

    # 3. Avg numeric by top category
    if cat and num:
        for c in cat[:1]:
            for n in num[:2]:
                grp = df.groupby(c)[n].mean().sort_values(ascending=False).head(12)
                fig = px.bar(
                    x=grp.index, y=grp.values,
                    title=f"Avg {n.replace('_',' ').title()} by {c.replace('_',' ').title()}",
                    labels={"x": c, "y": f"Avg {n}"},
                    color=grp.values,
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(**_DARK)
                fig.update_xaxes(**_AXIS)
                fig.update_yaxes(**_AXIS)
                fig.update_coloraxes(showscale=False)
                charts.append((f"Avg {n.replace('_',' ').title()} by {c.replace('_',' ').title()}", fig))

    # 4. Numeric distributions (histogram grid)
    if num:
        show = num[:6]
        cols = min(3, len(show))
        rows = (len(show) + cols - 1) // cols
        fig = make_subplots(rows=rows, cols=cols,
                            subplot_titles=[c.replace("_", " ").title() for c in show])
        for i, c in enumerate(show):
            fig.add_trace(
                go.Histogram(x=df[c].dropna(), name=c, marker_color="#3b82f6",
                             opacity=0.8, showlegend=False),
                row=i // cols + 1, col=i % cols + 1,
            )
        fig.update_layout(title="Numeric Distributions", height=280 * rows, **_DARK)
        for ax in fig.layout:
            if ax.startswith("xaxis") or ax.startswith("yaxis"):
                fig.layout[ax].update(**_AXIS)
        charts.append(("Distributions", fig))

    # 5. Time series if date + numeric
    if date and num:
        dcol = date[0]
        try:
            ts = df.copy()
            ts[dcol] = pd.to_datetime(ts[dcol], infer_datetime_format=True, errors="coerce")
            ts = ts.dropna(subset=[dcol]).sort_values(dcol)
            for ncol in num[:3]:
                agg = ts.groupby(dcol)[ncol].sum().reset_index()
                fig = px.line(
                    agg, x=dcol, y=ncol,
                    title=f"{ncol.replace('_',' ').title()} over Time",
                    labels={dcol: "Date", ncol: ncol.replace("_", " ").title()},
                )
                fig.update_traces(line_color="#3b82f6", line_width=2)
                fig.update_layout(**_DARK)
                fig.update_xaxes(**_AXIS)
                fig.update_yaxes(**_AXIS)
                charts.append((f"{ncol.replace('_',' ').title()} Trend", fig))
        except Exception:
            pass

    # 6. Correlation heatmap
    if len(num) >= 3:
        corr_cols = num[:12]
        corr = df[corr_cols].corr().round(2)
        fig = px.imshow(
            corr,
            title="Correlation Matrix",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            text_auto=True,
        )
        fig.update_layout(**_DARK)
        charts.append(("Correlations", fig))

    return charts


# ── Quality Charts ───────────────────────────────────────────────────────────

def build_quality_dashboard(df: pd.DataFrame, cleaning_report=None) -> list[go.Figure]:
    charts = []
    _, num, _ = _smart_cols(df)

    # 1. Completeness gauge
    completeness = (1 - df.isnull().sum().sum() / df.size) * 100
    bar_color = "#22c55e" if completeness > 90 else "#fbbf24" if completeness > 75 else "#f87171"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(completeness, 1),
        title={"text": "Data Completeness %", "font": {"color": "#e2e8f0", "size": 15}},
        number={"suffix": "%", "font": {"color": bar_color, "size": 40}},
        delta={"reference": 100, "relative": False,
               "decreasing": {"color": "#f87171"}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": "#64748b"}},
            "bar": {"color": bar_color, "thickness": 0.25},
            "bgcolor": "rgba(15,23,42,0.4)",
            "bordercolor": "rgba(51,65,85,0.4)",
            "steps": [
                {"range": [0,  75], "color": "rgba(239,68,68,0.08)"},
                {"range": [75, 90], "color": "rgba(245,158,11,0.08)"},
                {"range": [90, 100],"color": "rgba(34,197,94,0.08)"},
            ],
            "threshold": {"line": {"color": "#e2e8f0", "width": 2}, "value": 90},
        },
    ))
    fig.update_layout(height=280, **_DARK)
    charts.append(("Data Quality Score", fig))

    # 2. Missing values per column
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=True)
    if not missing.empty:
        pct = (missing / len(df) * 100).round(1)
        fig = px.bar(
            x=pct.values, y=pct.index, orientation="h",
            title="Missing Values by Column (%)",
            labels={"x": "Missing %", "y": "Column"},
            color=pct.values,
            color_continuous_scale="Reds",
        )
        fig.update_layout(**_DARK)
        fig.update_xaxes(**_AXIS)
        fig.update_yaxes(**_AXIS)
        fig.update_coloraxes(showscale=False)
        charts.append(("Missing Values", fig))
    else:
        fig = go.Figure()
        fig.add_annotation(text="✅ No missing values", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font={"size": 18, "color": "#22c55e"})
        fig.update_layout(title="Missing Values", **_DARK)
        charts.append(("Missing Values", fig))

    # 3. Data types breakdown
    dtype_map = {
        "int64": "Integer", "float64": "Float", "object": "Text",
        "datetime64[ns]": "Date", "bool": "Boolean",
    }
    dtypes = df.dtypes.astype(str).map(lambda x: dtype_map.get(x, x)).value_counts()
    fig = px.pie(
        values=dtypes.values, names=dtypes.index,
        title="Column Data Types",
        color_discrete_sequence=["#3b82f6", "#22c55e", "#a78bfa", "#fbbf24", "#f87171"],
        hole=0.4,
    )
    fig.update_layout(**_DARK)
    fig.update_traces(textfont_color="#e2e8f0")
    charts.append(("Data Types", fig))

    # 4. Outlier box plots
    if num:
        show = num[:8]
        fig = go.Figure()
        for c in show:
            fig.add_trace(go.Box(
                y=df[c].dropna(), name=c.replace("_", " ").title(),
                marker_color="#3b82f6", line_color="#3b82f6",
                boxmean="sd", showlegend=False,
            ))
        fig.update_layout(title="Outlier Detection — Numeric Columns",
                          height=380, **_DARK)
        fig.update_xaxes(**_AXIS)
        fig.update_yaxes(**_AXIS)
        charts.append(("Outlier Detection", fig))

    # 5. Cleaning actions summary
    if cleaning_report and cleaning_report.actions:
        actions = cleaning_report.actions
        severity_counts = {}
        for a in actions:
            severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
        colors = {"high": "#f87171", "medium": "#fbbf24", "low": "#4ade80"}
        fig = go.Figure(go.Bar(
            x=list(severity_counts.keys()),
            y=list(severity_counts.values()),
            marker_color=[colors.get(k, "#60a5fa") for k in severity_counts],
            text=list(severity_counts.values()),
            textposition="outside",
            textfont_color="#e2e8f0",
        ))
        fig.update_layout(title="Cleaning Actions by Severity",
                          xaxis_title="Severity", yaxis_title="Count", **_DARK)
        fig.update_xaxes(**_AXIS)
        fig.update_yaxes(**_AXIS)
        charts.append(("Cleaning Summary", fig))

    return charts
