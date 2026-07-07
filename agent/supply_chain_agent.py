"""
Supply Chain Data Analyst Agent
All agent logic in one place: memory, cleaning, code execution, insights,
ReAct loop, explanation, and the top-level orchestrator.

Specialized for supply chain companies (Jabil, Nvidia, TSMC, Foxconn, etc.)
and the metrics they care about: lead time, fill rate, OTIF, inventory turns,
supplier scorecards, shortage risk, and demand forecasting.
"""

import os
import re
import json
import traceback
import anthropic
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from dotenv import load_dotenv
from utils.data_profiler import profile_dataset

MODEL = "claude-sonnet-4-20250514"

SUPPLY_CHAIN_COMPANIES = [
    "Jabil", "Nvidia", "TSMC", "Foxconn", "Flex", "Celestica",
    "Apple", "Samsung", "Intel", "Qualcomm", "Broadcom", "AMD",
    "Toyota", "Honeywell", "Siemens", "Bosch", "3M"
]

# KPIs organized by the 6 supply chain modules
MODULE_KPIS: dict[str, dict] = {
    "Inventory": {
        "icon": "📦",
        "kpis": [
            "inventory turns", "days of supply (DOS)", "safety stock level",
            "reorder point (ROP)", "economic order quantity (EOQ)",
            "shortage / stockout rate", "dead stock %", "aging inventory",
            "ABC classification", "cycle count accuracy", "inventory carrying cost",
            "shrinkage rate", "min/max levels",
        ],
        "questions": [
            "What is the inventory turnover by SKU or category?",
            "Which items are overstocked or at risk of stockout?",
            "Show aging inventory — items with no movement in 90+ days.",
            "What is the days of supply for each product group?",
        ],
    },
    "Supplier Performance": {
        "icon": "🤝",
        "kpis": [
            "OTIF (On Time In Full)", "supplier scorecard", "defect rate (PPM)",
            "on-time delivery %", "supplier concentration risk",
            "quality escape rate", "corrective action (CAPA) rate",
            "delivery performance %", "response time SLA compliance",
            "supplier diversification index", "approved vendor list (AVL) coverage",
        ],
        "questions": [
            "Which suppliers have the worst OTIF performance?",
            "Rank suppliers by defect rate over the last quarter.",
            "Which suppliers represent more than 20% of our spend (concentration risk)?",
            "Show on-time delivery trend by supplier.",
        ],
    },
    "Procurement": {
        "icon": "🏭",
        "kpis": [
            "procurement spend", "purchase price variance (PPV)",
            "PO cycle time", "contract compliance %", "maverick spend %",
            "spend under management", "cost avoidance", "cost savings %",
            "supplier payment terms (DPO)", "contract coverage %",
            "requisition-to-PO cycle time", "MOQ (minimum order quantity)",
        ],
        "questions": [
            "What is the total procurement spend by category or supplier?",
            "Where is our purchase price variance highest?",
            "How much spend is outside approved contracts (maverick spend)?",
            "What is the average PO cycle time by buyer or category?",
        ],
    },
    "Demand Planning": {
        "icon": "📈",
        "kpis": [
            "forecast accuracy %", "MAPE (Mean Absolute Percentage Error)",
            "forecast bias", "MAD (Mean Absolute Deviation)",
            "demand variability (CV)", "service level %",
            "fill rate vs forecast", "new product forecast accuracy",
            "statistical forecast vs actuals", "error by SKU / region",
            "demand sensing signal strength",
        ],
        "questions": [
            "What is our forecast accuracy (MAPE) by product family?",
            "Which SKUs have the highest forecast bias?",
            "Show demand variability and coefficient of variation by category.",
            "Where is the gap between forecasted and actual demand largest?",
        ],
    },
    "Logistics": {
        "icon": "🚚",
        "kpis": [
            "lead time", "transit time", "freight cost per unit",
            "carrier on-time performance %", "freight cost as % of revenue",
            "mode split (air / ocean / ground / LTL / FTL)",
            "delivery exception rate", "damage rate in transit",
            "customs clearance time", "last-mile delivery performance",
            "freight invoice accuracy", "carbon emissions per shipment",
        ],
        "questions": [
            "Which carriers have the worst on-time delivery performance?",
            "What is the average freight cost per unit by lane or carrier?",
            "Show transit time trend — are lead times improving or worsening?",
            "What percentage of shipments travel by air vs ocean vs ground?",
        ],
    },
    "Warehouse Operations": {
        "icon": "🏪",
        "kpis": [
            "pick accuracy %", "order fulfillment cycle time",
            "dock-to-stock time", "storage utilization %",
            "put-away time", "shipping accuracy %", "receiving accuracy %",
            "cases / lines per hour (labor efficiency)", "cost per order",
            "returns processing time", "inventory accuracy %",
            "perfect order rate", "on-time shipment %",
        ],
        "questions": [
            "What is our pick accuracy rate and where are errors concentrated?",
            "How does storage utilization vary across warehouse locations?",
            "What is the average dock-to-stock time by product type?",
            "Show order fulfillment cycle time trend by week or shift.",
        ],
    },
}

