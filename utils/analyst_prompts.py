# prompts/analyst_prompts.py

def get_code_generation_prompt(question: str, dataset_context: str) -> str:
    """
    Prompt that instructs Claude to generate safe, executable Python code.
    We give it the dataset schema so it knows column names and types.
    """
    return f"""You are an expert Python data analyst. You have access to a pandas DataFrame called `df`.

DATASET INFORMATION:
{dataset_context}

USER QUESTION:
{question}

YOUR TASK:
Write Python code to answer the user's question using the DataFrame `df`.

STRICT RULES:
1. Use ONLY these libraries: pandas, numpy, plotly.express, plotly.graph_objects
2. The DataFrame is already loaded as `df` — do NOT load any files
3. For chart results: assign the figure to a variable named `fig`
4. For table/dataframe results: assign it to a variable named `result_df`
5. For single value results: assign it to a variable named `result_value`
6. For text/summary results: assign it to a variable named `result_text`
7. NEVER use: os, sys, subprocess, open(), eval(), exec(), __import__
8. NEVER try to read files or access the internet
9. Keep code concise and correct

RESPONSE FORMAT:
Return ONLY a JSON object with this exact structure:
{{
  "code": "your python code here",
  "result_type": "chart" | "dataframe" | "value" | "text",
  "explanation": "1-2 sentence plain English explanation of what the code does"
}}

No markdown, no extra text. Pure JSON only.
"""


def get_insight_prompt(question: str, result_summary: str) -> str:
    """
    After code runs, this prompt converts raw results into business insights.
    """
    return f"""You are a business analyst presenting findings to a non-technical executive.

ORIGINAL QUESTION: {question}

ANALYSIS RESULT: {result_summary}

Write a clear, concise business insight (2-4 sentences) that:
- Directly answers the question
- Highlights what's important or surprising
- Avoids technical jargon
- Ends with one actionable recommendation if applicable

Keep it professional and sharp.
"""