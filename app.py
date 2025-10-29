# ===============================
# 💧 SCADA Turbidity Dashboard - Mobile Responsive Version
# ===============================

import streamlit as st
import time
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="SCADA Turbidity Monitor",
    layout="wide",
    initial_sidebar_state="collapsed"  # Auto-collapse sidebar on mobile
)

# -------------------------------
# CONFIGURATION
# -------------------------------
ESP32_IP = "http://192.168.103.233"
DATA_URL = f"{ESP32_IP}/data"

# -------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------
if "refresh_sec" not in st.session_state:
    st.session_state.refresh_sec = 1.0
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["time", "PTU300", "PTU8011", "Temperature", "Pressure", "Flow", "pH"])

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def get_turbidity_status(value):
    """Determine water status based on turbidity value"""
    try:
        v = float(value)
    except Exception:
        v = 0.0
    if v < 2:
        return {
            "status": "Jernih",
            "color": "#10b981",
            "icon": "✅",
            "class": "status-clear"
        }
    elif v < 5:
        return {
            "status": "Keruh",
            "color": "#f59e0b",
            "icon": "⚡",
            "class": "status-turbid"
        }
    else:
        return {
            "status": "Sangat Keruh",
            "color": "#ef4444",
            "icon": "⚠️",
            "class": "status-danger"
        }

# -------------------------------
# DYNAMIC STYLING BASED ON THEME
# -------------------------------
def get_theme_colors():
    """Get colors based on current theme"""
    if st.session_state.dark_mode:
        return {
            "bg_primary": "#0a0e27",
            "bg_secondary": "#1a1f3a",
            "bg_card": "linear-gradient(135deg, #1a1f3a, #2d3561)",
            "text_primary": "#ffffff",
            "text_secondary": "#a8b2d1",
            "border": "#2d3561",
            "shadow": "0 8px 32px rgba(0, 0, 0, 0.4)",
            "gauge_bg": "#2d3561",
            "liquid_tank": "#3b82f6",
            "liquid_fill": "#1e40af",
            "chart_bg": "#1a1f3a",
            "chart_grid": "#2d3561",
            "chart_text": "#a8b2d1",
        }
    else:
        return {
            "bg_primary": "#f0f4f8",
            "bg_secondary": "#ffffff",
            "bg_card": "linear-gradient(135deg, #ffffff, #f8fafc)",
            "text_primary": "#1e293b",
            "text_secondary": "#64748b",
            "border": "#e2e8f0",
            "shadow": "0 8px 32px rgba(0, 0, 0, 0.08)",
            "gauge_bg": "#e2e8f0",
            "liquid_tank": "#60a5fa",
            "liquid_fill": "#3b82f6",
            "chart_bg": "#ffffff",
            "chart_grid": "#e2e8f0",
            "chart_text": "#64748b",
        }

colors = get_theme_colors()

# -------------------------------
# APPLY CUSTOM CSS WITH MOBILE RESPONSIVE
# -------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {{
    font-family: 'Inter', sans-serif;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

.stApp {{
    background-color: {colors['bg_primary']} !important;
}}

/* HIDE STREAMLIT BRANDING & WHITE ELEMENTS */
#MainMenu {{visibility: hidden !important;}}
footer {{visibility: hidden !important;}}
.stDeployButton {{display: none !important;}}
header {{visibility: hidden !important;}}
.stAppHeader {{display: none !important;}}
.stAppToolbar {{display: none !important;}}

.stApp > header {{
    background-color: transparent !important;
}}

/* Sidebar Styling */
[data-testid="stSidebar"] {{
    background-color: {colors['bg_secondary']};
    border-right: 2px solid {colors['border']};
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
    color: {colors['text_primary']};
}}

/* Top Navigation Bar - RESPONSIVE */
.top-nav {{
    background: {colors['bg_card']};
    padding: 1rem 1.5rem;
    border-radius: 15px;
    margin-bottom: 1rem;
    box-shadow: {colors['shadow']};
    border: 1px solid {colors['border']};
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}}

