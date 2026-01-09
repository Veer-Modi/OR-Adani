
import streamlit as st

def apply_custom_css():
    """Apply custom CSS for Professional Compact Theme (Dark Mode)."""
    st.markdown("""
        <style>
        /* Import Modern Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Reset */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #121212;
            color: #E0E0E0;
            font-size: 0.9rem; /* Slightly smaller base font */
        }
        
        /* Compact Headers */
        h1 { font-size: 1.8rem !important; margin-bottom: 1rem !important; }
        h2 { font-size: 1.4rem !important; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.2rem; margin-top: 1.5rem; }
        h3 { font-size: 1.1rem !important; color: #00ADB5; margin-bottom: 0.5rem !important; }
        
        /* GLASSMORPHISM CARDS (Compact) */
        div.css-1r6slb0, div.stDataFrame, div.stPlotlyChart {
            background: rgba(30, 30, 30, 0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 4px; /* Sharper corners */
            padding: 1rem; /* Reduced padding */
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
        }
        
        .industrial-card {
            background: rgba(30, 30, 30, 0.6);
            backdrop-filter: blur(12px);
            border-radius: 4px;
            padding: 1.2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.37);
            margin-bottom: 1rem;
        }
        
        /* COMPACT INPUTS & WIDGETS */
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stTextInput input, 
        .stNumberInput input {
            min-height: 38px !important;
            height: 38px !important;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            border-radius: 2px !important; /* Sharp technical look */
            border-color: rgba(255,255,255,0.2) !important;
            background-color: #1E1E1E !important;
            color: white !important;
            font-size: 0.85rem !important;
        }
        
        .stSelectbox label, .stNumberInput label, .stTextInput label, .stMultiSelect label {
            font-size: 0.8rem !important;
            color: #A0A0A0 !important;
            margin-bottom: 0.2rem !important;
        }

        /* Focus states */
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #00ADB5 !important;
            box-shadow: none !important;
        }
        
        /* BUTTONS (Compact) */
        button[kind="primary"] {
            background: linear-gradient(90deg, #00ADB5 0%, #008C94 100%) !important;
            border-radius: 4px !important;
            padding: 0.4rem 1.5rem !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            margin-top: 1rem;
        }
        
        button[kind="secondary"] {
            border-radius: 4px !important;
            padding: 0.4rem 1rem !important;
            font-size: 0.85rem !important;
        }
        
        /* TABLES (Compact) */
        table {
            font-size: 0.8rem !important;
        }
        thead tr th {
            background-color: #1E1E1E !important;
            color: #00ADB5 !important;
            border-bottom: 1px solid #00ADB5 !important;
            font-size: 0.8rem !important;
            padding: 0.5rem !important;
        }
        tbody tr td {
            padding: 0.4rem !important;
        }
        
        /* KPI Cards Compact */
        .kpi-card {
            background: linear-gradient(145deg, rgba(30,30,30,0.9), rgba(20,20,20,0.9));
            border-radius: 4px;
            padding: 1rem;
            border: 1px solid rgba(0, 173, 181, 0.2);
            position: relative;
        }
        .kpi-title { font-size: 0.75rem; color: #A0A0A0; text-transform: uppercase; margin-bottom: 0.2rem; }
        .kpi-value { font-size: 1.5rem; font-weight: 700; color: #fff; }
        .kpi-trend { font-size: 0.75rem; margin-top: 0.3rem; }

        </style>
    """, unsafe_allow_html=True)
