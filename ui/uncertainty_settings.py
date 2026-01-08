"""Demand Uncertainty Settings page.

This UI provides configuration for demand uncertainty analysis:
- Configure number of scenarios and volatility
- Set demand multipliers and probabilities
- Preview scenarios before running analysis

Business interpretation:
- Demand multiplier 0.9 means "10% lower than base demand"
- Demand multiplier 1.1 means "10% higher than base demand"
- Volatility controls how much demand can vary

Role access:
- Admin & Planner: can edit and save
- Viewer: view only
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
import pandas as pd

from backend.middleware.role_guard import require_authentication, require_role


def render_uncertainty_settings(role: str) -> None:
    if not require_authentication():
        return

    st.header("Demand Uncertainty Settings")
    st.caption("Configure demand scenarios and volatility for uncertainty analysis.")

    if not require_role(["Admin", "Planner", "Viewer"]):
        return

    can_edit = role in {"Admin", "Planner"}

    # Initialize session state for settings
    if 'uncertainty_settings' not in st.session_state:
        st.session_state.uncertainty_settings = {
            'is_enabled': True,
            'num_scenarios': 5,
            'volatility': 0.3,
            'scenarios': []
        }

    settings = st.session_state.uncertainty_settings

    # Enable/disable uncertainty analysis
    is_enabled = st.checkbox(
        "Enable demand uncertainty analysis",
        value=bool(settings.get("is_enabled", True)),
        disabled=not can_edit,
        help="If disabled, optimization runs use deterministic (known) demand.",
    )

    if is_enabled:
        st.subheader("Scenario Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_scenarios = st.slider(
                "Number of scenarios",
                min_value=3,
                max_value=10,
                value=int(settings.get("num_scenarios", 5)),
                step=1,
                disabled=not can_edit,
                help="More scenarios provide better uncertainty coverage but increase computation time."
            )
        
        with col2:
            volatility = st.slider(
                "Demand volatility",
                min_value=0.1,
                max_value=0.5,
                value=float(settings.get("volatility", 0.3)),
                step=0.05,
                disabled=not can_edit,
                help="Controls how much demand can vary across scenarios (10% = stable, 50% = highly variable)."
            )

        # Generate preview scenarios
        if st.button(" Preview Scenarios", disabled=not can_edit):
            with st.spinner("Generating scenario preview..."):
                scenarios = generate_scenario_preview(num_scenarios, volatility)
                settings['scenarios'] = scenarios
                st.session_state.uncertainty_settings = settings

        # Display scenarios
        if settings.get('scenarios'):
            st.subheader(" Scenario Preview")
            
            scenario_data = []
            for i, s in enumerate(settings['scenarios']):
                scenario_data.append({
                    'Scenario': s['name'],
                    'Probability': f"{s['probability']:.2%}",
                    'Demand Multiplier': f"{s['demand_multiplier']:.2f}x",
                    'Expected Demand': f"{s.get('expected_demand', 'N/A')}"
                })
            
            df_scenarios = pd.DataFrame(scenario_data)
            st.dataframe(df_scenarios, use_container_width=True, hide_index=True)
            
            # Validation
            total_prob = sum(s['probability'] for s in settings['scenarios'])
            st.info(f" **Total Probability**: {total_prob:.2%}")
            
            if abs(total_prob - 1.0) > 0.01:
                st.warning(" Probabilities should sum to 100%")
            else:
                st.success(" Scenario probabilities are valid")

        # Advanced settings
        with st.expander(" Advanced Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                base_demand_multiplier = st.number_input(
                    "Base demand multiplier",
                    min_value=0.5,
                    max_value=2.0,
                    value=float(settings.get("base_demand_multiplier", 1.0)),
                    step=0.1,
                    disabled=not can_edit,
                    help="Adjusts the base demand level for all scenarios."
                )
            
            with col2:
                seed_value = st.number_input(
                    "Random seed",
                    min_value=0,
                    max_value=9999,
                    value=int(settings.get("seed_value", 42)),
                    step=1,
                    disabled=not can_edit,
                    help="Fixes random seed for reproducible scenarios."
            )

        # Save settings
        if can_edit:
            if st.button(" Save Settings", type="primary"):
                settings.update({
                    'is_enabled': is_enabled,
                    'num_scenarios': num_scenarios,
                    'volatility': volatility,
                    'base_demand_multiplier': base_demand_multiplier,
                    'seed_value': seed_value
                })
                st.session_state.uncertainty_settings = settings
                st.success(" Settings saved successfully!")
                
                # Show next steps
                st.info(" **Next Steps**: Go to 'Demand Uncertainty Analysis' to run the analysis with these settings.")

    else:
        st.info(" Demand uncertainty analysis is disabled. Enable it above to configure scenarios.")

    # Help section
    with st.expander(" How to Use These Settings"):
        st.markdown("""
        ### Configuration Guide
        
        **Number of Scenarios**:
        - **3-5 scenarios**: Good balance of accuracy and speed
        - **6-8 scenarios**: Better uncertainty coverage
        - **9-10 scenarios**: Most comprehensive but slower
        
        **Demand Volatility**:
        - **10-20%**: Stable demand patterns (established markets)
        - **20-30%**: Moderate variability (seasonal demand)
        - **30-50%**: High variability (new markets, uncertain conditions)
        
        **Scenario Interpretation**:
        - **Probability**: Likelihood of each scenario occurring
        - **Demand Multiplier**: How demand compares to base case
        - **1.0x multiplier**: Same as base demand
        - **1.2x multiplier**: 20% higher than base demand
        - **0.8x multiplier**: 20% lower than base demand
        
        ### Best Practices
        
        1. **Start Simple**: Begin with 3-5 scenarios and 20-30% volatility
        2. **Validate Scenarios**: Ensure probabilities sum to 100%
        3. **Business Context**: Match volatility to your market conditions
        4. **Iterate**: Adjust based on analysis results
        
        ### After Configuration
        
        1. Save your settings
        2. Go to "Demand Uncertainty Analysis" page
        3. Run the analysis with your scenarios
        4. Review cost and service level impacts
        """)


def generate_scenario_preview(num_scenarios: int, volatility: float) -> List[Dict[str, Any]]:
    """Generate preview scenarios based on configuration."""
    
    import numpy as np
    
    np.random.seed(42)  # For reproducible results
    
    scenarios = []
    
    # Always include base case
    base_prob = 0.4  # 40% probability for base case
    remaining_prob = 0.6
    
    # Generate other scenarios
    if num_scenarios > 1:
        # Distribute remaining probability
        if num_scenarios == 2:
            probs = [1.0]
        else:
            probs = np.random.dirichlet(np.ones(num_scenarios-1), 1)[0]
        
        # Generate demand multipliers
        multipliers = np.random.normal(1.0, volatility, num_scenarios-1)
        multipliers = np.clip(multipliers, 0.5, 1.5)  # Reasonable bounds
        
        # Create scenarios
        scenarios.append({
            'name': 'Base Case',
            'probability': base_prob,
            'demand_multiplier': 1.0,
            'description': 'Expected demand scenario'
        })
        
        for i in range(num_scenarios-1):
            scenarios.append({
                'name': f'Scenario {i+1}',
                'probability': remaining_prob * probs[i],
                'demand_multiplier': multipliers[i],
                'description': f'Demand multiplier: {multipliers[i]:.2f}x'
            })
    else:
        scenarios.append({
            'name': 'Base Case',
            'probability': 1.0,
            'demand_multiplier': 1.0,
            'description': 'Single scenario (deterministic)'
        })
    
    return scenarios