.nav-brand {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
    min-width: 200px;
}}

.nav-logo {{
    font-size: 2rem;
    animation: float 3s ease-in-out infinite;
}}

@keyframes float {{
    0%, 100% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-10px); }}
}}

.nav-title {{
    font-size: 1.3rem;
    font-weight: 700;
    color: {colors['text_primary']};
    background: linear-gradient(135deg, #3b82f6, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
}}

.nav-subtitle {{
    font-size: 0.75rem;
    color: {colors['text_secondary']};
    margin-top: 0.15rem;
}}

.status-live {{
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    white-space: nowrap;
}}

.pulse-dot {{
    width: 8px;
    height: 8px;
    background: white;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(1.2); }}
}}

/* SCADA Cards - RESPONSIVE */
.scada-card {{
    background: {colors['bg_card']};
    border-radius: 15px;
    padding: 1rem;
    box-shadow: {colors['shadow']};
    border: 1px solid {colors['border']};
    text-align: center;
    transition: all 0.3s ease;
    height: 100%;
    min-height: 280px;
}}

.scada-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}}

.card-title {{
    font-size: 0.95rem;
    font-weight: 600;
    color: {colors['text_primary']};
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
}}

.card-icon {{
    font-size: 1.2rem;
}}

/* Status Badge */
.status-badge {{
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 15px;
    font-weight: 700;
    font-size: 0.75rem;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}}

.status-clear {{
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
}}

.status-turbid {{
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
}}

.status-danger {{
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
}}

/* Tank Visualization - RESPONSIVE */
.tank-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
}}

.tank {{
    width: 100px;
    height: 140px;
    background: {colors['liquid_tank']};
    border: 4px solid {colors['liquid_fill']};
    border-radius: 10px 10px 18px 18px;
    position: relative;
    overflow: hidden;
    box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.15);
}}

.liquid {{
    position: absolute;
    bottom: 0;
    width: 100%;
    background: linear-gradient(180deg, {colors['liquid_fill']}, #1e3a8a);
    transition: height 0.8s ease;
    animation: wave 3s ease-in-out infinite;
}}

@keyframes wave {{
    0%, 100% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-5px); }}
}}

.tank-label {{
    margin-top: 0.6rem;
    font-weight: 700;
    font-size: 0.9rem;
    color: {colors['text_primary']};
}}

/* Gauge Visualization - RESPONSIVE */
.gauge-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem;
}}

.gauge {{
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: conic-gradient(
        #10b981 0deg,
        #3b82f6 calc(var(--value) * 3.6deg),
        {colors['gauge_bg']} calc(var(--value) * 3.6deg)
    );
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: {colors['shadow']};
    transition: all 0.4s ease;
}}

.gauge::after {{
    content: "";
    position: absolute;
    width: 85px;
    height: 85px;
    border-radius: 50%;
    background: {colors['bg_secondary']};
}}

.gauge-value {{
    position: relative;
    z-index: 2;
    font-size: 1.1rem;
    font-weight: 700;
    color: {colors['text_primary']};
}}

.gauge-label {{
    font-size: 0.8rem;
    color: {colors['text_secondary']};
    font-weight: 600;
}}

/* Mini Gauge - RESPONSIVE */
.mini-gauge {{
    width: 95px;
    height: 95px;
    border-radius: 50%;
    background: conic-gradient(
        var(--color) calc(var(--value) * 3.6deg),
        {colors['gauge_bg']} calc(var(--value) * 3.6deg)
    );
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: {colors['shadow']};
}}

.mini-gauge::after {{
    content: "";
    position: absolute;
    width: 65px;
    height: 65px;
    border-radius: 50%;
    background: {colors['bg_secondary']};
}}

.mini-gauge-value {{
    position: relative;
    z-index: 2;
    font-size: 0.95rem;
    font-weight: 700;
    color: {colors['text_primary']};
}}

/* Progress Bar - RESPONSIVE */
.progress-container {{
    width: 100%;
    height: 20px;
    background: {colors['gauge_bg']};
    border-radius: 10px;
    overflow: hidden;
    margin-top: 0.5rem;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.12);
}}

.progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, #06b6d4, #3b82f6, #8b5cf6);
    transition: width 0.6s ease;
    border-radius: 10px;
    position: relative;
    overflow: hidden;
}}

.progress-fill::after {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.25), transparent);
    animation: shimmer 2s infinite;
}}

@keyframes shimmer {{
    0% {{ transform: translateX(-100%); }}
    100% {{ transform: translateX(100%); }}
}}

/* Chart Container - RESPONSIVE */
.chart-container {{
    background: {colors['bg_card']};
    border-radius: 15px;
    padding: 1rem;
    box-shadow: {colors['shadow']};
    border: 1px solid {colors['border']};
    margin-top: 1rem;
}}

.chart-title {{
    font-size: 1rem;
    font-weight: 700;
    color: {colors['text_primary']};
    margin-bottom: 0.75rem;
    text-align: center;
}}

/* Footer */
.footer {{
    text-align: center;
    padding: 0.75rem;
    margin-top: 1.5rem;
    background: {colors['bg_card']};
    border-radius: 10px;
    box-shadow: {colors['shadow']};
    border: 1px solid {colors['border']};
    color: {colors['text_secondary']};
    font-size: 0.75rem;
}}

/* Refresh Info */
.refresh-info {{
    text-align: center;
    color: {colors['text_secondary']};
    font-size: 0.75rem;
    margin-top: 0.75rem;
    padding: 0.6rem;
    background: {colors['bg_secondary']};
    border-radius: 8px;
    border: 1px solid {colors['border']};
}}

/* Value Display */
.value-display {{
    font-size: 0.75rem;
    color: {colors['text_secondary']};
    margin-top: 0.3rem;
}}

/* Streamlit specific fixes */
.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}}

.row-widget {{
    margin-bottom: 0.75rem !important;
}}

/* ================================
   MOBILE RESPONSIVE BREAKPOINTS
   ================================ */

/* Tablets and smaller (max-width: 768px) */
@media (max-width: 768px) {{
    .top-nav {{
        padding: 0.75rem 1rem;
        border-radius: 12px;
        flex-direction: column;
        text-align: center;
    }}
    
    .nav-brand {{
        justify-content: center;
        min-width: unset;
    }}
    
    .nav-logo {{
        font-size: 1.75rem;
    }}
    
    .nav-title {{
        font-size: 1.1rem;
    }}
    
    .nav-subtitle {{
        font-size: 0.7rem;
    }}
    
    .status-live {{
        padding: 0.4rem 0.85rem;
        font-size: 0.75rem;
    }}
    
    .scada-card {{
        padding: 0.85rem;
        border-radius: 12px;
        min-height: 240px;
    }}
    
    .card-title {{
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }}
    
    .card-icon {{
        font-size: 1rem;
    }}
    
    .tank {{
        width: 85px;
        height: 120px;
        border: 3px solid {colors['liquid_fill']};
    }}
    
    .tank-label {{
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }}
    
    .mini-gauge {{
        width: 80px;
        height: 80px;
    }}
    
    .mini-gauge::after {{
        width: 55px;
        height: 55px;
    }}
    
    .mini-gauge-value {{
        font-size: 0.85rem;
    }}
    
    .gauge-label {{
        font-size: 0.75rem;
    }}
    
    .status-badge {{
        font-size: 0.7rem;
        padding: 0.3rem 0.7rem;
        margin-top: 0.4rem;
    }}
    
    .value-display {{
        font-size: 0.7rem;
    }}
    
    .progress-container {{
        height: 18px;
    }}
    
    .chart-container {{
        padding: 0.85rem;
        border-radius: 12px;
    }}
    
    .chart-title {{
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }}
    
    .refresh-info {{
        font-size: 0.7rem;
        padding: 0.5rem;
    }}
    
    .footer {{
        font-size: 0.7rem;
        padding: 0.6rem;
    }}
    
    .block-container {{
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }}
}}

