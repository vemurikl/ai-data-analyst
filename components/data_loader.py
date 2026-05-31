import os
import pandas as pd
import streamlit as st
from utils.helpers import format_number, get_memory_usage

try:
    import duckdb
    _DUCKDB = True
except ImportError:
    _DUCKDB = False

_CHUNK_SIZE   = 50_000
_MAX_ROWS     = 1_000_000   # sample cap for upload mode
_LARGE_MB     = 100         # threshold to switch to chunked reading


def _fmt_size(n_bytes: int) -> str:
    for unit, div in [("TB", 2**40), ("GB", 2**30), ("MB", 2**20), ("KB", 2**10)]:
        if n_bytes >= div:
            return f"{n_bytes / div:.1f} {unit}"
    return f"{n_bytes} B"


def _read_uploaded(file) -> pd.DataFrame | None:
    """
    Smart loader for uploaded files.
    < 100 MB  → direct pandas read
    ≥ 100 MB  → chunked read, sample up to 1 M rows
    """
    size_mb = file.size / 2**20
    ext = file.name.rsplit(".", 1)[-1].lower()

    # Parquet (always direct — already columnar/compressed)
    if ext == "parquet":
        try:
            return pd.read_parquet(file)
        except Exception as e:
            st.error(f"❌ Parquet read failed: {e}")
            return None

    sep = "\t" if ext == "tsv" else ","

    if size_mb < _LARGE_MB:
        # ── Direct read ──────────────────────────────────────
        for enc in ("utf-8", "latin-1", "cp1252", "utf-8-sig"):
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=enc, sep=sep)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                st.error(f"❌ Failed to read file: {e}")
                return None
        st.error("❌ Could not decode file — try saving it as UTF-8.")
        return None

    # ── Chunked read for large uploads ────────────────────────
    st.markdown(f"""
    <div style="font-size:0.78rem;color:#fbbf24;background:rgba(69,26,3,0.4);border:1px solid rgba(180,83,9,0.3);border-radius:8px;padding:8px 12px;margin-bottom:8px;">
      ⚡ Large file detected ({_fmt_size(file.size)}) — reading in chunks, sampling up to {_MAX_ROWS:,} rows.
    </div>
    """, unsafe_allow_html=True)

    for enc in ("utf-8", "latin-1", "cp1252", "utf-8-sig"):
        try:
            file.seek(0)
            chunks, total = [], 0
            bar = st.progress(0.0, text="Reading…")
            for chunk in pd.read_csv(file, chunksize=_CHUNK_SIZE, encoding=enc, sep=sep):
                chunks.append(chunk)
                total += len(chunk)
                bar.progress(min(total / _MAX_ROWS, 1.0), text=f"Loaded {total:,} rows…")
                if total >= _MAX_ROWS:
                    break
            bar.empty()
            df = pd.concat(chunks, ignore_index=True)
            if total >= _MAX_ROWS:
                st.info(f"⚡ Showing first **{total:,}** rows — full file may contain more.")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            st.error(f"❌ Read error: {e}")
            return None

    st.error("❌ Could not decode file — try saving it as UTF-8.")
    return None


def _read_local(path: str) -> pd.DataFrame | None:
    """
    DuckDB-powered local path loader — handles TB-scale files
    by reading only a sample into memory.
    """
    if not os.path.exists(path):
        st.error(f"❌ File not found: `{path}`")
        return None

    ext  = path.rsplit(".", 1)[-1].lower()
    size = os.path.getsize(path)

    if not _DUCKDB:
        st.warning("DuckDB not installed — falling back to pandas chunked read.")
        try:
            chunks, total = [], 0
            bar = st.progress(0.0, text="Reading…")
            sep = "\t" if ext == "tsv" else ","
            for chunk in pd.read_csv(path, chunksize=_CHUNK_SIZE, sep=sep):
                chunks.append(chunk)
                total += len(chunk)
                bar.progress(min(total / _MAX_ROWS, 1.0), text=f"Loaded {total:,} rows…")
                if total >= _MAX_ROWS:
                    break
            bar.empty()
            return pd.concat(chunks, ignore_index=True)
        except Exception as e:
            st.error(f"❌ {e}")
            return None

    try:
        con = duckdb.connect()
        with st.spinner(f"Scanning {_fmt_size(size)} file with DuckDB…"):
            if ext == "parquet":
                total_q = f"SELECT COUNT(*) FROM '{path}'"
                data_q  = f"SELECT * FROM '{path}' LIMIT {_MAX_ROWS}"
            else:
                total_q = f"SELECT COUNT(*) FROM read_csv_auto('{path}')"
                data_q  = f"SELECT * FROM read_csv_auto('{path}') LIMIT {_MAX_ROWS}"

            total = con.execute(total_q).fetchone()[0]
            df    = con.execute(data_q).df()
        con.close()

        if total > _MAX_ROWS:
            st.info(
                f"⚡ Sampled **{_MAX_ROWS:,}** of **{total:,}** total rows "
                f"from **{_fmt_size(size)}** file. "
                f"The AI analyzes this representative sample."
            )
        else:
            st.success(f"✅ Loaded **{total:,}** rows ({_fmt_size(size)}).")
        return df

    except Exception as e:
        st.error(f"❌ DuckDB error: {e}")
        return None


