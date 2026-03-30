import streamlit as st
from components.data_loader import (
    render_upload_section,
    render_dataset_overview,
    render_data_preview,
    render_column_info,
)

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar():
    with st.sidebar:
        st.title("🤖 AI Data Analyst")
        st.caption("Your autonomous data analysis assistant")
        st.divider()
        st.markdown("""
        **Phases:**
        - ✅ Phase 1: Upload & Preview
        - 🔜 Phase 2: Data Understanding
        - 🔜 Phase 3: AI Q&A
        - 🔜 Phase 4: Code Agent
        """)
        st.divider()
        st.caption("Built with Streamlit + Claude API")


def main():
    render_sidebar()
    st.title("📈 Autonomous AI Data Analyst")
    st.markdown("Upload a dataset and let AI do the heavy lifting.")
    st.divider()

    df = render_upload_section()

    if df is not None:
        st.divider()
        render_dataset_overview(df)
        st.divider()
        render_data_preview(df)
        st.divider()
        render_column_info(df)


if __name__ == "__main__":
    main()