/* Mobile phones (max-width: 480px) */
@media (max-width: 480px) {{
    .top-nav {{
        padding: 0.6rem 0.75rem;
        border-radius: 10px;
        margin-bottom: 0.75rem;
    }}
    
    .nav-logo {{
        font-size: 1.5rem;
    }}
    
    .nav-title {{
        font-size: 0.95rem;
    }}
    
    .nav-subtitle {{
        font-size: 0.65rem;
    }}
    
    .status-live {{
        padding: 0.35rem 0.7rem;
        font-size: 0.7rem;
    }}
    
    .pulse-dot {{
        width: 6px;
        height: 6px;
    }}
    
    .scada-card {{
        padding: 0.75rem;
        border-radius: 10px;
        min-height: 220px;
    }}
    
    .card-title {{
        font-size: 0.8rem;
        margin-bottom: 0.4rem;
        gap: 0.3rem;
    }}
    
    .card-icon {{
        font-size: 0.9rem;
    }}
    
    .tank {{
        width: 70px;
        height: 100px;
        border: 3px solid {colors['liquid_fill']};
        border-radius: 8px 8px 15px 15px;
    }}
    
    .tank-label {{
        font-size: 0.75rem;
        margin-top: 0.4rem;
    }}
    
    .mini-gauge {{
        width: 70px;
        height: 70px;
    }}
    
    .mini-gauge::after {{
        width: 48px;
        height: 48px;
    }}
    
    .mini-gauge-value {{
        font-size: 0.75rem;
    }}
    
    .gauge-label {{
        font-size: 0.7rem;
        margin-top: 0.3rem;
    }}
    
    .status-badge {{
        font-size: 0.65rem;
        padding: 0.25rem 0.6rem;
        margin-top: 0.35rem;
        border-radius: 12px;
    }}
    
    .value-display {{
        font-size: 0.65rem;
        margin-top: 0.25rem;
    }}
    
    .progress-container {{
        height: 16px;
        margin-top: 0.4rem;
    }}
    
    .chart-container {{
        padding: 0.75rem;
        border-radius: 10px;
        margin-top: 0.75rem;
    }}
    
    .chart-title {{
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
    }}
    
    .refresh-info {{
        font-size: 0.65rem;
        padding: 0.45rem;
        margin-top: 0.5rem;
        border-radius: 6px;
    }}
    
    .footer {{
        font-size: 0.65rem;
        padding: 0.5rem;
        margin-top: 1rem;
        border-radius: 8px;
    }}
    
    .block-container {{
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-top: 0.75rem !important;
        padding-bottom: 0.75rem !important;
    }}
}}

/* Extra small devices (max-width: 360px) */
@media (max-width: 360px) {{
    .nav-title {{
        font-size: 0.85rem;
    }}
    
    .nav-subtitle {{
        font-size: 0.6rem;
    }}
    
    .card-title {{
        font-size: 0.75rem;
    }}
    
    .mini-gauge {{
        width: 65px;
        height: 65px;
    }}
    
    .mini-gauge::after {{
        width: 45px;
        height: 45px;
    }}
    
    .mini-gauge-value {{
        font-size: 0.7rem;
    }}
    
    .tank {{
        width: 60px;
        height: 90px;
    }}
}}

/* Landscape mode adjustments for mobile */
@media (max-height: 500px) and (orientation: landscape) {{
    .scada-card {{
        min-height: 180px;
    }}
    
    .mini-gauge {{
        width: 65px;
        height: 65px;
    }}
    
    .mini-gauge::after {{
        width: 45px;
        height: 45px;
    }}
    
    .tank {{
        width: 60px;
        height: 85px;
    }}
}}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# DATA FETCHING FUNCTION
# -------------------------------
def read_esp32_data(url: str):
    """Fetch data from ESP32"""
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            return {
                "ptu300": float(data.get("PTU300_ID7_NTU", 0.0)),
                "ptu8011": float(data.get("PTU8011_ID8_NTU", 0.0)),
                "flow": float(data.get("Flow_Lmin", 0.0)),
                "ph": float(data.get("pH_Value", 7.0)),
                "temperature": float(data.get("Temperature_C", 25.0)),
                "pressure": float(data.get("Pressure_Bar", 1.0)),
            }
    except Exception:
        pass
    return {"ptu300": 0.0, "ptu8011": 0.0, "flow": 0.0, "ph": 7.0, "temperature": 25.0, "pressure": 1.0}