# Flat list for prompts — all KPIs across all modules
SUPPLY_CHAIN_KPIS: list[str] = [
    kpi for module in MODULE_KPIS.values() for kpi in module["kpis"]
]


# ─── Client ───────────────────────────────────────────────────────────────────

def _get_client() -> anthropic.Anthropic:
    load_dotenv()
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ─── Conversation Memory ──────────────────────────────────────────────────────

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class ConversationMemory:
    def __init__(self, max_turns: int = 20):
        self.messages: list[Message] = []
        self.max_turns = max_turns

    def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str, metadata: dict = None):
        self.messages.append(Message(
            role="assistant", content=content, metadata=metadata or {}
        ))

    def get_history_for_llm(self) -> list[dict]:
        recent = self.messages[-self.max_turns:]
        return [{"role": m.role, "content": m.content} for m in recent]

    def get_last_n_exchanges(self, n: int = 3) -> list[Message]:
        return self.messages[-(n * 2):]

    def get_context_summary(self) -> str:
        if not self.messages:
            return "No previous conversation."
        user_questions = [m.content for m in self.messages if m.role == "user"]
        return "Recent questions:\n" + "\n".join(
            f"- {q}" for q in user_questions[-5:]
        )

    def clear(self):
        self.messages = []

    def to_json(self) -> str:
        return json.dumps([
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "metadata": m.metadata
            }
            for m in self.messages
        ], indent=2)

    @property
    def turn_count(self) -> int:
        return len([m for m in self.messages if m.role == "user"])

    @property
    def is_empty(self) -> bool:
        return len(self.messages) == 0


# ─── Data Cleaning ────────────────────────────────────────────────────────────

@dataclass
class CleaningAction:
    action_type: str
    column: str
    description: str
    reason: str
    rows_affected: int
    before_value: Any = None
    after_value: Any = None
    severity: str = "low"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CleaningReport:
    original_shape: tuple
    cleaned_shape: tuple
    actions: list[CleaningAction] = field(default_factory=list)
    issues_found: int = 0
    issues_fixed: int = 0
    data_quality_before: float = 0.0
    data_quality_after: float = 0.0

    def summary(self) -> str:
        return (
            f"Found {self.issues_found} issues, fixed {self.issues_fixed}. "
            f"Data quality improved from {self.data_quality_before:.1f}% "
            f"to {self.data_quality_after:.1f}%"
        )


def _quality_score(df: pd.DataFrame) -> float:
    return round((1 - df.isnull().sum().sum() / df.size) * 100, 2)


