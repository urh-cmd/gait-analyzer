"""
Haile - Tailwind UI
==================
Shared components: logo, sidebar, Tailwind-based design.
"""

# Plotly dark theme (ohne title – wird pro Chart gesetzt)
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", size=12, family="Inter, sans-serif"),
    xaxis=dict(gridcolor="rgba(148,163,184,0.1)", zerolinecolor="rgba(148,163,184,0.15)"),
    yaxis=dict(gridcolor="rgba(148,163,184,0.1)", zerolinecolor="rgba(148,163,184,0.15)"),
    margin=dict(l=50, r=30, t=40, b=40),
)

import streamlit as st

LOGO_SVG = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="28" height="28" fill="none">
  <rect width="32" height="32" rx="8" fill="url(#logo-grad)"/>
  <path d="M8 22L12 10L16 18L20 6L24 22" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <defs>
    <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
      <stop stop-color="#0284c7"/>
      <stop offset="1" stop-color="#0ea5e9"/>
    </linearGradient>
  </defs>
</svg>
'''

# Links separat – ohne script, da DOMPurify script entfernt und Block zerstören kann
TAILWIND_LINKS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'

# Nur style-Block – getrennt injizieren
BRIDGE_CSS = """
html { font-size: 16px; font-family: 'Inter', system-ui, sans-serif; }
.stApp, [data-testid="stAppViewContainer"] { background: #0f172a !important; }
.block-container { max-width: 1200px !important; padding: 2rem 1.5rem 3rem !important; overflow-x: hidden !important; }
h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; font-weight: 600 !important; letter-spacing: -0.025em !important; color: #f8fafc !important; }
h1 { font-size: 1.875rem !important; } h2 { font-size: 1.25rem !important; } h3 { font-size: 1.125rem !important; color: #94a3b8 !important; }
h4 { font-size: 1rem !important; color: #94a3b8 !important; }
[data-testid="stHorizontalBlock"] > div, [data-testid="column"], [class*="stHorizontalBlock"] > div { border: none !important; border-left: none !important; border-right: none !important; box-shadow: none !important; outline: none !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important; border-right: 1px solid #334155 !important; }
[data-testid="stSidebar"] .stMarkdown { color: #94a3b8 !important; }
[data-testid="stSidebar"] a { color: #94a3b8 !important; }
[data-testid="stSidebar"] a:hover { color: #38bdf8 !important; }
.stButton > button { font-family: 'Inter', sans-serif !important; font-weight: 500 !important; border-radius: 0.5rem !important; transition: all 0.2s ease !important; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #0284C7 0%, #0EA5E9 100%) !important; border: none !important; color: #ffffff !important; box-shadow: 0 1px 2px rgba(14, 165, 233, 0.3) !important; }
.stButton > button[kind="primary"]:hover { box-shadow: 0 4px 16px rgba(14, 165, 233, 0.4) !important; transform: translateY(-1px) !important; }
.stButton > button:not([kind="primary"]) { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid #334155 !important; color: #94a3b8 !important; }
.stButton > button:not([kind="primary"]):hover { background: rgba(51, 65, 85, 0.8) !important; border-color: #475569 !important; color: #e2e8f0 !important; }
[data-testid="stExpander"], .stAlert { border-radius: 0.75rem !important; border: 1px solid #334155 !important; background: rgba(30, 41, 59, 0.5) !important; }
[data-testid="stMetric"] { background: rgba(30, 41, 59, 0.5) !important; padding: 1rem 1.25rem !important; border-radius: 0.75rem !important; border: 1px solid #334155 !important; box-shadow: none !important; }
[data-testid="stMetric"] label { color: #94a3b8 !important; font-size: 0.75rem !important; font-weight: 500 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 1.5rem !important; font-weight: 600 !important; }
hr { border: none !important; border-top: 1px solid #334155 !important; margin: 1.5rem 0 !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid #334155 !important; border-radius: 0.5rem !important; color: #f8fafc !important; }
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem !important; }
.stTabs [data-baseweb="tab"] { font-weight: 500 !important; border-radius: 0.5rem !important; }
.stTabs [aria-selected="true"] { background: rgba(14, 165, 233, 0.15) !important; color: #0EA5E9 !important; }
.stAlert { border-radius: 0.75rem !important; }
[data-testid="stFileUploader"] { border: 2px dashed #475569 !important; border-radius: 0.75rem !important; background: rgba(30, 41, 59, 0.3) !important; }
[data-testid="stFileUploader"]:hover { border-color: #0ea5e9 !important; }
.stProgress > div > div { background: linear-gradient(90deg, #0284C7 0%, #0EA5E9 100%) !important; }
.section-card { background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin: 1rem 0; }
"""


def render_linear_css():
    """Links und CSS getrennt injizieren – umgeht DOMPurify/Sanitizer-Probleme."""
    st.markdown(TAILWIND_LINKS, unsafe_allow_html=True)
    st.markdown(f"<style>{BRIDGE_CSS}</style>", unsafe_allow_html=True)


def render_logo_header(size=28):
    """Logo + Haile text mit Tailwind."""
    svg = LOGO_SVG.replace('width="28" height="28"', f'width="{size}" height="{size}"')
    st.markdown(
        f'<div class="flex items-center gap-2.5 mb-6">'
        f'{svg}'
        f'<span class="text-xl font-bold text-sky-400">Haile</span>'
        f'</div>',
        unsafe_allow_html=True
    )