# -------------------------------
# SIDEBAR
# -------------------------------
with st.sidebar:
    st.markdown("# ⚙️ Settings")
    st.markdown("---")

    st.markdown("### 🔄 Auto-Refresh")
    st.session_state.refresh_sec = st.selectbox(
        "Refresh Interval",
        [0.5, 1, 2, 5, 10],
        index=[0.5, 1, 2, 5, 10].index(st.session_state.refresh_sec)
        if st.session_state.refresh_sec in [0.5, 1, 2, 5, 10]
        else 1,
    )

    st.session_state.auto_refresh = st.checkbox(
        "Enable auto-refresh",
        value=st.session_state.auto_refresh
    )

    st.markdown("---")

    st.markdown("### 🎨 Theme Mode")
    theme_col1, theme_col2 = st.columns(2)
    with theme_col1:
        if st.button("🌙 Dark", use_container_width=True, type="primary" if st.session_state.dark_mode else "secondary"):
            st.session_state.dark_mode = True
            st.rerun()
    with theme_col2:
        if st.button("☀️ Light", use_container_width=True, type="primary" if not st.session_state.dark_mode else "secondary"):
            st.session_state.dark_mode = False
            st.rerun()

    st.markdown("---")

    st.markdown("### 📊 Live Statistics")
    if len(st.session_state.history) > 0:
        st.metric("📈 Data Points", len(st.session_state.history))

        avg_ptu300 = st.session_state.history['PTU300'].astype(float).mean()
        st.metric("💧 Avg PTU-300", f"{avg_ptu300:.2f} NTU")

        avg_ptu8011 = st.session_state.history['PTU8011'].astype(float).mean()
        st.metric("💧 Avg PTU-8011", f"{avg_ptu8011:.2f} NTU")

        avg_temp = st.session_state.history['Temperature'].astype(float).mean()
        st.metric("🌡️ Avg Temperature", f"{avg_temp:.2f} °C")

        avg_pressure = st.session_state.history['Pressure'].astype(float).mean()
        st.metric("⚙️ Avg Pressure", f"{avg_pressure:.2f} Bar")

        if 'Flow' in st.session_state.history.columns:
            avg_flow = st.session_state.history['Flow'].astype(float).mean()
            st.metric("💨 Avg Flow", f"{avg_flow:.2f} L/min")
        if 'pH' in st.session_state.history.columns:
            avg_ph = st.session_state.history['pH'].astype(float).mean()
            st.metric("⚗️ Avg pH", f"{avg_ph:.2f}")

        st.markdown("---")

        max_ptu300 = st.session_state.history['PTU300'].astype(float).max()
        st.metric("🔺 Max PTU-300", f"{max_ptu300:.2f} NTU")

        max_temp = st.session_state.history['Temperature'].astype(float).max()
        st.metric("🔥 Max Temperature", f"{max_temp:.2f} °C")

    else:
        st.info("📊 No data available yet...")

    st.markdown("---")

    st.markdown("### 📖 Turbidity Guide")
    st.markdown("""
    **Status Levels (NTU):**
    - ✅ **Jernih**: < 2 
    - ⚡ **Keruh**: 2-5 
    - ⚠️ **Sangat Keruh**: > 5
    """)