class DataCleaningAgent:
    def __init__(self, aggressive: bool = False):
        self.aggressive = aggressive

    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
        df = df.copy()
        report = CleaningReport(
            original_shape=df.shape,
            cleaned_shape=df.shape,
            data_quality_before=_quality_score(df)
        )
        df, report = self._fix_column_names(df, report)
        df, report = self._remove_duplicates(df, report)
        df, report = self._fix_missing_values(df, report)
        df, report = self._fix_data_types(df, report)
        df, report = self._handle_outliers(df, report)

        report.cleaned_shape = df.shape
        report.data_quality_after = _quality_score(df)
        report.issues_found = len(report.actions)
        report.issues_fixed = len([a for a in report.actions if a.rows_affected > 0])
        return df, report

    def _fix_column_names(self, df, report):
        original_cols = list(df.columns)
        new_cols = [
            col.strip().lower().replace(" ", "_").replace("-", "_")
            for col in df.columns
        ]
        changed = [(o, n) for o, n in zip(original_cols, new_cols) if o != n]
        if changed:
            df.columns = new_cols
            for old, new in changed:
                report.actions.append(CleaningAction(
                    action_type="rename_column", column=old,
                    description=f"Renamed '{old}' → '{new}'",
                    reason="Standardizing to snake_case prevents code generation errors.",
                    rows_affected=len(df), severity="low"
                ))
        return df, report

    def _remove_duplicates(self, df, report):
        n_dupes = df.duplicated().sum()
        if n_dupes > 0:
            df = df.drop_duplicates()
            report.actions.append(CleaningAction(
                action_type="remove_duplicates", column="all",
                description=f"Removed {n_dupes} duplicate rows",
                reason=f"{n_dupes} rows were exact duplicates. Duplicates inflate counts and skew KPIs like fill rate and OTIF.",
                rows_affected=n_dupes,
                severity="high" if n_dupes > 10 else "medium"
            ))
        return df, report

    def _fix_missing_values(self, df, report):
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count == 0:
                continue
            missing_pct = missing_count / len(df) * 100

            if missing_pct > 70 and self.aggressive:
                df = df.drop(columns=[col])
                report.actions.append(CleaningAction(
                    action_type="drop_column", column=col,
                    description=f"Dropped '{col}' ({missing_pct:.1f}% missing)",
                    reason="Over 70% missing — column adds noise rather than signal.",
                    rows_affected=missing_count, severity="high"
                ))
                continue

            if pd.api.types.is_numeric_dtype(df[col].dtype):
                fill_value = df[col].median()
                df[col] = df[col].fillna(fill_value)
                report.actions.append(CleaningAction(
                    action_type="fill_missing", column=col,
                    description=f"Filled {missing_count} missing values in '{col}' with median ({fill_value:.2f})",
                    reason=f"Median fill is robust to outliers — important for supply chain data where extreme values (e.g. rush orders) are common.",
                    rows_affected=missing_count,
                    before_value="NaN", after_value=round(fill_value, 2),
                    severity="medium" if missing_pct > 10 else "low"
                ))
            else:
                mode_vals = df[col].mode()
                if not mode_vals.empty:
                    fill_value = mode_vals.iloc[0]
                    df[col] = df[col].fillna(fill_value)
                    report.actions.append(CleaningAction(
                        action_type="fill_missing", column=col,
                        description=f"Filled {missing_count} missing values in '{col}' with '{fill_value}'",
                        reason="Most-frequent value preserves the existing distribution without introducing a new category.",
                        rows_affected=missing_count,
                        before_value="NaN", after_value=str(fill_value),
                        severity="medium" if missing_pct > 10 else "low"
                    ))
        return df, report

    def _fix_data_types(self, df, report):
        for col in df.columns:
            if df[col].dtype != object:
                continue
            sample = df[col].dropna().head(100)

            converted = pd.to_numeric(sample, errors="coerce")
            if converted.notna().mean() > 0.9:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                report.actions.append(CleaningAction(
                    action_type="fix_dtype", column=col,
                    description=f"Converted '{col}' from text to numeric",
                    reason="Numbers stored as text break aggregations like sum, average, and lead-time calculations.",
                    rows_affected=len(df),
                    before_value="object (string)", after_value="float64", severity="medium"
                ))
                continue

            try:
                pd.to_datetime(sample, infer_datetime_format=True)
                df[col] = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
                report.actions.append(CleaningAction(
                    action_type="fix_dtype", column=col,
                    description=f"Converted '{col}' from text to datetime",
                    reason="Date strings prevent time-series analysis, lead-time calculation, and delivery trend detection.",
                    rows_affected=len(df),
                    before_value="object (string)", after_value="datetime64", severity="medium"
                ))
            except Exception:
                pass
        return df, report

    def _handle_outliers(self, df, report):
        for col in df.select_dtypes(include=[np.number]).columns:
            series = df[col].dropna()
            if len(series) < 10:
                continue
            Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
            IQR = Q3 - Q1
            if IQR == 0:
                continue
            lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
            n_outliers = ((df[col] < lower) | (df[col] > upper)).sum()
            if n_outliers > 0:
                pct = n_outliers / len(df) * 100
                report.actions.append(CleaningAction(
                    action_type="outlier_detected", column=col,
                    description=f"Found {n_outliers} outliers in '{col}' ({pct:.1f}%). Range: [{lower:.2f}, {upper:.2f}]",
                    reason="Flagged but NOT removed — supply chain outliers often represent real events (e.g. emergency orders, supplier failures).",
                    rows_affected=n_outliers,
                    severity="medium" if pct > 5 else "low"
                ))
        return df, report


