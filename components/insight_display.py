# components/insight_display.py

import streamlit as st

# Maps insight type to color + emoji
INSIGHT_STYLE = {
    "positive":  {"emoji": "📈", "color": "#22c55e", "bg": "#f0fdf4"},
    "negative":  {"emoji": "📉", "color": "#ef4444", "bg": "#fef2f2"},
    "neutral":   {"emoji": "💡", "color": "#3b82f6", "bg": "#eff6ff"},
    "warning":   {"emoji": "⚠️", "color": "#f59e0b", "bg": "#fffbeb"},
}

CONFIDENCE_STYLE = {
    "high":   ("🟢", "High Confidence"),
    "medium": ("🟡", "Medium Confidence"),
    "low":    ("🔴", "Low Confidence"),
}


def render_insight_cards(insight_data: dict, question: str = ""):
    """
    Renders structured insight data as Streamlit UI components.

    Args:
        insight_data: The parsed dict from insight_engine.generate_insights()
        question: The original user question (optional, for context header)
    """

    if not insight_data.get("success"):
        st.error(f"Could not generate insights: {insight_data.get('error')}")
        return

    data = insight_data["data"]

    # ── Section header ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🧠 AI Business Insights")

    if question:
        st.caption(f"Analysis of: *{question}*")

    # ── Executive Summary ────────────────────────────────────────
    summary = data.get("summary", "")
    if summary:
        st.info(f"**Executive Summary:** {summary}")

    # ── Confidence Badge ─────────────────────────────────────────
    confidence = data.get("confidence", "medium")
    conf_icon, conf_label = CONFIDENCE_STYLE.get(confidence, ("🟡", "Medium Confidence"))
    st.caption(f"{conf_icon} {conf_label}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Insight Cards ────────────────────────────────────────────
    insights = data.get("insights", [])

    if not insights:
        st.warning("No insights were generated.")
        return

    # Render cards in columns (max 3 per row)
    cols = st.columns(min(len(insights), 3))

    for i, insight in enumerate(insights):
        col = cols[i % 3]
        insight_type = insight.get("type", "neutral")
        style = INSIGHT_STYLE.get(insight_type, INSIGHT_STYLE["neutral"])

        with col:
            st.markdown(
                f"""
                <div style="
                    background-color: {style['bg']};
                    border-left: 4px solid {style['color']};
                    border-radius: 8px;
                    padding: 16px 18px;
                    margin-bottom: 12px;
                    min-height: 120px;
                ">
                    <div style="font-size: 1.4rem; margin-bottom: 6px;">
                        {style['emoji']}
                    </div>
                    <div style="
                        font-weight: 700;
                        font-size: 0.95rem;
                        color: {style['color']};
                        margin-bottom: 6px;
                    ">
                        {insight.get('title', '')}
                    </div>
                    <div style="
                        font-size: 0.88rem;
                        color: #374151;
                        line-height: 1.5;
                    ">
                        {insight.get('detail', '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ── Recommendation ───────────────────────────────────────────
    recommendation = data.get("recommendation", "")
    if recommendation:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #667eea22, #764ba222);
                border: 1px solid #667eea55;
                border-radius: 10px;
                padding: 16px 20px;
            ">
                <span style="font-weight: 700; color: #4f46e5;">
                    💼 Recommendation:
                </span>
                <span style="color: #1f2937; margin-left: 8px;">
                    {recommendation}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")


def render_insight_history(history: list):
    """
    Renders a collapsible history of all insights generated in the session.

    Args:
        history: List of dicts, each with keys: question, insight_data
    """

    if not history:
        return

    with st.expander(f"📚 Insight History ({len(history)} analyses)", expanded=False):
        for i, entry in enumerate(reversed(history)):
            st.markdown(f"**Q{len(history) - i}:** {entry['question']}")
            summary = entry.get("insight_data", {}).get("data", {}).get("summary", "")
            if summary:
                st.caption(f"→ {summary}")
            st.markdown("---")