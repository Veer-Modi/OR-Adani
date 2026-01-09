
import streamlit as st

from backend.auth.auth_service import login
from backend.auth.session import ensure_session_defaults, login_user
from backend.core.logger import audit_log

def render_login_page() -> None:
    """Show login page with split layout."""
    ensure_session_defaults()
    
    # 2-Column Split Layout
    col_left, col_right = st.columns([1, 1.2], gap="large")
    
    with col_left:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## Sign In")
        st.caption("Secure, AI-driven Supply Chain Optimization")
        
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="admin@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
        
        if submitted:
            success, message, user = login(email=email, password=password)
            if not success:
                st.error(message)
                return
            login_user(user)
            st.rerun()

    with col_right:
        # Right side graphical element (Abstract Blue Card)
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #00ADB5 0%, #007A80 100%);
            border-radius: 20px;
            padding: 3rem;
            color: white;
            height: 500px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0, 173, 181, 0.3);
        ">
            <!-- Decorative Circles -->
            <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
            <div style="position: absolute; bottom: 50px; left: -50px; width: 150px; height: 150px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
            
            <h2 style="color: white !important; border: none; text-align: center;">Welcome Back!</h2>
            <p style="text-align: center; opacity: 0.9;">
                Orchestrate your cement logistics with precision.
            </p>
            
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(10px);
                padding: 1.5rem;
                border-radius: 12px;
                margin-top: 2rem;
                width: 80%;
                text-align: center;
            ">
                <div style="font-size: 0.8rem; opacity: 0.8;">System Status</div>
                <div style="font-size: 1.2rem; font-weight: bold;">Online & Optimized</div>
            </div>
            
        </div>
        """, unsafe_allow_html=True)