# ─── Code Executor ────────────────────────────────────────────────────────────

def _safe_import(name, *args, **kwargs):
    allowed = {
        "pandas", "numpy",
        "plotly", "plotly.express", "plotly.graph_objects", "plotly.subplots",
    }
    if name not in allowed:
        raise ImportError(f"Import of '{name}' is not allowed in the sandbox.")
    return __import__(name, *args, **kwargs)


from plotly.subplots import make_subplots as _make_subplots

_SAFE_GLOBALS: dict = {
    "pd": pd, "pandas": pd,
    "np": np, "numpy": np,
    "px": px, "go": go,
    "make_subplots": _make_subplots,
    "__builtins__": {
        "__import__": _safe_import,
        "int": int, "float": float, "str": str,
        "bool": bool, "list": list, "dict": dict,
        "set": set, "tuple": tuple,
        "len": len, "range": range, "enumerate": enumerate,
        "zip": zip, "map": map, "filter": filter,
        "sorted": sorted, "reversed": reversed,
        "sum": sum, "min": min, "max": max,
        "abs": abs, "round": round,
        "print": print, "isinstance": isinstance,
        "type": type, "hasattr": hasattr, "getattr": getattr,
    },
}


def execute_code_safely(code: str, df: pd.DataFrame) -> dict[str, Any]:
    local_vars = {"df": df.copy()}
    try:
        exec(code, _SAFE_GLOBALS, local_vars)
        if "fig" in local_vars:
            return {"success": True, "result_type": "chart", "data": local_vars["fig"]}
        elif "result_df" in local_vars:
            result = local_vars["result_df"]
            if not isinstance(result, pd.DataFrame):
                result = pd.DataFrame(result)
            return {"success": True, "result_type": "dataframe", "data": result}
        elif "result_value" in local_vars:
            return {"success": True, "result_type": "value", "data": local_vars["result_value"]}
        elif "result_text" in local_vars:
            return {"success": True, "result_type": "text", "data": local_vars["result_text"]}
        else:
            return {
                "success": False, "result_type": "error", "data": None,
                "error": "Code ran but produced no output. Expected: fig, result_df, result_value, or result_text."
            }
    except Exception as e:
        return {
            "success": False, "result_type": "error", "data": None,
            "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        }


# ─── Insight Engine ───────────────────────────────────────────────────────────

_INSIGHT_SYSTEM = """You are a senior supply chain analyst covering all six operational modules:
📦 Inventory · 🤝 Supplier Performance · 🏭 Procurement · 📈 Demand Planning · 🚚 Logistics · 🏪 Warehouse Operations.

Rules:
- Use plain English. Reference the correct module's KPIs (e.g. OTIF/defect rate for Supplier Performance,
  MAPE/forecast bias for Demand Planning, pick accuracy/dock-to-stock for Warehouse Ops, freight cost/transit time for Logistics).
- Be specific — use exact numbers from the results.
- Focus on operational impact: risk, cost, delivery performance, supplier reliability.
- Keep each insight to 1-2 sentences.
- Always respond in valid JSON."""


def generate_insights(
    question: str,
    code_output: str,
    dataset_context: str,
    num_insights: int = 3
) -> dict:
    client = _get_client()
    prompt = f"""Dataset: {dataset_context}
Question: {question}
Analysis output: {code_output}

Generate exactly {num_insights} supply chain business insights.

Respond ONLY with this JSON (no markdown):
{{
  "summary": "One-sentence executive summary.",
  "insights": [
    {{"title": "3-5 word title", "detail": "1-2 sentence insight with numbers.", "type": "positive|negative|neutral|warning"}}
  ],
  "recommendation": "One actionable next step.",
  "confidence": "high|medium|low"
}}"""

    try:
        response = client.messages.create(
            model=MODEL, max_tokens=1000,
            system=_INSIGHT_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return {"success": True, "data": json.loads(raw.strip())}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_dataset_overview_insights(profile: dict) -> dict:
    client = _get_client()
    prompt = f"""Supply chain dataset profile:
{json.dumps(profile, indent=2, default=str)}

Generate a supply chain-focused overview: what data this contains, quality issues, and which analyses would be most valuable.

Respond ONLY with this JSON (no markdown):
{{
  "summary": "What this dataset contains (1 sentence).",
  "insights": [
    {{"title": "Short title", "detail": "Explanation with numbers.", "type": "positive|negative|neutral|warning"}}
  ],
  "recommendation": "What supply chain analysis should the user run first?",
  "confidence": "high|medium|low"
}}"""

    try:
        response = client.messages.create(
            model=MODEL, max_tokens=1000,
            system=_INSIGHT_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return {"success": True, "data": json.loads(raw.strip())}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── ReAct Agent ─────────────────────────────────────────────────────────────

MAX_ITERATIONS = 4

_REACT_SYSTEM_TEMPLATE = """You are an expert supply chain data analyst using Python in a ReAct loop.
Key metrics you understand: lead time, fill rate, OTIF, inventory turns, days of supply, shortage risk.

DATASET:
- Shape: {rows} rows x {cols} columns
- Columns:
{columns_info}

{context}

CODE RULES — you MUST follow all of these:
- DataFrame is always called `df`
- For charts: use plotly express (import plotly.express as px), assign to `fig`
  - For dashboards/overviews use plotly subplots: from plotly.subplots import make_subplots; import plotly.graph_objects as go
- For dataframe results: assign to `result_df`
- For single values: assign to `result_value`
- For text: assign to `result_text`
- Always wrap code in ```python ... ``` blocks
- NEVER respond with only text — ALWAYS include a ```python ... ``` code block

DASHBOARD REQUESTS — when user asks for a dashboard, overview, or summary:
- Use make_subplots to combine multiple charts into one figure assigned to `fig`
- Include: KPI summary charts, distributions of numeric columns, category breakdowns
- Example structure:
  ```python
  from plotly.subplots import make_subplots
  import plotly.graph_objects as go
  fig = make_subplots(rows=2, cols=2, subplot_titles=(...))
  fig.add_trace(..., row=1, col=1)
  fig.update_layout(title="Dashboard", height=700)
  ```

REACT FORMAT:
Thought: [your reasoning about what to do]
Action: [ALWAYS write python code in a ```python ... ``` block here]"""


def run_react_agent(question: str, df: pd.DataFrame, system_context: str = "") -> dict:
    client = _get_client()
    columns_info = "\n".join([
        f"  - {col} ({df[col].dtype}): sample → {df[col].dropna().head(3).tolist()}"
        for col in df.columns
    ])
    system_prompt = _REACT_SYSTEM_TEMPLATE.format(
        rows=df.shape[0], cols=df.shape[1],
        columns_info=columns_info, context=system_context
    )

    messages = []
    thought_process = []
    last_error = last_code = None

    for iteration in range(1, MAX_ITERATIONS + 1):
        if iteration == 1:
            user_msg = f"Question: {question}\n\nThink step by step, then write Python code to answer this."
        else:
            user_msg = (
                f"The previous code failed:\n```\n{last_error}\n```\n\n"
                f"Previous code:\n```python\n{last_code}\n```\n\n"
                f"Reflect on what went wrong and write corrected code."
            )

        messages.append({"role": "user", "content": user_msg})

        try:
            response = client.messages.create(
                model=MODEL, max_tokens=2000,
                system=system_prompt, messages=messages
            )
            llm_response = response.content[0].text
        except Exception as e:
            return {
                "success": False, "final_code": last_code, "result": None,
                "figure": None, "thought_process": thought_process,
                "iterations": iteration, "error": f"LLM call failed: {str(e)}"
            }

        messages.append({"role": "assistant", "content": llm_response})
        thought = _extract_thought(llm_response)
        code = _extract_code(llm_response)

        step = {
            "iteration": iteration, "thought": thought,
            "code": code, "status": "pending", "error": None, "result_type": None
        }

        if not code:
            step["status"] = "no_code"
            step["error"] = "LLM did not generate code"
            thought_process.append(step)
            last_error = "No code generated. Write executable Python code."
            continue

        last_code = code
        exec_result = execute_code_safely(code, df)

        if exec_result["success"]:
            step["status"] = "success"
            step["result_type"] = exec_result["result_type"]
            thought_process.append(step)
            return {
                "success": True, "final_code": code,
                "result": exec_result["data"] if exec_result["result_type"] != "chart" else None,
                "figure": exec_result["data"] if exec_result["result_type"] == "chart" else None,
                "result_type": exec_result["result_type"],
                "thought_process": thought_process,
                "iterations": iteration, "error": None
            }
        else:
            last_error = exec_result["error"]
            step["status"] = "failed"
            step["error"] = last_error
            thought_process.append(step)

    return {
        "success": False, "final_code": last_code,
        "result": None, "figure": None,
        "thought_process": thought_process,
        "iterations": MAX_ITERATIONS,
        "error": f"Failed after {MAX_ITERATIONS} attempts. Last error: {last_error}"
    }


def _extract_thought(text: str) -> str:
    match = re.search(r"Thought:\s*(.*?)(?=Action:|```|$)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    lines = text.split("\n")
    return lines[0].strip() if lines else "No thought"


def _extract_code(text: str) -> str | None:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else None


# ─── Explanation Agent ────────────────────────────────────────────────────────

def detect_industry(df: pd.DataFrame) -> dict:
    client = _get_client()
    columns_info = ", ".join([f"{col} ({df[col].dtype})" for col in df.columns])
    sample_values = {col: df[col].dropna().head(3).tolist() for col in list(df.columns)[:5]}

    # Build module hint for the prompt
    module_hints = "\n".join([
        f"- {m} ({info['icon']}): look for columns related to {', '.join(info['kpis'][:4])}"
        for m, info in MODULE_KPIS.items()
    ])

    prompt = f"""Identify which supply chain module this dataset belongs to.

The six modules are:
{module_hints}

Dataset columns: {columns_info}
Sample values: {json.dumps(sample_values, default=str)}

Pick the single best-matching module as the subdomain.
Return 3 key metrics from that module and 4 typical questions a user would ask.

Respond ONLY with valid JSON (no markdown):
{{
    "industry": "supply chain",
    "subdomain": "Inventory | Supplier Performance | Procurement | Demand Planning | Logistics | Warehouse Operations",
    "confidence": "high|medium|low",
    "reasoning": "one sentence explaining your detection",
    "key_metrics": ["metric 1", "metric 2", "metric 3"],
    "typical_questions": [
        "question 1",
        "question 2",
        "question 3",
        "question 4"
    ]
}}"""

    try:
        response = client.messages.create(
            model=MODEL, max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = re.sub(r"```json|```", "", response.content[0].text).strip()
        return {"success": True, "data": json.loads(raw)}
    except Exception:
        return {
            "success": True,
            "data": {
                "industry": "supply chain",
                "subdomain": "Inventory",
                "confidence": "low",
                "reasoning": "Default supply chain context.",
                "key_metrics": ["inventory turns", "days of supply", "shortage rate"],
                "typical_questions": [
                    "What is the inventory turnover by SKU or category?",
                    "Which items are overstocked or at risk of stockout?",
                    "Show aging inventory — items with no movement in 90+ days.",
                    "What is the days of supply for each product group?",
                ]
            }
        }


def explain_result(question: str, result, df: pd.DataFrame, industry: str = "supply chain") -> dict:
    client = _get_client()
    result_str = _format_result(result)
    dataset_context = f"{df.shape[0]} rows x {df.shape[1]} cols. Columns: {list(df.columns)}"

    # Find the closest module match from the subdomain
    matched_module = next(
        (m for m in MODULE_KPIS if m.lower() in industry.lower()), None
    )
    module_kpi_hint = (
        f"Relevant KPIs for {matched_module}: {', '.join(MODULE_KPIS[matched_module]['kpis'][:6])}"
        if matched_module else
        "Cover inventory, logistics, supplier performance, procurement, demand planning, and warehouse ops as relevant."
    )

    prompt = f"""You are a senior supply chain analyst explaining findings to an operations manager.

Module context: {industry}
{module_kpi_hint}
Dataset: {dataset_context}
Question: {question}
Result: {result_str}

Respond ONLY with valid JSON (no markdown):
{{
    "explanation": "2-3 sentence explanation with specific numbers and module-relevant KPI context",
    "confidence": "high|medium|low",
    "confidence_reason": "one sentence",
    "limitations": ["limitation 1", "limitation 2"],
    "next_steps": ["next analysis 1", "next analysis 2"],
    "industry_context": "one sentence connecting this finding to the operational module",
    "key_number": "the single most important number",
    "sentiment": "positive|negative|neutral|warning"
}}"""

    try:
        response = client.messages.create(
            model=MODEL, max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = re.sub(r"```json|```", "", response.content[0].text).strip()
        return {"success": True, "data": json.loads(raw)}
    except Exception:
        return {
            "success": True,
            "data": {
                "explanation": "Analysis completed successfully.",
                "confidence": "medium",
                "confidence_reason": "Result generated but detailed explanation unavailable.",
                "limitations": [], "next_steps": [],
                "industry_context": "",
                "key_number": str(result)[:50],
                "sentiment": "neutral"
            }
        }


def explain_cleaning_report(cleaning_report: CleaningReport, industry: str = "supply chain") -> dict:
    client = _get_client()
    actions_summary = "\n".join([
        f"- {a.description} (Reason: {a.reason})"
        for a in cleaning_report.actions
    ]) if cleaning_report.actions else "No cleaning needed."

    prompt = f"""Explain data cleaning results to a supply chain operations manager.

Summary: {cleaning_report.summary()}
Actions:
{actions_summary}

Respond ONLY with valid JSON (no markdown):
{{
    "headline": "one sentence summary of data quality improvement",
    "explanation": "2-3 sentences on what was cleaned and why it matters for supply chain analysis",
    "trust_score": 85,
    "biggest_issue": "the most important problem fixed",
    "recommendation": "one action the supply chain team should take based on data quality findings"
}}"""

    try:
        response = client.messages.create(
            model=MODEL, max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = re.sub(r"```json|```", "", response.content[0].text).strip()
        return {"success": True, "data": json.loads(raw)}
    except Exception:
        return {
            "success": True,
            "data": {
                "headline": "Data cleaning completed.",
                "explanation": f"Cleaned dataset. {cleaning_report.summary()}",
                "trust_score": 80,
                "biggest_issue": "See cleaning actions for details.",
                "recommendation": "Review flagged outliers — they may represent real supply chain events."
            }
        }


def _format_result(result) -> str:
    if result is None:
        return "No result"
    if isinstance(result, pd.DataFrame):
        return f"DataFrame with {len(result)} rows:\n{result.head(10).to_string()}"
    if isinstance(result, pd.Series):
        return f"Series:\n{result.head(10).to_string()}"
    return str(result)[:500]


# ─── Supply Chain Orchestrator ────────────────────────────────────────────────

class SupplyChainOrchestrator:
    """
    Master coordinator for supply chain data analysis.
    On dataset upload: detect domain, clean data, explain what was cleaned.
    On each question: ReAct loop → explain result → store in memory.
    """

    def __init__(self):
        self.memory = ConversationMemory(max_turns=20)
        self.cleaning_agent = DataCleaningAgent(aggressive=False)
        self.industry_info = None
        self.cleaning_report = None
        self.df_original = None
        self.df_clean = None
        self.is_initialized = False

    def initialize(self, df: pd.DataFrame) -> dict:
        self.df_original = df.copy()

        industry_result = detect_industry(df)
        self.industry_info = industry_result["data"] if industry_result["success"] else {
            "industry": "supply chain", "subdomain": "operations",
            "confidence": "low", "reasoning": "",
            "key_metrics": SUPPLY_CHAIN_KPIS[:3],
            "typical_questions": [
                "Which suppliers have the longest lead times?",
                "What is our fill rate by product category?",
                "Show inventory aging by supplier."
            ]
        }

        self.df_clean, self.cleaning_report = self.cleaning_agent.clean(df)

        cleaning_explanation = explain_cleaning_report(
            self.cleaning_report,
            industry=self.industry_info.get("industry", "supply chain")
        )

        self.is_initialized = True

        return {
            "industry": self.industry_info,
            "cleaning_report": self.cleaning_report,
            "cleaning_explanation": cleaning_explanation.get("data", {}),
            "df_clean": self.df_clean,
            "rows_removed": self.df_original.shape[0] - self.df_clean.shape[0],
            "quality_before": self.cleaning_report.data_quality_before,
            "quality_after": self.cleaning_report.data_quality_after,
        }

    def answer_question(self, question: str) -> dict:
        if not self.is_initialized:
            return {
                "success": False, "question": question,
                "error": "No dataset loaded. Please upload a CSV first.",
                "iterations": 0, "thought_process": [],
                "code": None, "result": None, "figure": None, "explanation": None
            }

        df = self.df_clean
        industry = self.industry_info.get("industry", "supply chain")
        self.memory.add_user_message(question)

        subdomain = self.industry_info.get("subdomain", "")
        matched_module = next(
            (m for m in MODULE_KPIS if m.lower() in subdomain.lower()), None
        )
        if matched_module:
            kpi_context = (
                f"Primary module: {matched_module} {MODULE_KPIS[matched_module]['icon']}\n"
                f"Key KPIs: {', '.join(MODULE_KPIS[matched_module]['kpis'])}"
            )
        else:
            kpi_context = "All modules in scope: " + " | ".join(
                f"{info['icon']} {m}" for m, info in MODULE_KPIS.items()
            )

        react_result = run_react_agent(
            question=question, df=df,
            system_context=f"""Industry: {industry} — {subdomain}
{kpi_context}
Previous conversation:
{self.memory.get_context_summary()}"""
        )

        explanation_data = None
        if react_result["success"] and react_result["result"] is not None:
            exp = explain_result(
                question=question, result=react_result["result"],
                df=df, industry=industry
            )
            if exp["success"]:
                explanation_data = exp["data"]

        response = {
            "success": react_result["success"],
            "question": question,
            "code": react_result["final_code"],
            "result": react_result["result"],
            "figure": react_result["figure"],
            "result_type": react_result.get("result_type"),
            "thought_process": react_result["thought_process"],
            "iterations": react_result["iterations"],
            "explanation": explanation_data,
            "error": react_result["error"],
            "industry": industry,
        }

        summary = (
            explanation_data.get("explanation", "")
            if explanation_data
            else react_result.get("error", "Analysis completed.")
        )
        self.memory.add_assistant_message(
            content=summary,
            metadata={
                "iterations": react_result["iterations"],
                "success": react_result["success"],
                "had_chart": react_result["figure"] is not None
            }
        )

        return response

    def get_suggested_questions(self) -> list[str]:
        if self.industry_info:
            return self.industry_info.get("typical_questions", [])
        return []

    def reset(self):
        self.memory.clear()
        self.industry_info = None
        self.cleaning_report = None
        self.df_original = None
        self.df_clean = None
        self.is_initialized = False
