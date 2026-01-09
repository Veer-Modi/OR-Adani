
import streamlit as st
import plotly.graph_objects as go

def render_home_overview():
    """Render the Home/Overview page with Premium Control Tower styling."""
    
    st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
    st.title("Network Control Tower")
    st.markdown("""
    <div style="color: #A0A0A0; margin-top: -1.5rem; margin-bottom: 1rem;">
    Real-time optimization and strategic planning for Clinker Supply Chain.
    </div>
    """, unsafe_allow_html=True)
    
    # Workflow Status Bar (Mockup)
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem; margin-bottom: 2rem;">
        <div>
            <span style="color: #00ADB5; font-weight: 600;">SYSTEM STATUS</span>
            <span style="margin-left: 10px; color: #4CAF50;">● ONLINE</span>
        </div>
        <div>
            <span style="color: #A0A0A0;">Last Optimization:</span>
            <span style="color: white; font-weight: 600; margin-left: 5px;">24 mins ago</span>
        </div>
        <div>
            <span style="color: #A0A0A0;">Active Scenario:</span>
            <span style="color: #F4A261; font-weight: 600; margin-left: 5px;">Base Case 2024</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Premium KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Network Efficiency</div>
            <div class="kpi-value">94.2%</div>
            <div class="kpi-trend" style="color: #4CAF50;">
                <span>▲</span> 2.1% vs Last Month
            </div>
            <div style="position: absolute; right: 10px; top: 10px; opacity: 0.2;">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="white"><path d="M12 2L2 7l10 5 10-5-10-5zm0 9l2.5-1.25L12 8.75 9.5 9.75 12 11zm0 2.5l-5-2.5-5 2.5L12 22l10-8.5-5-2.5-5 2.5z"/></svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Total Spend</div>
            <div class="kpi-value">$4.2M</div>
            <div class="kpi-trend" style="color: #F44336;">
                <span>▼</span> $120k vs Budget
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Active Routes</div>
            <div class="kpi-value">128</div>
            <div class="kpi-trend" style="color: #00ADB5;">
                <span>●</span> 12 Critical
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
        <div class="kpi-card" style="border-color: #F4A261; box-shadow: 0 0 10px rgba(244, 162, 97, 0.1);">
            <div class="kpi-title" style="color: #F4A261;">Avg Inventory</div>
            <div class="kpi-value" style="text-shadow: 0 0 10px rgba(244, 162, 97, 0.5);">320k</div>
            <div class="kpi-trend" style="color: #A0A0A0;">
                Target: 300k
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Mini Chart Section
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown('<div class="industrial-card"><h3>Cost Trend (6 Months)</h3>', unsafe_allow_html=True)
        # Mock Data for illustration
        fig = go.Figure(data=[go.Scatter(
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            y=[4.5, 4.3, 4.8, 4.2, 4.1, 4.2],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#00ADB5', width=3),
            marker=dict(size=8, color='#00FFF5')
        )])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            height=250,
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Million $"),
            xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chart2:
        st.markdown('<div class="industrial-card"><h3>Mode Utilization</h3>', unsafe_allow_html=True)
        fig2 = go.Figure(data=[go.Pie(
            labels=['Rail', 'Road', 'Sea'],
            values=[65, 25, 10],
            hole=.6,
            marker=dict(colors=['#00ADB5', '#393E46', '#F4A261'])
        )])
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            height=250,
            showlegend=True
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
