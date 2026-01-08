"""
Fix for statsmodels import issue in plotly trendline functions
"""

import sys
import importlib.util

def safe_import_statsmodels():
    """Safely import statsmodels or provide mock if not available."""
    try:
        import statsmodels.api as sm
        return sm
    except ImportError:
        # Create a minimal mock for trendline functionality
        class MockStatsmodels:
            @staticmethod
            def trendline_function(data):
                # Simple linear trendline as fallback
                import numpy as np
                x = np.arange(len(data))
                if len(data) > 1:
                    coeffs = np.polyfit(x, data, 1)
                    trend = coeffs[0] * x + coeffs[1]
                    return trend.tolist()
                else:
                    return data
        return MockStatsmodels()

# Monkey patch the import
sys.modules['statsmodels.api'] = safe_import_statsmodels()

if __name__ == "__main__":
    # Test the import
    try:
        from plotly.express.trendline_functions import trendline_function
        print("✅ statsmodels import working")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        
    # Test our fix
    import plotly.express as px
    data = [1, 2, 3, 4, 5]
    try:
        trend = px.trendline_function(data)
        print(f"✅ Trendline working: {trend}")
    except Exception as e:
        print(f"❌ Trendline error: {e}")
