# components/chat_interface.py
"""
Chat UI — modern dark theme with styled message bubbles.
"""

import re
import streamlit as st
import pandas as pd
from agent.supply_chain_agent import ConversationMemory


def render_chat_history(memory: ConversationMemory, results_store: list):
    """Render the full conversation thread."""
    if memory.is_empty:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 60px 20px;
            color: #4a5568;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">💬</div>
            <div style="font-size: 1rem; font-weight: 500; color: #6b7280;">
                Start the conversation
            </div>
            <div style="font-size: 0.85rem; margin-top: 6px; color: #4a5568;">
                Ask anything about your dataset below
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    result_idx = 0
    for msg in memory.messages:
        if msg.role == "user":
            _render_user_bubble(msg.content)
        elif msg.role == "assistant":
            result = results_store[result_idx] if result_idx < len(results_store) else None
            _render_assistant_bubble(msg.content, result)
            result_idx += 1


def _render_user_bubble(content: str):
    """User message — right aligned blue bubble."""
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: flex-end;
        margin: 12px 0;
    ">
        <div style="
            background: linear-gradient(135deg, #1e3a8a, #2563eb);
            color: white;
            padding: 12px 18px;
            border-radius: 18px 18px 4px 18px;
            max-width: 72%;
            font-size: 14px;
            line-height: 1.6;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
        ">
            {content}
        </div>
        <div style="
            width: 32px;
            height: 32px;
            background: #2a3a5e;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-left: 8px;
            flex-shrink: 0;
            font-size: 14px;
            align-self: flex-end;
        ">👤</div>
    </div>
    """, unsafe_allow_html=True)


def _render_assistant_bubble(content: str, result: dict | None):
    """AI response — left aligned with icon."""
    explanation = _strip_code_blocks(content)

    st.markdown(f"""
    <div style="
        display: flex;
        align-items: flex-start;
        margin: 12px 0;
        gap: 10px;
    ">
        <div style="
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #1e3a8a, #2563eb);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 14px;
            margin-top: 4px;
        ">🤖</div>
        <div style="
            background: #1a1f2e;
            border: 1px solid #2a2f3e;
            color: #e0e0e0;
            padding: 14px 18px;
            border-radius: 4px 18px 18px 18px;
            max-width: 80%;
            font-size: 14px;
            line-height: 1.7;
        ">
            {explanation if explanation else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render results OUTSIDE the bubble (charts, code, tables need full width)
    if result:
        with st.container():
            st.markdown("<div style='margin-left: 42px;'>", unsafe_allow_html=True)
            _render_result_content(result)
            st.markdown("</div>", unsafe_allow_html=True)


def _render_result_content(result: dict):
    """Render code, chart, table, insight."""
    result_type = result.get("type")

    # Generated code expander
    if result.get("code"):
        with st.expander("🔧 View Generated Code"):
            st.code(result["code"], language="python")

    # Chart
    if result.get("figure"):
        st.plotly_chart(result["figure"], use_container_width=True)

    # Table or value
    elif result.get("execution_result") is not None:
        val = result["execution_result"]
        if isinstance(val, pd.DataFrame):
            st.dataframe(val, use_container_width=True)
        elif isinstance(val, pd.Series):
            st.dataframe(val.to_frame(), use_container_width=True)
        else:
            st.markdown(f"""
            <div style="
                background: #1a1f2e;
                border: 1px solid #2a2f3e;
                border-radius: 10px;
                padding: 16px 24px;
                margin: 8px 0;
                display: inline-block;
            ">
                <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase;
                            letter-spacing: 0.1em; margin-bottom: 4px;">Result</div>
                <div style="color: #7c9ef8; font-size: 1.8rem; font-weight: 700;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    # Business insight
    if result.get("insight"):
        st.markdown(f"""
        <div style="
            background: #0d2a1a;
            border: 1px solid #1a5c36;
            border-left: 4px solid #4ade80;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 10px;
            font-size: 13px;
            color: #86efac;
            line-height: 1.6;
        ">
            💡 <strong>Insight:</strong> {result['insight']}
        </div>
        """, unsafe_allow_html=True)

    # Error
    if result_type == "code_error":
        st.markdown(f"""
        <div style="
            background: #2a0d0d;
            border: 1px solid #5c1a1a;
            border-left: 4px solid #ef4444;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 10px;
            font-size: 12px;
            color: #fca5a5;
            font-family: monospace;
        ">
            ⚠️ {result.get('error', 'Unknown error')}
        </div>
        """, unsafe_allow_html=True)


def _strip_code_blocks(text: str) -> str:
    """Remove code fences for clean bubble display."""
    return re.sub(r"```python\s*.*?```", "", text, flags=re.DOTALL).strip()


def render_memory_sidebar(memory: ConversationMemory):
    """Sidebar memory panel."""
    st.sidebar.markdown("""
    <div class="section-header" style="
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #4a5568;
        margin-top: 24px;
        margin-bottom: 12px;
    ">
        Conversation Memory
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Questions", memory.turn_count)
    with col2:
        st.metric("Messages", len(memory.messages))

    if not memory.is_empty:
        st.sidebar.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

        if st.sidebar.button("🗑️ Clear Conversation"):
            memory.clear()
            st.rerun()

        chat_json = memory.to_json()
        st.sidebar.download_button(
            label="📥 Export History",
            data=chat_json,
            file_name="chat_history.json",
            mime="application/json",
            use_container_width=True
        )