# agents/code_agent.py

import json
import re
import pandas as pd
import anthropic
from utils.code_executor import execute_code_safely
from prompts.analyst_prompts import get_code_generation_prompt, get_insight_prompt


def build_dataset_context(df: pd.DataFrame) -> str:
    """
    Builds a compact schema string describing the dataset.
    This tells the LLM what columns and data types exist — critical for correct code gen.
    """
    lines = [
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        f"Columns and types:"
    ]
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        lines.append(f"  - {col} ({dtype}): sample values = {sample}")

    null_cols = df.columns[df.isnull().any()].tolist()
    if null_cols:
        lines.append(f"Columns with nulls: {null_cols}")

    return "\n".join(lines)


def parse_llm_response(response_text: str) -> dict:
    """
    Parses the JSON response from Claude.
    Handles edge cases where the model wraps JSON in markdown code fences.
    """
    # Strip markdown code fences if present (e.g., ```json ... ```)
    cleaned = re.sub(r"```(?:json)?", "", response_text).replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Return a structured error so the UI can handle it gracefully
        return {
            "code": "",
            "result_type": "error",
            "explanation": f"Failed to parse LLM response as JSON: {e}\n\nRaw response:\n{response_text}"
        }


def run_code_agent(question: str, df: pd.DataFrame, api_key: str) -> dict:
    """
    Main agent function:
    1. Build dataset context
    2. Ask Claude to generate code
    3. Parse the response
    4. Execute code safely
    5. Generate a business insight from the result
    
    Returns a result dict for the UI to render.
    """
    client = anthropic.Anthropic(api_key=api_key)

    # Step 1: Build context from the dataframe
    dataset_context = build_dataset_context(df)

    # Step 2: Generate code via Claude
    code_prompt = get_code_generation_prompt(question, dataset_context)

    code_response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": code_prompt}]
    )

    raw_response = code_response.content[0].text

    # Step 3: Parse JSON from Claude's response
    parsed = parse_llm_response(raw_response)

    if not parsed.get("code"):
        return {
            "success": False,
            "error": parsed.get("explanation", "No code was generated."),
            "code": "",
            "result_type": "error"
        }

    generated_code = parsed["code"]
    result_type_hint = parsed.get("result_type", "unknown")
    code_explanation = parsed.get("explanation", "")

    # Step 4: Execute the generated code safely
    execution_result = execute_code_safely(generated_code, df)

    # Step 5: Generate a business insight if execution succeeded
    business_insight = ""
    if execution_result["success"]:
        result_summary = summarize_result_for_insight(
            execution_result["result_type"],
            execution_result["data"]
        )
        insight_prompt = get_insight_prompt(question, result_summary)
        insight_response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": insight_prompt}]
        )
        business_insight = insight_response.content[0].text

    return {
        "success": execution_result["success"],
        "code": generated_code,
        "code_explanation": code_explanation,
        "result_type": execution_result["result_type"],
        "data": execution_result.get("data"),
        "business_insight": business_insight,
        "error": execution_result.get("error", "")
    }


def summarize_result_for_insight(result_type: str, data) -> str:
    """
    Converts the execution result into a string summary for the insight prompt.
    We can't pass a full DataFrame to the LLM — we summarize it first.
    """
    if result_type == "chart":
        return "A chart/visualization was generated successfully."
    elif result_type == "dataframe":
        if hasattr(data, 'to_string'):
            # Limit to first 10 rows so we don't overflow the prompt
            return data.head(10).to_string(index=False)
        return str(data)
    elif result_type == "value":
        return f"Computed result: {data}"
    elif result_type == "text":
        return str(data)
    else:
        return "Analysis completed."