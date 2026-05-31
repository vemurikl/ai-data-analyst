# utils/llm_handler.py
# Handles all communication with Anthropic Claude API

import anthropic
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Q&A helpers
# ═══════════════════════════════════════════════════════════════════════════════

def build_system_prompt(dataset_summary: dict) -> str:
    """Build a system prompt that gives Claude full context about the dataset."""
    summary   = dataset_summary.get("summary", {})
    col_types = dataset_summary.get("column_types", {})
    missing   = dataset_summary.get("missing_values", {})

    shape   = f"{summary.get('rows', '?')} x {summary.get('columns', '?')}"
    columns = list(col_types.keys()) if col_types else []

    return f"""You are an expert AI Data Analyst. You have been given a dataset with the following profile:

Dataset Overview:
- Shape: {shape} (rows x columns)
- Columns: {', '.join(columns)}

Column Types:
{_format_column_types(col_types)}

Missing Values:
{_format_missing_values(missing)}

Your job:
1. Answer user questions about this dataset clearly and helpfully.
2. Use simple, business-friendly language.
3. If a question requires actual computation, explain WHAT you would compute and WHY.
4. If something is unclear, ask a clarifying question.
5. Always be concise but insightful.
"""


def _format_column_types(column_types: dict) -> str:
    if not column_types:
        return "  Not available"
    lines = []
    for col, dtype in column_types.items():
        lines.append(f"  - {col}: {dtype}")
    return "\n".join(lines)


def _format_missing_values(missing) -> str:
    if hasattr(missing, 'empty'):
        if missing.empty:
            return "  No missing values detected"
        lines = []
        for _, row in missing.iterrows():
            col = row.get("Column", row.iloc[0])
            pct = row.get("Missing %", "")
            lines.append(f"  - {col}: {pct}% missing")
        return "\n".join(lines)

    if not missing:
        return "  No missing values detected"
    lines = []
    for col, count in missing.items():
        if count > 0:
            lines.append(f"  - {col}: {count} missing")
    return "\n".join(lines) if lines else "  No missing values detected"


def ask_llm(question: str, dataset_summary: dict, chat_history: list) -> str:
    """Send a question to Claude with dataset context and chat history."""
    system_prompt = build_system_prompt(dataset_summary)

    messages = []
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    except anthropic.AuthenticationError:
        return "❌ API key error. Please check your ANTHROPIC_API_KEY in the .env file."
    except anthropic.RateLimitError:
        return "⚠️ Rate limit reached. Please wait a moment and try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — Code Agent helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _build_dataset_context(df) -> str:
    """
    Compact schema string passed to the code-generation prompt.
    Tells the LLM exactly what columns exist so it writes correct Pandas code.
    """
    lines = [
        f"Shape : {df.shape[0]:,} rows × {df.shape[1]} columns",
        "Columns (name | dtype | sample values):",
    ]
    for col in df.columns:
        sample = df[col].dropna().head(3).tolist()
        lines.append(f"  - {col!r}  [{df[col].dtype}]  e.g. {sample}")
    null_cols = [c for c in df.columns if df[c].isnull().any()]
    if null_cols:
        lines.append(f"Columns with nulls: {null_cols}")
    return "\n".join(lines)


def _parse_code_response(raw: str) -> dict:
    """
    Extract JSON from Claude's response.
    Handles cases where the model wraps JSON in ```json fences.
    """
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "code": "",
            "result_type": "error",
            "explanation": f"Could not parse model response as JSON.\n\nRaw output:\n{raw}",
        }


def _summarize_for_insight(result_type: str, data) -> str:
    """Condense execution result to a short string for the insight prompt."""
    if result_type == "chart":
        return "A chart visualisation was produced successfully."
    if result_type == "dataframe":
        return data.head(10).to_string(index=False) if hasattr(data, "head") else str(data)
    if result_type in ("value", "text"):
        return str(data)
    return "Analysis completed."


def ask_code_agent(question: str, df, dataset_summary: dict) -> dict:
    """
    Phase 4 agent entry point.
    1. Build schema context from the live DataFrame
    2. Ask Claude to generate Python code (JSON response)
    3. Parse + validate the response
    4. Execute code safely in sandbox
    5. If successful, ask Claude for a plain-English business insight
    """
    from utils.analyst_prompts import get_code_generation_prompt, get_insight_prompt
    from utils.code_executor import execute_code_safely

    # Step 1 — build schema
    context     = _build_dataset_context(df)
    code_prompt = get_code_generation_prompt(question, context)

    # Step 2 — generate code
    try:
        code_response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": code_prompt}],
        )
        raw = code_response.content[0].text
    except Exception as exc:
        return {
            "success": False, "code": "", "result_type": "error",
            "data": None, "business_insight": "",
            "error": f"API error during code generation: {exc}",
            "code_explanation": "",
        }

    # Step 3 — parse
    parsed = _parse_code_response(raw)
    if not parsed.get("code"):
        return {
            "success": False, "code": "", "result_type": "error",
            "data": None, "business_insight": "",
            "error": parsed.get("explanation", "No code was generated."),
            "code_explanation": "",
        }

    generated_code   = parsed["code"]
    code_explanation = parsed.get("explanation", "")

    # Step 4 — execute safely
    exec_result = execute_code_safely(generated_code, df)

    # Step 5 — business insight
    business_insight = ""
    if exec_result["success"]:
        summary_str    = _summarize_for_insight(exec_result["result_type"], exec_result["data"])
        insight_prompt = get_insight_prompt(question, summary_str)
        try:
            ins_response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[{"role": "user", "content": insight_prompt}],
            )
            business_insight = ins_response.content[0].text
        except Exception:
            business_insight = ""   # insight is nice-to-have; never crash for it

    return {
        "success":          exec_result["success"],
        "code":             generated_code,
        "code_explanation": code_explanation,
        "result_type":      exec_result["result_type"],
        "data":             exec_result.get("data"),
        "business_insight": business_insight,
        "error":            exec_result.get("error", ""),
    }