# -------------------------------
# TOP NAVIGATION BAR
# -------------------------------
st.markdown(f"""
<div class="top-nav">
    <div class="nav-brand">
        <div class="nav-logo">🌊</div>
        <div>
            <div class="nav-title">SCADA SYSTEM TIRTAWENING</div>
            <div class="nav-subtitle">Real-time Water Quality Monitoring</div>
        </div>
    </div>
    <div class="status-live">
        <div class="pulse-dot"></div>
        LIVE
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# MAIN CONTENT - AUTO REFRESH LOOP
# -------------------------------
placeholder = st.empty()

while True:
    with placeholder.container():
        # Fetch data
        data = read_esp32_data(DATA_URL)
        ptu300 = data.get("ptu300", 0.0)
        ptu8011 = data.get("ptu8011", 0.0)
        flow_rate = data.get("flow", 0.0)
        ph_value = data.get("ph", 7.0)
        temperature = data.get("temperature", 25.0)
        pressure = data.get("pressure", 1.0)

        # Get status for turbidity sensors
        ptu300_status = get_turbidity_status(ptu300)
        ptu8011_status = get_turbidity_status(ptu8011)

        # Update history
        new_row = pd.DataFrame({
            "time": [datetime.now().strftime("%H:%M:%S")],
            "PTU300": [ptu300],
            "PTU8011": [ptu8011],
            "Temperature": [temperature],
            "Pressure": [pressure],
            "Flow": [flow_rate],
            "pH": [ph_value]
        })
        st.session_state.history = pd.concat(
            [st.session_state.history, new_row],
            ignore_index=True
        )

        # Keep only last 100 records
        if len(st.session_state.history) > 100:
            st.session_state.history = st.session_state.history.iloc[-100:]

        # Calculate tank level based on turbidity difference
        try:
            tank_level = 50 + (float(ptu300) - float(ptu8011)) * 5
        except Exception:
            tank_level = 50
        tank_level = max(10, min(90, tank_level))

        # -------------------------------
        # ROW 1: MAIN SCADA WIDGETS
        # -------------------------------
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small")

        with col1:
            st.markdown(f"""
            <div class="scada-card">
                <div class="card-title">
                    <span class="card-icon">💧</span>
                    Input Tank
                </div>
                <div class="tank-container">
                    <div class="tank">
                        <div class="liquid" style="height:{tank_level}%"></div>
                    </div>
                    <div class="tank-label">{tank_level:.1f}%</div>
                    <div class="value-display">Water Level</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            ptu300_percent = min(ptu300 * 10, 100)
            st.markdown(f"""
            <div class="scada-card">
                <div class="card-title">
                    <span class="card-icon">🧪</span>
                    PTU-300
                </div>
                <div class="gauge-container">
                    <div>
                        <div class="mini-gauge" style="--value:{ptu300_percent}; --color:{ptu300_status['color']};">
                            <div class="mini-gauge-value">{ptu300:.2f}</div>
                        </div>
                        <div class="gauge-label" style="margin-top:0.4rem;">NTU</div>
                        <div class="status-badge {ptu300_status['class']}">
                            {ptu300_status['icon']} {ptu300_status['status']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            ptu8011_percent = min(ptu8011 * 10, 100)
            st.markdown(f"""
            <div class="scada-card">
                <div class="card-title">
                    <span class="card-icon">🧪</span>
                    PTU-8011
                </div>
                <div class="gauge-container">
                    <div>
                        <div class="mini-gauge" style="--value:{ptu8011_percent}; --color:{ptu8011_status['color']};">
                            <div class="mini-gauge-value">{ptu8011:.2f}</div>
                        </div>
                        <div class="gauge-label" style="margin-top:0.4rem;">NTU</div>
                        <div class="status-badge {ptu8011_status['class']}">
                            {ptu8011_status['icon']} {ptu8011_status['status']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            try:
                flow_percent = min((float(flow_rate) / 20.0) * 100.0, 100.0)
            except Exception:
                flow_rate = 0.0
                flow_percent = 0.0

            try:
                fval = float(flow_rate)
            except Exception:
                fval = 0.0
            if fval <= 0:
                flow_status = {"status": "No Flow", "class": "status-danger", "icon": "⛔", "color": "#ef4444"}
            elif fval < 1:
                flow_status = {"status": "Low", "class": "status-turbid", "icon": "⚠️", "color": "#f59e0b"}
            elif fval <= 15:
                flow_status = {"status": "Normal", "class": "status-clear", "icon": "✅", "color": "#10b981"}
            else:
                flow_status = {"status": "High", "class": "status-turbid", "icon": "⚡", "color": "#f59e0b"}

            st.markdown(f"""
            <div class="scada-card">
                <div class="card-title">
                    <span class="card-icon">💨</span>
                    Flow Meter
                </div>
                <div class="gauge-container">
                    <div class="mini-gauge" style="--value:{flow_percent}; --color:{flow_status['color']};">
                        <div class="mini-gauge-value">{flow_rate:.2f}</div>
                    </div>
                    <div class="gauge-label" style="margin-top:0.4rem;">L/min</div>
                    <div class="progress-container" style="margin-top:0.5rem;">
                        <div class="progress-fill" style="width:{flow_percent}%;"></div>
                    </div>
                    <div class="status-badge {flow_status['class']}" style="margin-top:0.5rem;">
                        {flow_status['icon']} {flow_status['status']}
                    </div>
                    <div class="value-display" style="margin-top:0.3rem;">
                        {flow_percent:.1f}%
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # -------------------------------
        # ROW 2: Temperature & Pressure & pH
        # -------------------------------
        col_t, col_p, col_ph = st.columns([1, 1, 1], gap="small")

        with col_t:
            try:
                temp_percent = min((float(temperature) / 50.0) * 100.0, 100.0)
            except Exception:
                temperature = 0.0
                temp_percent = 0.0
            temp_color = "#3b82f6" if 20 <= float(temperature) <= 30 else "#f59e0b" if 15 <= float(temperature) <= 35 else "#ef4444"
            temp_status = "Normal" if 20 <= float(temperature) <= 30 else "Warning" if 15 <= float(temperature) <= 35 else "Danger"
            temp_class = "status-clear" if temp_status == "Normal" else "status-turbid" if temp_status == "Warning" else "status-danger"

            st.markdown(f"""
            <div class="scada-card">
                <div class="card-title">
                    <span class="card-icon">🌡️</span>
                    Temperature
                </div>
                <div class="gauge-container">
                    <div class="mini-gauge" style="--value:{temp_percent}; --color:{temp_color};">
                        <div class="mini-gauge-value">{temperature:.1f}</div>
                    </div>
                    <div class="gauge-label" style="margin-top:0.4rem;">°C</div>
                    <div class="status-badge {temp_class}">
                        {temp_status}
                    </div>
                    <div class="value-display">20-30 °C</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_p:
            try:
                pressure_percent = min((float(pressure) / 5.0) * 100.0, 100.0)
            except Exception:
                pressure = 0.0
                pressure_percent = 0.0
            pressure_color = "#10b981" if 1.0 <= float(pressure) <= 2.0 else "#f59e0b" if 0.5 <= float(pressure) <= 3.0 else "#ef4444"
            pressure_status = "Normal" if 1.0 <= float(pressure) <= 2.0 else "Warning" if 0.5 <= float(pressure) <= 3.0 else "Danger"
            pressure_class = "status-clear" if pressure_status == "Normal" else "status-turbid" if pressure_status == "Warning" else "status-danger"

            st.markdown(f"""
            <div class="scada-card">
                <div class="card-title">
                    <span class="card-icon">⚙️</span>
                    Pressure
                </div>
                <div class="gauge-container">
                    <div class="mini-gauge" style="--value:{pressure_percent}; --color:{pressure_color};">
                        <div class="mini-gauge-value">{pressure:.2f}</div>
                    </div>
                    <div class="gauge-label" style="margin-top:0.4rem;">Bar</div>
                    <div class="status-badge {pressure_class}">
                        {pressure_status}
                    </div>
                    <div class="value-display">1.0-2.0 Bar</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_ph:
            try:
                ph_percent = min((float(ph_value) / 14.0) * 100.0, 100.0)
            except Exception:
                ph_value = 0.0
                ph_percent = 0.0
            ph_color = "#10b981" if 6.5 <= float(ph_value) <= 8.5 else "#f59e0b" if 5 <= float(ph_value) <= 9 else "#ef4444"
            ph_status = "Normal" if 6.5 <= float(ph_value) <= 8.5 else "Warning" if 5 <= float(ph_value) <= 9 else "Danger"
            ph_class = "status-clear" if ph_status == "Normal" else "status-turbid" if ph_status == "Warning" else "status-danger"

            st.markdown(f"""
            <div class="scada-card">
                <div class="card-title">
                    <span class="card-icon">🧫</span>
                    pH Sensor
                </div>
                <div class="gauge-container">
                    <div class="mini-gauge" style="--value:{ph_percent}; --color:{ph_color};">
                        <div class="mini-gauge-value">{ph_value:.2f}</div>
                    </div>
                    <div class="gauge-label" style="margin-top:0.4rem;">pH</div>
                    <div class="status-badge {ph_class}">
                        {ph_status}
                    </div>
                    <div class="value-display">6.5-8.5</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # -------------------------------
        # ROW 3: TREND CHART WITH PLOTLY
        # -------------------------------
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">📈 Trend Analysis</div>', unsafe_allow_html=True)

        if len(st.session_state.history) > 0:
            # Create Plotly chart with theme
            fig = go.Figure()

            # Add traces for each parameter
            fig.add_trace(go.Scatter(
                x=st.session_state.history['time'],
                y=st.session_state.history['PTU300'],
                mode='lines+markers',
                name='PTU-300',
                line=dict(color='#3b82f6', width=2),
                marker=dict(size=3)
            ))

            fig.add_trace(go.Scatter(
                x=st.session_state.history['time'],
                y=st.session_state.history['PTU8011'],
                mode='lines+markers',
                name='PTU-8011',
                line=dict(color='#10b981', width=2),
                marker=dict(size=3)
            ))

            fig.add_trace(go.Scatter(
                x=st.session_state.history['time'],
                y=st.session_state.history['Temperature'],
                mode='lines+markers',
                name='Temp',
                line=dict(color='#f59e0b', width=2),
                marker=dict(size=3)
            ))

            fig.add_trace(go.Scatter(
                x=st.session_state.history['time'],
                y=st.session_state.history['Flow'],
                mode='lines+markers',
                name='Flow',
                line=dict(color='#8b5cf6', width=2),
                marker=dict(size=3)
            ))

            fig.add_trace(go.Scatter(
                x=st.session_state.history['time'],
                y=st.session_state.history['pH'],
                mode='lines+markers',
                name='pH',
                line=dict(color='#ec4899', width=2),
                marker=dict(size=3)
            ))

            # Update layout based on theme
            fig.update_layout(
                height=300,
                plot_bgcolor=colors['chart_bg'],
                paper_bgcolor=colors['chart_bg'],
                font=dict(
                    color=colors['chart_text'],
                    size=10
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor=colors['chart_grid'],
                    gridwidth=1,
                    zeroline=False,
                    color=colors['chart_text']
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=colors['chart_grid'],
                    gridwidth=1,
                    zeroline=False,
                    color=colors['chart_text']
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(color=colors['chart_text'], size=9)
                ),
                margin=dict(l=35, r=15, t=35, b=35),
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Waiting for data...")

        st.markdown('</div>', unsafe_allow_html=True)

        # Refresh info
        st.markdown(f"""
        <div class="refresh-info">
            🔄 Auto-refresh: {'✅ On' if st.session_state.auto_refresh else '❌ Off'} 
            | ⏱️ {st.session_state.refresh_sec}s 
            | 🕐 {datetime.now().strftime("%H:%M:%S")}
        </div>
        """, unsafe_allow_html=True)

    # Delay based on refresh interval
    if st.session_state.auto_refresh:
        time.sleep(st.session_state.refresh_sec)
    else:
        break

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("""
<div class="footer">
    © 2025 STI PERUMDA TIRTAWENING
    <br>
    <small>🌊 Turbidity Monitoring System v2.0</small>
</div>
""", unsafe_allow_html=True)
