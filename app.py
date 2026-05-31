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
    page_title="Ceaser.ai",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
* { box-sizing: border-box; }

.stApp {
  background-color: #050912;
  background-image:
    radial-gradient(ellipse at 15% 50%, rgba(59,130,246,0.08) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 15%, rgba(139,92,246,0.05) 0%, transparent 40%),
    radial-gradient(ellipse at 65% 85%, rgba(34,197,94,0.04) 0%, transparent 40%),
    linear-gradient(rgba(30,41,59,0.3) 1px, transparent 1px),
    linear-gradient(90deg, rgba(30,41,59,0.3) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 100% 100%, 44px 44px, 44px 44px;
  color: #e2e8f0;
}

/* ── Sidebar width & style ── */
section[data-testid="stSidebar"] {
  width: 420px !important;
  min-width: 420px !important;
  background: rgba(7,11,22,0.97) !important;
  border-right: 1px solid rgba(30,41,59,0.8) !important;
}
section[data-testid="stSidebar"] > div:first-child {
  width: 420px !important;
  padding: 0 0 80px 0 !important;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(51,65,85,0.8); border-radius: 4px; }

[data-testid="stMetric"] {
  background: rgba(15,23,42,0.75);
  border: 1px solid rgba(51,65,85,0.5);
  border-radius: 14px;
  padding: 14px 18px;
  backdrop-filter: blur(12px);
}
[data-testid="stMetric"]:hover { border-color: rgba(59,130,246,0.4); }
[data-testid="stMetricValue"] { color: #60a5fa !important; font-size: 1.3rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #475569 !important; font-size: 0.58rem !important; text-transform: uppercase; letter-spacing: 0.12em; }

.stTabs [data-baseweb="tab-list"] {
  background: rgba(15,23,42,0.6);
  border-radius: 12px;
  padding: 4px;
  border: 1px solid rgba(51,65,85,0.4);
  gap: 2px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  border-radius: 8px;
  color: #475569;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
  background: rgba(59,130,246,0.15) !important;
  color: #60a5fa !important;
  border: 1px solid rgba(59,130,246,0.3) !important;
}

.stButton > button {
  background: rgba(30,58,138,0.2);
  color: #93c5fd;
  border: 1px solid rgba(59,130,246,0.2);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.stButton > button:hover {
  background: rgba(59,130,246,0.2);
  border-color: rgba(59,130,246,0.5);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(59,130,246,0.2);
}

.stFormSubmitButton > button {
  background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  width: 100% !important;
  padding: 11px !important;
  box-shadow: 0 2px 12px rgba(37,99,235,0.35) !important;
  transition: all 0.2s !important;
}
.stFormSubmitButton > button:hover {
  background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
  box-shadow: 0 4px 24px rgba(59,130,246,0.45) !important;
  transform: translateY(-1px) !important;
}

.stTextInput > div > div > input {
  background: rgba(15,23,42,0.9) !important;
  border: 1px solid rgba(51,65,85,0.6) !important;
  border-radius: 12px !important;
  color: #e2e8f0 !important;
  font-size: 14px !important;
  padding: 10px 16px !important;
}
.stTextInput > div > div > input:focus {
  border-color: rgba(59,130,246,0.5) !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}

[data-testid="stDataFrame"] { border: 1px solid rgba(51,65,85,0.4); border-radius: 12px; overflow: hidden; }
.streamlit-expanderHeader { background: rgba(15,23,42,0.6) !important; border: 1px solid rgba(51,65,85,0.4) !important; border-radius: 10px !important; color: #94a3b8 !important; font-size: 13px !important; }
[data-testid="stFileUploader"] { background: rgba(15,23,42,0.4) !important; border: 1.5px dashed rgba(59,130,246,0.3) !important; border-radius: 16px !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stChatMessage"] { background: rgba(15,23,42,0.5) !important; border: 1px solid rgba(51,65,85,0.3) !important; border-radius: 12px !important; margin-bottom: 8px !important; }
.stSuccess { background: rgba(5,46,22,0.5) !important; border: 1px solid rgba(22,101,52,0.5) !important; border-radius: 10px !important; }
.stInfo    { background: rgba(7,29,82,0.5) !important;  border: 1px solid rgba(29,78,216,0.3) !important;  border-radius: 10px !important; }
.stError   { background: rgba(69,10,10,0.5) !important; border: 1px solid rgba(185,28,28,0.3) !important; border-radius: 10px !important; }

@keyframes fade-float {
  0%, 100% { opacity: var(--op, 0.04); transform: translateY(0px) rotate(var(--rot, -5deg)); }
  50% { opacity: calc(var(--op, 0.04) * 1.8); transform: translateY(-14px) rotate(var(--rot, -5deg)); }
}
@keyframes blink-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>""", unsafe_allow_html=True)

# Floating KPI background
st.markdown("""
<div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;user-select:none;">
  <span style="position:absolute;top:7%;left:22%;font-size:7rem;font-weight:900;color:rgba(59,130,246,0.05);--op:0.05;--rot:-8deg;animation:fade-float 9s ease-in-out infinite;">94.2%</span>
  <span style="position:absolute;top:20%;right:4%;font-size:5rem;font-weight:900;color:rgba(34,197,94,0.045);--op:0.045;--rot:5deg;animation:fade-float 11s ease-in-out infinite 2s;">OTIF</span>
  <span style="position:absolute;top:42%;left:22%;font-size:5.5rem;font-weight:900;color:rgba(139,92,246,0.04);--op:0.04;--rot:-3deg;animation:fade-float 13s ease-in-out infinite 4s;">18d</span>
  <span style="position:absolute;top:64%;right:3%;font-size:6rem;font-weight:900;color:rgba(59,130,246,0.04);--op:0.04;--rot:7deg;animation:fade-float 10s ease-in-out infinite 1s;">87.3%</span>
  <span style="position:absolute;top:80%;left:30%;font-size:4rem;font-weight:900;color:rgba(245,158,11,0.04);--op:0.04;--rot:-6deg;animation:fade-float 14s ease-in-out infinite 3s;">12×</span>
  <span style="position:absolute;top:10%;left:55%;font-size:3.5rem;font-weight:900;color:rgba(34,197,94,0.03);--op:0.03;--rot:2deg;animation:fade-float 12s ease-in-out infinite 5s;">BOM</span>
  <span style="position:absolute;bottom:10%;left:40%;font-size:5rem;font-weight:900;color:rgba(59,130,246,0.04);--op:0.04;--rot:3deg;animation:fade-float 11s ease-in-out infinite 3.5s;">▲12.4%</span>
  <span style="position:absolute;bottom:28%;right:15%;font-size:3.5rem;font-weight:900;color:rgba(34,197,94,0.03);--op:0.03;--rot:-9deg;animation:fade-float 9s ease-in-out infinite 7s;">JIT</span>
  <span style="position:absolute;top:33%;right:25%;font-size:3rem;font-weight:900;color:rgba(245,158,11,0.03);--op:0.03;--rot:6deg;animation:fade-float 16s ease-in-out infinite 2.5s;">MOQ</span>
  <span style="position:absolute;bottom:5%;left:25%;font-size:4.5rem;font-weight:900;color:rgba(139,92,246,0.03);--op:0.03;--rot:4deg;animation:fade-float 13s ease-in-out infinite 1.5s;">EOQ</span>
</div>
""", unsafe_allow_html=True)

# Session state
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = SupplyChainOrchestrator()
if "init_report" not in st.session_state:
    st.session_state.init_report = None
if "responses" not in st.session_state:
    st.session_state.responses = []
if "df_display" not in st.session_state:
    st.session_state.df_display = None

orch = st.session_state.orchestrator

# ── SIDEBAR ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Sidebar header
    st.markdown("""
    <div style="padding:20px 20px 14px;border-bottom:1px solid rgba(30,41,59,0.8);">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
        <div style="background:linear-gradient(135deg,#1d4ed8,#7c3aed);border-radius:8px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;box-shadow:0 3px 10px rgba(29,78,216,0.4);">⚡</div>
        <span style="font-size:1.1rem;font-weight:700;color:#e2e8f0;letter-spacing:-0.02em;">Ceaser.ai</span>
      </div>
      <div style="font-size:0.65rem;color:#334155;text-transform:uppercase;letter-spacing:0.1em;padding-left:40px;">AI Supply Chain Analyst</div>
    </div>
    """, unsafe_allow_html=True)

    if not orch.is_initialized:
        st.markdown("""
        <div style="padding:24px 20px;text-align:center;">
          <div style="font-size:2rem;margin-bottom:10px;">🏭</div>
          <div style="font-size:0.875rem;font-weight:500;color:#64748b;margin-bottom:6px;">No data loaded yet</div>
          <div style="font-size:0.775rem;color:#334155;line-height:1.5;">Upload a CSV in the main panel<br>to start chatting with your data.</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # ── Question history (ChatGPT-style) ──
        if st.session_state.responses:
            st.markdown("""
            <div style="padding:12px 20px 6px;">
              <div style="font-size:0.6rem;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;">Previous Questions</div>
            </div>
            """, unsafe_allow_html=True)

            for i, resp in enumerate(reversed(st.session_state.responses)):
                q = resp["question"]
                q_short = q if len(q) <= 48 else q[:46] + "…"
                idx = len(st.session_state.responses) - 1 - i
                col_q, col_btn = st.columns([5, 1])
                with col_q:
                    st.markdown(f"""
                    <div style="
                      padding:8px 12px;
                      background:rgba(15,23,42,0.5);
                      border:1px solid rgba(51,65,85,0.25);
                      border-left:2px solid rgba(59,130,246,0.4);
                      border-radius:8px;
                      font-size:0.775rem;
                      color:#94a3b8;
                      line-height:1.4;
                      margin-bottom:4px;
                      cursor:default;
                    ">{q_short}</div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("↩", key=f"re_{idx}", help="Re-ask this question"):
                        st.session_state["prefill_question"] = q
                        st.rerun()

            st.markdown("<div style='height:2px;background:linear-gradient(90deg,transparent,rgba(59,130,246,0.2),transparent);margin:8px 20px 0;'></div>", unsafe_allow_html=True)

        # ── Chat messages ──
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
                st.markdown("<div style='padding:0 4px;font-size:0.6rem;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:6px;'>Suggested</div>", unsafe_allow_html=True)
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
                            c2.metric("Confidence", exp.get("confidence", "—").title())

                            s_color = {"positive": "#4ade80", "negative": "#f87171", "warning": "#fbbf24", "neutral": "#60a5fa"}.get(exp.get("sentiment", "neutral"), "#60a5fa")
                            if exp.get("industry_context"):
                                st.markdown(f'<div style="background:rgba(15,23,42,0.5);border-left:3px solid {s_color};border-radius:6px;padding:8px 12px;font-size:0.775rem;color:#94a3b8;margin:4px 0;">{exp["industry_context"]}</div>', unsafe_allow_html=True)

                        if resp.get("figure"):
                            st.plotly_chart(resp["figure"], use_container_width=True)
                            chart_html = resp["figure"].to_html(include_plotlyjs="cdn", full_html=True)
                            st.download_button(
                                "⬇️ Download Chart",
                                data=chart_html,
                                file_name="chart.html",
                                mime="text/html",
                                key=f"dl_{id(resp)}",
                            )
                        elif resp.get("result") is not None:
                            val = resp["result"]
                            if isinstance(val, pd.DataFrame):
                                st.dataframe(val, use_container_width=True)
                            elif isinstance(val, pd.Series):
                                st.dataframe(val.to_frame(), use_container_width=True)
                            else:
                                st.markdown(f'<div style="background:rgba(15,23,42,0.6);border:1px solid rgba(51,65,85,0.4);border-radius:10px;padding:12px 16px;margin:4px 0;"><div style="color:#475569;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:3px;">Result</div><div style="color:#60a5fa;font-size:1.5rem;font-weight:700;">{val}</div></div>', unsafe_allow_html=True)

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
                                    if step.get("thought"):
                                        st.caption(step["thought"])
                                    if step.get("code"):
                                        st.code(step["code"], language="python")
                                    if step.get("error"):
                                        st.error(step["error"])

                        if resp.get("code"):
                            with st.expander("🔧 Code"):
                                st.code(resp["code"], language="python")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Input form ──
        st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(59,130,246,0.2),transparent);margin:8px 0 12px;'></div>", unsafe_allow_html=True)

        prefill = st.session_state.pop("prefill_question", "")
        with st.form(key="chat_form", clear_on_submit=True):
            question = st.text_input(
                "question",
                value=prefill,
                placeholder="Ask about your supply chain data…",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Analyze 🚀", use_container_width=True)

        if submitted and question.strip():
            with st.spinner("Reasoning…"):
                response = orch.answer_question(question.strip())
                st.session_state.responses.append(response)
            st.rerun()

        # Clear button
        if orch.memory.turn_count > 0:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ Clear chat", use_container_width=True):
                    orch.memory.clear()
                    st.session_state.responses = []
                    st.rerun()
            with c2:
                st.download_button(
                    "📥 Export",
                    data=orch.memory.to_json(),
                    file_name="ceaser_chat.json",
                    mime="application/json",
                    use_container_width=True,
                )

# ── MAIN AREA ────────────────────────────────────────────────────────────────────

# ── LANDING PAGE (not initialized) ──────────────────────────────────────────────
if not orch.is_initialized:
    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px;">
      <div style="font-size:0.7rem;color:#334155;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:16px;">Supply Chain Intelligence · ceaser.ai</div>
      <div style="font-size:2.2rem;font-weight:800;color:#e2e8f0;letter-spacing:-0.03em;line-height:1.2;margin-bottom:10px;">
        Ask your data anything.<br>
        <span style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Get supply chain answers.</span>
      </div>
      <div style="font-size:0.9rem;color:#475569;max-width:480px;margin:0 auto;line-height:1.6;">Upload any CSV — inventory, orders, supplier data — and ask questions in plain English.</div>
    </div>
    """, unsafe_allow_html=True)

    # KPI sticker row
    st.markdown("""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:24px 0;justify-content:center;">
      <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(59,130,246,0.25);border-radius:18px;padding:18px 22px;min-width:145px;backdrop-filter:blur(20px);box-shadow:0 8px 32px rgba(0,0,0,0.4);">
        <div style="font-size:1.3rem;margin-bottom:4px;">📦</div>
        <div style="font-size:0.58rem;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:2px;">OTIF Rate</div>
        <div style="font-size:1.8rem;font-weight:800;color:#60a5fa;line-height:1;">94.2%</div>
        <div style="font-size:0.68rem;color:#4ade80;margin-top:5px;">↑ 2.1% vs last qtr</div>
      </div>
      <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(34,197,94,0.2);border-radius:18px;padding:18px 22px;min-width:145px;backdrop-filter:blur(20px);box-shadow:0 8px 32px rgba(0,0,0,0.4);">
        <div style="font-size:1.3rem;margin-bottom:4px;">⏱️</div>
        <div style="font-size:0.58rem;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:2px;">Avg Lead Time</div>
        <div style="font-size:1.8rem;font-weight:800;color:#4ade80;line-height:1;">18 days</div>
        <div style="font-size:0.68rem;color:#4ade80;margin-top:5px;">↓ 3d improvement</div>
      </div>
      <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(245,158,11,0.2);border-radius:18px;padding:18px 22px;min-width:145px;backdrop-filter:blur(20px);box-shadow:0 8px 32px rgba(0,0,0,0.4);">
        <div style="font-size:1.3rem;margin-bottom:4px;">📊</div>
        <div style="font-size:0.58rem;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:2px;">Fill Rate</div>
        <div style="font-size:1.8rem;font-weight:800;color:#fbbf24;line-height:1;">87.3%</div>
        <div style="font-size:0.68rem;color:#4ade80;margin-top:5px;">↑ 5% this month</div>
      </div>
      <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(139,92,246,0.2);border-radius:18px;padding:18px 22px;min-width:145px;backdrop-filter:blur(20px);box-shadow:0 8px 32px rgba(0,0,0,0.4);">
        <div style="font-size:1.3rem;margin-bottom:4px;">🔄</div>
        <div style="font-size:0.58rem;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:2px;">Inventory Turns</div>
        <div style="font-size:1.8rem;font-weight:800;color:#a78bfa;line-height:1;">12×</div>
        <div style="font-size:0.68rem;color:#4ade80;margin-top:5px;">↑ vs industry 8×</div>
      </div>
      <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(239,68,68,0.2);border-radius:18px;padding:18px 22px;min-width:145px;backdrop-filter:blur(20px);box-shadow:0 8px 32px rgba(0,0,0,0.4);">
        <div style="font-size:1.3rem;margin-bottom:4px;">⚠️</div>
        <div style="font-size:0.58rem;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:2px;">Shortage Risk</div>
        <div style="font-size:1.8rem;font-weight:800;color:#f87171;line-height:1;">3 SKUs</div>
        <div style="font-size:0.68rem;color:#f87171;margin-top:5px;">↑ action needed</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    up_col, info_col = st.columns([1, 1], gap="large")

    with up_col:
        st.markdown("""
        <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(59,130,246,0.2);border-radius:20px;padding:24px 22px 18px;backdrop-filter:blur(20px);box-shadow:0 12px 48px rgba(0,0,0,0.5);margin-bottom:14px;">
          <div style="text-align:center;margin-bottom:16px;">
            <div style="font-size:2.2rem;margin-bottom:8px;">🏭</div>
            <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;">Upload Your Supply Chain Data</div>
            <div style="font-size:0.775rem;color:#475569;">CSV files from ERP, WMS, TMS, or any supply chain system</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        df_raw = render_upload_section()
        if df_raw is not None:
            with st.spinner("🔍 Analyzing supply chain data..."):
                report = orch.initialize(df_raw)
                st.session_state.init_report = report
                st.session_state.df_display = report["df_clean"]
                st.session_state.responses = []
            st.rerun()

    with info_col:
        for icon, title, desc, color in [
            ("🔍", "Auto-detect supply chain domain", "Identifies your vertical: EMS, semiconductor, 3PL, automotive, procurement", "#3b82f6"),
            ("🧹", "Intelligent data cleaning", "Fixes missing values & type errors — every decision explained with a full audit trail", "#22c55e"),
            ("🤔", "Self-healing ReAct analysis", "Writes and debugs its own Python code — up to 4 self-correction attempts per query", "#a78bfa"),
            ("📊", "KPI-driven insights", "Translates findings into OTIF, fill rate, lead time, and shortage risk language", "#fbbf24"),
        ]:
            st.markdown(f"""
            <div style="display:flex;gap:14px;align-items:flex-start;background:rgba(15,23,42,0.6);border:1px solid rgba(51,65,85,0.3);border-left:3px solid {color};border-radius:14px;padding:13px 16px;margin-bottom:10px;backdrop-filter:blur(8px);">
              <div style="font-size:1.2rem;flex-shrink:0;margin-top:1px;">{icon}</div>
              <div>
                <div style="font-size:0.85rem;font-weight:600;color:#e2e8f0;margin-bottom:3px;">{title}</div>
                <div style="font-size:0.76rem;color:#64748b;line-height:1.5;">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.stop()

# ── MAIN AREA (initialized) ──────────────────────────────────────────────────────
df = st.session_state.df_display
report = st.session_state.init_report
industry = orch.industry_info
quality_after = orch.cleaning_report.data_quality_after
issues_fixed = report["cleaning_report"].issues_fixed
q_color = "#4ade80" if quality_after > 90 else "#fbbf24" if quality_after > 75 else "#f87171"

# Status bar
st.markdown(f"""
<div style="background:rgba(15,23,42,0.75);border:1px solid rgba(51,65,85,0.4);border-radius:14px;padding:10px 20px;margin-bottom:18px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;backdrop-filter:blur(12px);">
  <div style="display:flex;align-items:center;gap:6px;">
    <div style="width:7px;height:7px;background:#22c55e;border-radius:50%;box-shadow:0 0 8px #22c55e;animation:blink-dot 2s ease-in-out infinite;"></div>
    <span style="font-size:0.7rem;color:#4ade80;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;">LIVE</span>
  </div>
  <div style="height:14px;width:1px;background:rgba(51,65,85,0.6);"></div>
  <span style="font-size:0.75rem;color:#64748b;"><span style="color:#93c5fd;font-weight:600;">{industry.get('industry','Supply Chain').title()}</span> · {industry.get('subdomain','')}</span>
  <div style="height:14px;width:1px;background:rgba(51,65,85,0.6);"></div>
  <span style="font-size:0.75rem;color:#64748b;">{df.shape[0]:,} rows · {df.shape[1]} cols</span>
  <div style="height:14px;width:1px;background:rgba(51,65,85,0.6);"></div>
  <span style="font-size:0.75rem;color:#64748b;">Quality <span style="color:{q_color};font-weight:600;">{quality_after:.0f}%</span></span>
  <div style="height:14px;width:1px;background:rgba(51,65,85,0.6);"></div>
  <span style="font-size:0.75rem;color:#64748b;">{issues_fixed} issues fixed</span>
  <div style="height:14px;width:1px;background:rgba(51,65,85,0.6);"></div>
  <span style="font-size:0.75rem;color:#64748b;">Confidence <span style="color:#93c5fd;">{industry.get('confidence','medium').title()}</span></span>
</div>
""", unsafe_allow_html=True)

# Full-width data explorer
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊  Data Explorer", "🎯  Business Dashboard", "🔬  Quality Dashboard", "🧹  Cleaning Report", "🏭  Industry & KPIs"])

with tab1:
    render_dataset_overview(df)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    render_data_preview(df)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    render_column_info(df)

with tab2:
    st.markdown("""
    <div style="font-size:0.62rem;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;">
      Auto-generated · Business Team View
    </div>
    """, unsafe_allow_html=True)
    with st.spinner("Building business dashboard…"):
        biz_charts = build_business_dashboard(df)
    if not biz_charts:
        st.info("Upload a dataset with numeric or categorical columns to generate charts.")
    else:
        for title, fig in biz_charts:
            st.plotly_chart(fig, use_container_width=True)
            chart_html = fig.to_html(include_plotlyjs="cdn", full_html=True)
            st.download_button(
                f"⬇️ Download — {title}",
                data=chart_html,
                file_name=f"{title.lower().replace(' ','_')}.html",
                mime="text/html",
                key=f"biz_{title}",
            )
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

with tab3:
    st.markdown("""
    <div style="font-size:0.62rem;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;">
      Auto-generated · Quality & Data Science Team View
    </div>
    """, unsafe_allow_html=True)
    with st.spinner("Building quality dashboard…"):
        qual_charts = build_quality_dashboard(df, report["cleaning_report"])
    for title, fig in qual_charts:
        st.plotly_chart(fig, use_container_width=True)
        chart_html = fig.to_html(include_plotlyjs="cdn", full_html=True)
        st.download_button(
            f"⬇️ Download — {title}",
            data=chart_html,
            file_name=f"{title.lower().replace(' ','_')}.html",
            mime="text/html",
            key=f"qual_{title}",
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

with tab4:
    cleaning_exp = report.get("cleaning_explanation", {})
    if cleaning_exp:
        st.markdown(f"""
        <div style="background:rgba(5,46,22,0.4);border:1px solid rgba(22,101,52,0.4);border-left:3px solid #4ade80;border-radius:12px;padding:14px 18px;margin-bottom:14px;">
          <div style="color:#4ade80;font-weight:600;font-size:0.9rem;margin-bottom:5px;">{cleaning_exp.get('headline','Data cleaned successfully')}</div>
          <div style="color:#86efac;font-size:0.8rem;line-height:1.6;">{cleaning_exp.get('explanation','')}</div>
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
    c1.metric("Industry", industry.get("industry", "General").title())
    c2.metric("Confidence", industry.get("confidence", "medium").title())
    c3.metric("Domain", (industry.get("subdomain") or "—").title()[:14])

    if industry.get("reasoning"):
        st.markdown(f"""
        <div style="background:rgba(15,23,42,0.6);border:1px solid rgba(51,65,85,0.3);border-radius:10px;padding:12px 16px;margin:12px 0;font-size:0.82rem;color:#94a3b8;line-height:1.6;">{industry['reasoning']}</div>
        """, unsafe_allow_html=True)

    if industry.get("key_metrics"):
        st.markdown("<div style='font-size:0.62rem;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;'>Key KPIs detected</div>", unsafe_allow_html=True)
        pills = "".join([
            f'<span style="background:rgba(30,58,138,0.3);border:1px solid rgba(59,130,246,0.2);border-radius:20px;padding:4px 12px;font-size:12px;color:#93c5fd;margin:3px;display:inline-block;">{m}</span>'
            for m in industry["key_metrics"]
        ])
        st.markdown(f'<div style="margin-bottom:16px;">{pills}</div>', unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.62rem;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;'>Suggested questions — click to send to chat</div>", unsafe_allow_html=True)
    q_cols = st.columns(2)
    for i, q in enumerate(industry.get("typical_questions", [])):
        with q_cols[i % 2]:
            if st.button(q, key=f"sq_{q}", use_container_width=True):
                st.session_state["prefill_question"] = q
                st.rerun()