# ── Public render functions ────────────────────────────────────────────────────

def render_upload_section() -> pd.DataFrame | None:
    tab_upload, tab_local = st.tabs(["📤  Upload File", "📂  Local Path (large files)"])

    with tab_upload:
        st.markdown("""
        <div style="font-size:0.72rem;color:#475569;margin-bottom:6px;">
          CSV, TSV, or Parquet · up to <strong style="color:#93c5fd;">5 GB</strong> via browser upload
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload file",
            type=["csv", "tsv", "parquet"],
            label_visibility="collapsed",
        )
        if uploaded:
            st.markdown(f"""
            <div style="font-size:0.72rem;color:#64748b;margin:6px 0 2px;">
              📄 <strong style="color:#e2e8f0;">{uploaded.name}</strong>
              &nbsp;·&nbsp; {_fmt_size(uploaded.size)}
            </div>
            """, unsafe_allow_html=True)
            return _read_uploaded(uploaded)

    with tab_local:
        st.markdown("""
        <div style="font-size:0.72rem;color:#475569;margin-bottom:8px;">
          Point to a file on <em>this machine</em> — DuckDB reads it without loading it all into RAM.
          Ideal for <strong style="color:#93c5fd;">GB / TB scale</strong> data.
        </div>
        """, unsafe_allow_html=True)
        path = st.text_input(
            "File path",
            placeholder=r"e.g.  C:\data\orders.csv  or  /data/inventory.parquet",
            label_visibility="collapsed",
        )
        if path and path.strip():
            return _read_local(path.strip())

    return None


def render_dataset_overview(df: pd.DataFrame) -> None:
    st.markdown("""
    <div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;letter-spacing:0.12em;color:#334155;margin-bottom:10px;">
      Dataset Overview
    </div>
    """, unsafe_allow_html=True)
    missing     = df.isnull().sum().sum()
    completeness = round((1 - missing / df.size) * 100, 1)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows",          format_number(df.shape[0]))
    c2.metric("Columns",       format_number(df.shape[1]))
    c3.metric("Missing",       format_number(missing))
    c4.metric("Completeness",  f"{completeness}%")
    c5.metric("Memory",        get_memory_usage(df))


def render_data_preview(df: pd.DataFrame) -> None:
    st.markdown("""
    <div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;letter-spacing:0.12em;color:#334155;margin-bottom:10px;">
      Data Preview
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    with c2:
        n = st.selectbox("Rows", [10, 25, 50, 100, 500], index=0, label_visibility="collapsed")
    st.dataframe(df.head(n), use_container_width=True, height=320)


def render_column_info(df: pd.DataFrame) -> None:
    st.markdown("""
    <div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;letter-spacing:0.12em;color:#334155;margin-bottom:10px;">
      Column Information
    </div>
    """, unsafe_allow_html=True)
    info = pd.DataFrame({
        "Column":   df.columns,
        "Type":     df.dtypes.values.astype(str),
        "Non-Null": df.notnull().sum().values,
        "Null %":   (df.isnull().sum().values / len(df) * 100).round(1),
        "Unique":   df.nunique().values,
    })
    st.dataframe(info, use_container_width=True, hide_index=True)
