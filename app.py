import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from components.data_loader import (
    render_upload_section,
    render_dataset_overview,
    render_data_preview,
    render_column_info,
)
from utils.dashboard import build_business_dashboard, build_quality_dashboard
from agent.supply_chain_agent import SupplyChainOrchestrator

load_dotenv()

st.set_page_config(
    page_title="Caeser.ai",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
* { box-sizing: border-box; }

/* ── Base light theme ── */
.stApp {
  background-color: #f8fafc;
  background-image:
    radial-gradient(ellipse at 10% 30%, rgba(37,99,235,0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 90% 70%, rgba(124,58,237,0.05) 0%, transparent 45%),
    radial-gradient(ellipse at 50% 100%, rgba(16,185,129,0.04) 0%, transparent 40%),
    linear-gradient(rgba(226,232,240,0.6) 1px, transparent 1px),
    linear-gradient(90deg, rgba(226,232,240,0.6) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 100% 100%, 44px 44px, 44px 44px;
  color: #0f172a;
}

/* ── Sidebar (width set dynamically below) ── */
section[data-testid="stSidebar"] {
  background: #ffffff !important;
  border-right: 1px solid rgba(226,232,240,0.9) !important;
  box-shadow: 2px 0 12px rgba(0,0,0,0.04) !important;
  transition: width 0.25s ease !important;
}
section[data-testid="stSidebar"] > div:first-child {
  padding: 0 0 80px 0 !important;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.6); border-radius: 4px; }

/* ── Metrics ── */
[data-testid="stMetric"] {
  background: #ffffff;
  border: 1px solid rgba(226,232,240,0.9);
  border-radius: 14px;
  padding: 14px 18px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
  transition: box-shadow 0.2s;
}
[data-testid="stMetric"]:hover { box-shadow: 0 4px 16px rgba(37,99,235,0.1); }
[data-testid="stMetricValue"] { color: #2563eb !important; font-size: 1.3rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.58rem !important; text-transform: uppercase; letter-spacing: 0.12em; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 4px;
  border: 1px solid rgba(226,232,240,0.9);
  gap: 2px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  border-radius: 8px;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  padding: 7px 16px;
}
.stTabs [aria-selected="true"] {
  background: #ffffff !important;
  color: #2563eb !important;
  border: 1px solid rgba(37,99,235,0.2) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}

/* ── Buttons ── */
.stButton > button {
  background: #f8fafc;
  color: #2563eb;
  border: 1px solid rgba(37,99,235,0.25);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.stButton > button:hover {
  background: #eff6ff;
  border-color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37,99,235,0.15);
}

/* ── Submit button ── */
.stFormSubmitButton > button {
  background: linear-gradient(135deg, #1d4ed8, #7c3aed) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  width: 100% !important;
  padding: 11px !important;
  box-shadow: 0 4px 14px rgba(37,99,235,0.3) !important;
  transition: all 0.2s !important;
}
.stFormSubmitButton > button:hover {
  box-shadow: 0 6px 20px rgba(37,99,235,0.4) !important;
  transform: translateY(-1px) !important;
}

/* ── Text input ── */
.stTextInput > div > div > input {
  background: #ffffff !important;
  border: 1px solid rgba(226,232,240,0.9) !important;
  border-radius: 12px !important;
  color: #0f172a !important;
  font-size: 14px !important;
  padding: 10px 16px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
.stTextInput > div > div > input:focus {
  border-color: #2563eb !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
.stTextInput > div > div > input::placeholder { color: #94a3b8 !important; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] { border: 1px solid rgba(226,232,240,0.9); border-radius: 12px; overflow: hidden; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }

/* ── Expander ── */
.streamlit-expanderHeader { background: #f8fafc !important; border: 1px solid rgba(226,232,240,0.9) !important; border-radius: 10px !important; color: #64748b !important; font-size: 13px !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] { background: #f8fafc !important; border: 1.5px dashed rgba(37,99,235,0.35) !important; border-radius: 16px !important; }

/* ── Alerts ── */
.stSuccess { background: #f0fdf4 !important; border: 1px solid #bbf7d0 !important; border-radius: 10px !important; color: #166534 !important; }
.stInfo    { background: #eff6ff !important; border: 1px solid #bfdbfe !important; border-radius: 10px !important; color: #1e40af !important; }
.stError   { background: #fef2f2 !important; border: 1px solid #fecaca !important; border-radius: 10px !important; color: #991b1b !important; }
.stWarning { background: #fffbeb !important; border: 1px solid #fde68a !important; border-radius: 10px !important; color: #92400e !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] { background: #f8fafc !important; border: 1px solid rgba(226,232,240,0.9) !important; border-radius: 12px !important; margin-bottom: 8px !important; }

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Selectbox / dropdown ── */
[data-testid="stSelectbox"] > div > div {
  background: #ffffff !important;
  border: 1px solid rgba(226,232,240,0.9) !important;
  border-radius: 10px !important;
  color: #0f172a !important;
}

@keyframes float-light {
  0%, 100% { opacity: var(--op, 0.09); transform: translateY(0px) rotate(var(--rot, -5deg)); }
  50%       { opacity: calc(var(--op, 0.09) * 1.6); transform: translateY(-14px) rotate(var(--rot, -5deg)); }
}
@keyframes blink-dot {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>""", unsafe_allow_html=True)

# Floating KPI numbers — dark/vivid on light background
st.markdown("""
<div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;user-select:none;">
  <span style="position:absolute;top:6%;left:18%;font-size:7rem;font-weight:900;color:rgba(37,99,235,0.08);--op:0.08;--rot:-8deg;animation:float-light 9s ease-in-out infinite;">94.2%</span>
  <span style="position:absolute;top:22%;right:3%;font-size:5rem;font-weight:900;color:rgba(124,58,237,0.07);--op:0.07;--rot:5deg;animation:float-light 11s ease-in-out infinite 2s;">OTIF</span>
  <span style="position:absolute;top:44%;left:20%;font-size:5.5rem;font-weight:900;color:rgba(16,185,129,0.07);--op:0.07;--rot:-3deg;animation:float-light 13s ease-in-out infinite 4s;">18d</span>
  <span style="position:absolute;top:66%;right:2%;font-size:6rem;font-weight:900;color:rgba(37,99,235,0.07);--op:0.07;--rot:7deg;animation:float-light 10s ease-in-out infinite 1s;">87.3%</span>
  <span style="position:absolute;top:80%;left:28%;font-size:4rem;font-weight:900;color:rgba(217,119,6,0.08);--op:0.08;--rot:-6deg;animation:float-light 14s ease-in-out infinite 3s;">12×</span>
  <span style="position:absolute;top:10%;left:55%;font-size:3.5rem;font-weight:900;color:rgba(16,185,129,0.06);--op:0.06;--rot:2deg;animation:float-light 12s ease-in-out infinite 5s;">BOM</span>
  <span style="position:absolute;bottom:12%;left:38%;font-size:5rem;font-weight:900;color:rgba(37,99,235,0.07);--op:0.07;--rot:3deg;animation:float-light 11s ease-in-out infinite 3.5s;">▲12.4%</span>
  <span style="position:absolute;bottom:30%;right:14%;font-size:3.5rem;font-weight:900;color:rgba(124,58,237,0.06);--op:0.06;--rot:-9deg;animation:float-light 9s ease-in-out infinite 7s;">JIT</span>
  <span style="position:absolute;top:35%;right:22%;font-size:3rem;font-weight:900;color:rgba(217,119,6,0.06);--op:0.06;--rot:6deg;animation:float-light 16s ease-in-out infinite 2.5s;">MOQ</span>
  <span style="position:absolute;bottom:6%;left:22%;font-size:4.5rem;font-weight:900;color:rgba(124,58,237,0.06);--op:0.06;--rot:4deg;animation:float-light 13s ease-in-out infinite 1.5s;">EOQ</span>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "orchestrator"   not in st.session_state:
    st.session_state.orchestrator   = SupplyChainOrchestrator()
if "init_report"    not in st.session_state:
    st.session_state.init_report    = None
if "responses"      not in st.session_state:
    st.session_state.responses      = []
if "df_display"     not in st.session_state:
    st.session_state.df_display     = None
if "sidebar_wide"   not in st.session_state:
    st.session_state.sidebar_wide   = False

orch = st.session_state.orchestrator

# Dynamic sidebar width
_sw = "680px" if st.session_state.sidebar_wide else "420px"
st.markdown(f"""<style>
section[data-testid="stSidebar"] {{ width: {_sw} !important; min-width: {_sw} !important; }}
section[data-testid="stSidebar"] > div:first-child {{ width: {_sw} !important; }}
</style>""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    hdr_left, hdr_right = st.columns([4, 1])
    with hdr_left:
        st.markdown("""
        <div style="padding:20px 0 14px 20px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <div style="background:linear-gradient(135deg,#1d4ed8,#7c3aed);border-radius:8px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;box-shadow:0 3px 10px rgba(29,78,216,0.25);">⚡</div>
            <span style="font-size:1.1rem;font-weight:800;color:#0f172a;letter-spacing:-0.02em;">Caeser.ai</span>
          </div>
          <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;padding-left:40px;">AI Supply Chain Analyst</div>
        </div>
        """, unsafe_allow_html=True)
    with hdr_right:
        st.markdown("<div style='padding-top:18px;'>", unsafe_allow_html=True)
        expand_icon = "↙" if st.session_state.sidebar_wide else "↗"
        expand_tip  = "Collapse chat" if st.session_state.sidebar_wide else "Expand chat"
        if st.button(expand_icon, help=expand_tip, key="toggle_sidebar"):
            st.session_state.sidebar_wide = not st.session_state.sidebar_wide
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='border-bottom:1px solid rgba(226,232,240,0.9);margin:0 0 4px;'></div>", unsafe_allow_html=True)

    if not orch.is_initialized:
        st.markdown("""
        <div style="padding:28px 20px;text-align:center;">
          <div style="font-size:0.875rem;font-weight:500;color:#64748b;margin-bottom:6px;">No data loaded yet</div>
          <div style="font-size:0.775rem;color:#94a3b8;line-height:1.6;">Upload a CSV in the main panel<br>to start chatting with your data.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Question history
        if st.session_state.responses:
            st.markdown("""
            <div style="padding:12px 20px 6px;">
              <div style="font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;">Previous Questions</div>
            </div>
            """, unsafe_allow_html=True)
            for i, resp in enumerate(reversed(st.session_state.responses)):
                q = resp["question"]
                q_short = q if len(q) <= 48 else q[:46] + "…"
                idx = len(st.session_state.responses) - 1 - i
                col_q, col_btn = st.columns([5, 1])
                with col_q:
                    st.markdown(f"""
                    <div style="padding:8px 12px;background:#f8fafc;border:1px solid rgba(226,232,240,0.9);border-left:2px solid #2563eb;border-radius:8px;font-size:0.775rem;color:#475569;line-height:1.4;margin-bottom:4px;">{q_short}</div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("↩", key=f"re_{idx}", help="Re-ask"):
                        st.session_state["prefill_question"] = q
                        st.rerun()
            st.markdown("<div style='height:2px;background:linear-gradient(90deg,transparent,rgba(37,99,235,0.15),transparent);margin:8px 20px 0;'></div>", unsafe_allow_html=True)

        # Chat messages
        st.markdown("<div style='padding:4px 4px 0;'>", unsafe_allow_html=True)
        if not st.session_state.responses:
            st.markdown("""
            <div style="padding:28px 16px;text-align:center;">
              <div style="font-size:1.8rem;margin-bottom:8px;">💬</div>
              <div style="font-size:0.85rem;font-weight:500;color:#64748b;">Ask a question to start</div>
            </div>
            """, unsafe_allow_html=True)
            quick_qs = orch.get_suggested_questions()
            if quick_qs:
                st.markdown("<div style='padding:0 4px;font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:6px;'>Suggested</div>", unsafe_allow_html=True)
                for i, q in enumerate(quick_qs[:4]):
                    if st.button(q, key=f"qs_{i}", use_container_width=True):
                        st.session_state["prefill_question"] = q
                        st.rerun()
        else:
            for resp in st.session_state.responses:
                with st.chat_message("user"):
                    st.write(resp["question"])
                with st.chat_message("assistant"):
                    if not resp["success"]:
                        st.error(f"Failed after {resp['iterations']} attempts.")
                        if resp.get("error"):
                            st.caption(resp["error"])
                    else:
                        if resp.get("explanation"):
                            exp = resp["explanation"]
                            st.write(exp.get("explanation", ""))
                            c1, c2 = st.columns(2)
                            c1.metric("Key Finding", exp.get("key_number", "—"))
                            c2.metric("Confidence",  exp.get("confidence", "—").title())
                            s_color = {"positive": "#16a34a", "negative": "#dc2626", "warning": "#d97706", "neutral": "#2563eb"}.get(exp.get("sentiment", "neutral"), "#2563eb")
                            if exp.get("industry_context"):
                                st.markdown(f'<div style="background:#f8fafc;border-left:3px solid {s_color};border-radius:6px;padding:8px 12px;font-size:0.775rem;color:#475569;margin:4px 0;">{exp["industry_context"]}</div>', unsafe_allow_html=True)

                        if resp.get("figure"):
                            st.plotly_chart(resp["figure"], use_container_width=True)
                            chart_html = resp["figure"].to_html(include_plotlyjs="cdn", full_html=True)
                            st.download_button("⬇️ Download Chart", data=chart_html, file_name="chart.html", mime="text/html", key=f"dl_{id(resp)}")
                        elif resp.get("result") is not None:
                            val = resp["result"]
                            if isinstance(val, pd.DataFrame):
                                st.dataframe(val, use_container_width=True)
                            elif isinstance(val, pd.Series):
                                st.dataframe(val.to_frame(), use_container_width=True)
                            else:
                                st.markdown(f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 16px;margin:4px 0;"><div style="color:#94a3b8;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:3px;">Result</div><div style="color:#1d4ed8;font-size:1.5rem;font-weight:700;">{val}</div></div>', unsafe_allow_html=True)

                        if resp.get("explanation"):
                            exp = resp["explanation"]
                            if exp.get("next_steps") or exp.get("limitations"):
                                with st.expander("📋 Next steps & limitations"):
                                    for s in exp.get("next_steps", []):
                                        st.markdown(f"- {s}")
                                    for lim in exp.get("limitations", []):
                                        st.markdown(f"- _{lim}_")
                        if resp.get("thought_process") and resp["iterations"] > 1:
                            with st.expander(f"🤔 Reasoning — {resp['iterations']} iterations"):
                                for step in resp["thought_process"]:
                                    icon = "✅" if step["status"] == "success" else "❌"
                                    st.markdown(f"**Iter {step['iteration']}** {icon}")
                                    if step.get("thought"): st.caption(step["thought"])
                                    if step.get("code"):    st.code(step["code"], language="python")
                                    if step.get("error"):   st.error(step["error"])
                        if resp.get("code"):
                            with st.expander("🔧 Code"):
                                st.code(resp["code"], language="python")
        st.markdown("</div>", unsafe_allow_html=True)

        # Input
        st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(37,99,235,0.15),transparent);margin:8px 0 12px;'></div>", unsafe_allow_html=True)
        prefill = st.session_state.pop("prefill_question", "")
        with st.form(key="chat_form", clear_on_submit=True):
            question = st.text_input("q", value=prefill, placeholder="Ask about your supply chain data…", label_visibility="collapsed")
            submitted = st.form_submit_button("Analyze ⚡", use_container_width=True)
        if submitted and question.strip():
            with st.spinner("Reasoning…"):
                response = orch.answer_question(question.strip())
                st.session_state.responses.append(response)
            st.rerun()

        if orch.memory.turn_count > 0:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ Clear", use_container_width=True):
                    orch.memory.clear()
                    st.session_state.responses = []
                    st.rerun()
            with c2:
                st.download_button("📥 Export", data=orch.memory.to_json(), file_name="caeser_chat.json", mime="application/json", use_container_width=True)

# ── LANDING PAGE ───────────────────────────────────────────────────────────────
if not orch.is_initialized:
    # Hero
    st.markdown("""
    <div style="text-align:center;padding:48px 0 28px;">
      <div style="display:inline-flex;align-items:center;gap:8px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:20px;padding:6px 16px;margin-bottom:20px;">
        <span style="font-size:0.7rem;font-weight:600;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.1em;">⚡ AI-Powered · Supply Chain Intelligence</span>
      </div>
      <div style="font-size:3rem;font-weight:900;color:#0f172a;letter-spacing:-0.04em;line-height:1.1;margin-bottom:14px;">
        Your supply chain data,<br>
        <span style="background:linear-gradient(135deg,#1d4ed8,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">answered instantly.</span>
      </div>
      <div style="font-size:1rem;color:#64748b;max-width:520px;margin:0 auto 10px;line-height:1.7;">
        Upload any CSV — inventory, orders, supplier scorecards, logistics data — and ask questions in plain English. Caeser.ai generates charts, KPIs, and insights in seconds.
      </div>
    </div>
    """, unsafe_allow_html=True)


    up_col, info_col = st.columns([1, 1], gap="large")

    with up_col:
        st.markdown("""
        <div style="background:#fff;border:1px solid rgba(226,232,240,0.9);border-radius:20px;padding:24px 22px 18px;box-shadow:0 4px 24px rgba(0,0,0,0.07);margin-bottom:14px;">
          <div style="text-align:center;margin-bottom:16px;">
            <div style="font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:4px;">Upload Your Supply Chain Data</div>
            <div style="font-size:0.775rem;color:#64748b;">CSV · TSV · Parquet · up to 5 GB</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        df_raw = render_upload_section()
        if df_raw is not None:
            with st.spinner("🔍 Analyzing supply chain data…"):
                report = orch.initialize(df_raw)
                st.session_state.init_report  = report
                st.session_state.df_display   = report["df_clean"]
                st.session_state.responses    = []
            st.rerun()

        # Example questions
        st.markdown("""
        <div style="background:#f8fafc;border:1px solid rgba(226,232,240,0.9);border-radius:14px;padding:14px 16px;margin-top:14px;">
          <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;">Try asking…</div>
          <div style="display:flex;flex-direction:column;gap:6px;">
            <div style="font-size:0.8rem;color:#475569;padding:7px 12px;background:#fff;border-radius:8px;border:1px solid rgba(226,232,240,0.9);">"Which suppliers have the longest lead times?"</div>
            <div style="font-size:0.8rem;color:#475569;padding:7px 12px;background:#fff;border-radius:8px;border:1px solid rgba(226,232,240,0.9);">"Show fill rate trends by product category"</div>
            <div style="font-size:0.8rem;color:#475569;padding:7px 12px;background:#fff;border-radius:8px;border:1px solid rgba(226,232,240,0.9);">"Which SKUs are at shortage risk this quarter?"</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with info_col:
        pass

    st.stop()

# ── MAIN INTERFACE ─────────────────────────────────────────────────────────────
df       = st.session_state.df_display
report   = st.session_state.init_report
industry = orch.industry_info
quality_after = orch.cleaning_report.data_quality_after
issues_fixed  = report["cleaning_report"].issues_fixed
q_color = "#16a34a" if quality_after > 90 else "#d97706" if quality_after > 75 else "#dc2626"

# Status bar
st.markdown(f"""
<div style="background:#fff;border:1px solid rgba(226,232,240,0.9);border-radius:14px;padding:10px 20px;margin-bottom:18px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;box-shadow:0 1px 6px rgba(0,0,0,0.04);">
  <div style="display:flex;align-items:center;gap:6px;">
    <div style="width:7px;height:7px;background:#16a34a;border-radius:50%;box-shadow:0 0 6px #16a34a;animation:blink-dot 2s ease-in-out infinite;"></div>
    <span style="font-size:0.7rem;color:#16a34a;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">LIVE</span>
  </div>
  <div style="height:14px;width:1px;background:rgba(226,232,240,0.9);"></div>
  <span style="font-size:0.75rem;color:#64748b;"><span style="color:#1d4ed8;font-weight:600;">{industry.get('industry','Supply Chain').title()}</span> · {industry.get('subdomain','')}</span>
  <div style="height:14px;width:1px;background:rgba(226,232,240,0.9);"></div>
  <span style="font-size:0.75rem;color:#64748b;">{df.shape[0]:,} rows · {df.shape[1]} cols</span>
  <div style="height:14px;width:1px;background:rgba(226,232,240,0.9);"></div>
  <span style="font-size:0.75rem;color:#64748b;">Quality <span style="color:{q_color};font-weight:600;">{quality_after:.0f}%</span></span>
  <div style="height:14px;width:1px;background:rgba(226,232,240,0.9);"></div>
  <span style="font-size:0.75rem;color:#64748b;">{issues_fixed} issues fixed</span>
  <div style="height:14px;width:1px;background:rgba(226,232,240,0.9);"></div>
  <span style="font-size:0.75rem;color:#64748b;">Confidence <span style="color:#1d4ed8;">{industry.get('confidence','medium').title()}</span></span>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊  Data Explorer", "🎯  Business Dashboard", "🔬  Quality Dashboard", "🧹  Cleaning Report", "Industry & KPIs"])

with tab1:
    render_dataset_overview(df)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    render_data_preview(df)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    render_column_info(df)

with tab2:
    st.markdown('<div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;">Auto-generated · Business Team View</div>', unsafe_allow_html=True)
    with st.spinner("Building business dashboard…"):
        biz_charts = build_business_dashboard(df)
    if not biz_charts:
        st.info("Upload a dataset with numeric or categorical columns to generate charts.")
    else:
        for title, fig in biz_charts:
            st.plotly_chart(fig, use_container_width=True)
            st.download_button(f"⬇️ Download — {title}", data=fig.to_html(include_plotlyjs="cdn", full_html=True), file_name=f"{title.lower().replace(' ','_')}.html", mime="text/html", key=f"biz_{title}")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;">Auto-generated · Quality & Data Science Team View</div>', unsafe_allow_html=True)
    with st.spinner("Building quality dashboard…"):
        qual_charts = build_quality_dashboard(df, report["cleaning_report"])
    for title, fig in qual_charts:
        st.plotly_chart(fig, use_container_width=True)
        st.download_button(f"⬇️ Download — {title}", data=fig.to_html(include_plotlyjs="cdn", full_html=True), file_name=f"{title.lower().replace(' ','_')}.html", mime="text/html", key=f"qual_{title}")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

with tab4:
    cleaning_exp = report.get("cleaning_explanation", {})
    if cleaning_exp:
        st.markdown(f"""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-left:3px solid #16a34a;border-radius:12px;padding:14px 18px;margin-bottom:14px;">
          <div style="color:#166534;font-weight:600;font-size:0.875rem;margin-bottom:5px;">{cleaning_exp.get('headline','Data cleaned successfully')}</div>
          <div style="color:#15803d;font-size:0.775rem;line-height:1.6;">{cleaning_exp.get('explanation','')}</div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Trust Score", f"{cleaning_exp.get('trust_score','N/A')}%")
        c2.metric("Issues Fixed", issues_fixed)
        c3.metric("Quality After", f"{quality_after:.0f}%")
        if cleaning_exp.get("recommendation"):
            st.info(f"💼 {cleaning_exp['recommendation']}")
    actions = report["cleaning_report"].actions
    if not actions:
        st.success("✅ Data is already clean — no issues found.")
    else:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        for action in actions:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(action.severity, "⚪")
            with st.expander(f"{icon}  {action.description}", expanded=action.severity == "high"):
                st.markdown(f"**Why:** {action.reason}")
                if action.before_value and action.after_value:
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Before:** `{action.before_value}`")
                    c2.markdown(f"**After:** `{action.after_value}`")

with tab5:
    c1, c2, c3 = st.columns(3)
    c1.metric("Industry",   industry.get("industry", "General").title())
    c2.metric("Confidence", industry.get("confidence", "medium").title())
    c3.metric("Domain",     (industry.get("subdomain") or "—").title()[:14])
    if industry.get("reasoning"):
        st.markdown(f'<div style="background:#f8fafc;border:1px solid rgba(226,232,240,0.9);border-radius:10px;padding:12px 16px;margin:12px 0;font-size:0.82rem;color:#64748b;line-height:1.6;">{industry["reasoning"]}</div>', unsafe_allow_html=True)
    if industry.get("key_metrics"):
        st.markdown("<div style='font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;'>Key KPIs detected</div>", unsafe_allow_html=True)
        pills = "".join([f'<span style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:20px;padding:4px 12px;font-size:12px;color:#1d4ed8;margin:3px;display:inline-block;font-weight:500;">{m}</span>' for m in industry["key_metrics"]])
        st.markdown(f'<div style="margin-bottom:16px;">{pills}</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;'>Suggested questions</div>", unsafe_allow_html=True)
    q_cols = st.columns(2)
    for i, q in enumerate(industry.get("typical_questions", [])):
        with q_cols[i % 2]:
            if st.button(q, key=f"sq_{q}", use_container_width=True):
                st.session_state["prefill_question"] = q
                st.rerun()
