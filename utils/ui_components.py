"""
ui_components.py
----------------
Custom UI components for DA Agent.
Includes branded loading animations, spinner, and page header.
"""

import streamlit as st


def inject_custom_css():
    """
    Injects global CSS for the slate/orange theme and
    the stick figure loading animation.
    Call this once at the top of app.py.
    """
    st.markdown("""
    <style>
    /* ── Global font & background ───────────────────── */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }

    /* ── Sidebar styling ────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #2E3440 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ECEFF4 !important;
    }
    section[data-testid="stSidebar"] .stCaption {
        color: rgba(255,255,255,0.45) !important;
    }

    /* ── Tab styling ────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid #F1EFE8;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        color: #888780;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #E8640C !important;
        border-bottom: 2px solid #E8640C !important;
        background: transparent !important;
    }

    /* ── Metric cards ───────────────────────────────── */
    [data-testid="stMetric"] {
        background: #F1EFE8;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 3px solid #E8640C;
    }
    [data-testid="stMetricLabel"] {
        font-size: 12px !important;
        color: #5F5E5A !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 22px !important;
        font-weight: 600 !important;
        color: #2C2C2A !important;
    }

    /* ── Buttons ────────────────────────────────────── */
    .stButton > button {
        background-color: #E8640C;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #CF560A;
        color: white;
    }

    /* ── File uploader ──────────────────────────────── */
    [data-testid="stFileUploader"] {
        border: 2px dashed #E8640C !important;
        border-radius: 10px;
        padding: 12px;
    }

    /* ── Stick figure animation ─────────────────────── */
    @keyframes walk {
        0%   { transform: translateX(-60px); }
        100% { transform: translateX(60px); }
    }
    @keyframes leftArm {
        0%, 100% { transform: rotate(-30deg); }
        50%       { transform: rotate(30deg); }
    }
    @keyframes rightArm {
        0%, 100% { transform: rotate(30deg); }
        50%       { transform: rotate(-30deg); }
    }
    @keyframes leftLeg {
        0%, 100% { transform: rotate(-25deg); }
        50%       { transform: rotate(25deg); }
    }
    @keyframes rightLeg {
        0%, 100% { transform: rotate(25deg); }
        50%       { transform: rotate(-25deg); }
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0px); }
        50%       { transform: translateY(-4px); }
    }
    @keyframes fadeText {
        0%, 100% { opacity: 0.4; }
        50%       { opacity: 1; }
    }
    @keyframes spin-ring {
        to { transform: rotate(360deg); }
    }

    .stick-loader-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 0 20px;
        gap: 16px;
    }
    .stick-stage {
        width: 160px;
        height: 80px;
        position: relative;
        overflow: hidden;
    }
    .stick-figure {
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        animation: walk 1s ease-in-out infinite alternate,
                   bounce 0.5s ease-in-out infinite;
    }
    .stick-text {
        font-size: 13px;
        color: #E8640C;
        font-weight: 500;
        animation: fadeText 1.4s ease-in-out infinite;
        letter-spacing: 0.5px;
    }
    .stick-subtext {
        font-size: 11px;
        color: #888780;
        margin-top: -10px;
    }

    /* ── Progress bar override ──────────────────────── */
    .stProgress > div > div {
        background-color: #E8640C !important;
    }

    /* ── Footer ─────────────────────────────────────── */
    .da-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #2E3440;
        color: rgba(255,255,255,0.45);
        font-size: 11px;
        padding: 6px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 999;
    }
    .da-footer .footer-status {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .da-footer .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #639922;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)


def show_stick_figure_loader(message: str = "Analysing your data..."):
    """
    Renders an animated stick figure loading animation.
    Use inside a st.empty() placeholder so it can be cleared later.

    WHY: A branded loading state makes the app feel alive and professional
    instead of showing a blank screen while processing runs.

    Usage:
        placeholder = st.empty()
        with placeholder:
            show_stick_figure_loader("Profiling dataset...")
        # ... do work ...
        placeholder.empty()  # clears the animation
    """
    st.markdown(f"""
    <div class="stick-loader-wrap">

      <!-- Stick figure SVG with animated limbs -->
      <div class="stick-stage">
        <div class="stick-figure">
          <svg width="48" height="72" viewBox="0 0 48 72" fill="none"
               xmlns="http://www.w3.org/2000/svg">

            <!-- Head -->
            <circle cx="24" cy="10" r="8" stroke="#E8640C" stroke-width="2.5" fill="none"/>

            <!-- Body -->
            <line x1="24" y1="18" x2="24" y2="42"
                  stroke="#E8640C" stroke-width="2.5" stroke-linecap="round"/>

            <!-- Left arm -->
            <g style="transform-origin: 24px 24px;
                      animation: leftArm 0.5s ease-in-out infinite;">
              <line x1="24" y1="24" x2="8" y2="36"
                    stroke="#E8640C" stroke-width="2.5" stroke-linecap="round"/>
            </g>

            <!-- Right arm -->
            <g style="transform-origin: 24px 24px;
                      animation: rightArm 0.5s ease-in-out infinite;">
              <line x1="24" y1="24" x2="40" y2="36"
                    stroke="#E8640C" stroke-width="2.5" stroke-linecap="round"/>
            </g>

            <!-- Left leg -->
            <g style="transform-origin: 24px 42px;
                      animation: leftLeg 0.5s ease-in-out infinite;">
              <line x1="24" y1="42" x2="12" y2="62"
                    stroke="#E8640C" stroke-width="2.5" stroke-linecap="round"/>
            </g>

            <!-- Right leg -->
            <g style="transform-origin: 24px 42px;
                      animation: rightLeg 0.5s ease-in-out infinite;">
              <line x1="24" y1="42" x2="36" y2="62"
                    stroke="#E8640C" stroke-width="2.5" stroke-linecap="round"/>
            </g>

          </svg>
        </div>
      </div>

      <div class="stick-text">{message}</div>
      <div class="stick-subtext">Please wait a moment</div>
    </div>
    """, unsafe_allow_html=True)


def show_page_header():
    """
    Renders the branded DA Agent header with logo text.
    Place at the top of the main content area.
    """
    st.markdown("""
    <div style="display:flex; align-items:center; gap:14px;
                padding: 8px 0 20px; border-bottom: 2px solid #E8640C; margin-bottom: 24px;">
        <div style="background:#2E3440; border-radius:10px;
                    width:44px; height:44px; display:flex;
                    align-items:center; justify-content:center;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                 stroke="#E8640C" stroke-width="2" stroke-linecap="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M3 12h3m12 0h3M12 3v3m0 12v3
                         M6.34 6.34l2.12 2.12m7.08 7.08 2.12 2.12
                         M17.66 6.34l-2.12 2.12M8.46 15.54l-2.12 2.12"/>
            </svg>
        </div>
        <div>
            <div style="font-size:20px; font-weight:700;
                        color:#2C2C2A; letter-spacing:0.3px;">
                DATA <span style="color:#E8640C;">AGENT</span>
            </div>
            <div style="font-size:11px; color:#888780; margin-top:1px;">
                No Queries. Just Answers.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_progress_steps(current_step: int):
    """
    Renders a visual progress indicator showing which phase the user is on.
    current_step: 1=Upload, 2=Profile, 3=AI Q&A, 4=Insights
    """
    steps = ["Upload", "Profile", "AI Q&A", "Insights"]
    cols = st.columns(len(steps))

    for i, (col, step) in enumerate(zip(cols, steps)):
        step_num = i + 1
        if step_num < current_step:
            # Completed
            col.markdown(f"""
            <div style="text-align:center;">
                <div style="width:28px;height:28px;border-radius:50%;
                            background:#E8640C;color:white;font-size:12px;
                            font-weight:600;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 4px;">✓</div>
                <div style="font-size:11px;color:#E8640C;font-weight:500;">{step}</div>
            </div>
            """, unsafe_allow_html=True)
        elif step_num == current_step:
            # Active
            col.markdown(f"""
            <div style="text-align:center;">
                <div style="width:28px;height:28px;border-radius:50%;
                            background:#E8640C;color:white;font-size:12px;
                            font-weight:600;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 4px;
                            box-shadow:0 0 0 4px rgba(232,100,12,0.2);">{step_num}</div>
                <div style="font-size:11px;color:#E8640C;font-weight:600;">{step}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Upcoming
            col.markdown(f"""
            <div style="text-align:center;">
                <div style="width:28px;height:28px;border-radius:50%;
                            border:2px solid #D3D1C7;color:#888780;font-size:12px;
                            font-weight:500;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 4px;">{step_num}</div>
                <div style="font-size:11px;color:#888780;">{step}</div>
            </div>
            """, unsafe_allow_html=True)


def show_footer():
    """
    Renders a fixed footer at the bottom of the page.
    """
    st.markdown("""
    <div class="da-footer">
        <span>DA Agent v2.0 &nbsp;·&nbsp; Autonomous Data Analyst</span>
        <div class="footer-status">
            <span class="status-dot"></span>
            <span>All systems operational</span>
        </div>
    </div>
    <div style="height:32px;"></div>
    """, unsafe_allow_html=True)