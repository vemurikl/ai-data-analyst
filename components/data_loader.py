import streamlit as st
import pandas as pd
from utils.helpers import format_number, get_memory_usage


def render_upload_section() -> pd.DataFrame | None:
    st.header("📂 Upload Your Dataset")

    uploaded_file = st.file_uploader(
        label="Upload a CSV file to get started",
        type=["csv"],
        help="Max file size: 200MB"
    )

    if uploaded_file is None:
        st.info("👆 Upload a CSV file above to begin your analysis.")
        return None

    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
        return None

    st.success(f"✅ **{uploaded_file.name}** loaded successfully!")
    return df


def render_dataset_overview(df: pd.DataFrame) -> None:
    st.subheader("📊 Dataset Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Rows", format_number(df.shape[0]))
    with col2:
        st.metric("Columns", format_number(df.shape[1]))
    with col3:
        missing = df.isnull().sum().sum()
        st.metric("Missing Values", format_number(missing))
    with col4:
        st.metric("Memory Usage", get_memory_usage(df))


def render_data_preview(df: pd.DataFrame) -> None:
    st.subheader("🔍 Data Preview")

    n_rows = st.slider(
        "Rows to display",
        min_value=5,
        max_value=min(100, len(df)),
        value=10,
        step=5
    )

    st.dataframe(df.head(n_rows), use_container_width=True)


def render_column_info(df: pd.DataFrame) -> None:
    st.subheader("🗂️ Column Information")

    col_info = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.values.astype(str),
        "Non-Null Count": df.notnull().sum().values,
        "Null Count": df.isnull().sum().values,
        "Null %": (df.isnull().sum().values / len(df) * 100).round(1)
    })

    st.dataframe(col_info, use_container_width=True, hide_index=True)