
import streamlit as st

from backend.auth.auth_service import signup

def render_signup_page() -> None:
    """Show signup page with split layout."""
    
    col_left, col_right = st.columns([1, 1.2], gap="large")
    
    with col_left:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## Sign Up")
        st.caption("Secure Your Communications with Easymail (Demo)")
        
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
        
        with st.form("signup_form"):
            name = st.text_input("Name", placeholder="Daniel Ahmadi")
            email = st.text_input("Email", placeholder="daniel@gmail.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            role = st.selectbox("Role", ["Admin", "Planner", "Viewer"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
            
        if submitted:
            success, message = signup(name=name, email=email, password=password, role=role)
            if success:
                st.success(message)
                st.info("Account created! Please login.")
            else:
                st.error(message)

    with col_right:
        # Right side graphical element (Abstract Floating Cards)
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #4A90E2 0%, #0056b3 100%);
            border-radius: 20px;
            padding: 3rem;
            color: white;
            height: 600px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(74, 144, 226, 0.3);
        ">
            <!-- Floating Card 1 -->
            <div style="
                position: absolute; top: 10%; right: 10%;
                background: white; color: #333;
                padding: 1.5rem; border-radius: 15px;
                width: 180px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            ">
                <div style="font-size: 0.8rem; color: #888;">Inbox</div>
                <div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem;">176,18</div>
                <!-- Sparkline Mock -->
                <div style="height: 4px; background: #eee; width: 100%; border-radius: 2px;">
                    <div style="height: 100%; width: 70%; background: #FFA500; border-radius: 2px;"></div>
                </div>
            </div>
            
            <!-- Floating Card 2 -->
            <div style="
                position: absolute; bottom: 15%; left: 10%;
                background: white; color: #333;
                padding: 1.5rem; border-radius: 15px;
                width: 260px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            ">
                <div style="font-weight: bold; margin-bottom: 0.5rem;">Your data, your rules</div>
                <div style="font-size: 0.8rem; color: #888; line-height: 1.5;">
                    Your data belongs to you, and our encryption ensures that.
                </div>
            </div>
            
        </div>
        """, unsafe_allow_html=True)
