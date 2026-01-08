"""
Quick start guide for running optimization without errors.
"""

import subprocess
import sys
import os

def start_streamlit_app():
    """Start Streamlit app with proper configuration."""
    
    print("🚀 STARTING STREAMLIT APP")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ app.py not found in current directory")
        print("Please navigate to: c:/Users/zeelk/OneDrive/Desktop/Adani/hack-clink/auth-system")
        return False
    
    # Check if Excel file exists
    if not os.path.exists('Dataset_Dummy_Clinker_3MPlan.xlsx'):
        print("❌ Dataset_Dummy_Clinker_3MPlan.xlsx not found")
        return False
    
    print("✅ All required files found")
    print("🌐 Starting Streamlit app...")
    
    try:
        # Start Streamlit with specific configuration
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "false",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ]
        
        print(f"🔧 Running command: {' '.join(cmd)}")
        print("📱 App will open in your browser...")
        print("🔗 URL: http://localhost:8501")
        print("\n💡 TIPS:")
        print("   - Wait for app to fully load")
        print("   - Navigate to 'Run Optimization' page")
        print("   - Select months and click 'Run Optimization'")
        print("   - If you see errors, press F12 for browser console")
        
        # Start the app
        subprocess.run(cmd, cwd=os.getcwd())
        
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return False
    
    return True

def show_troubleshooting():
    """Show troubleshooting tips."""
    
    print("\n🔧 TROUBLESHOOTING TIPS")
    print("=" * 30)
    
    print("If you encounter errors:")
    print("1. 🔄 Refresh the browser page")
    print("2. 🗑️  Clear browser cache (Ctrl+Shift+Del)")
    print("3. 🔄 Restart the Streamlit app")
    print("4. 📱 Try a different browser")
    print("5. 🔍 Check browser console (F12) for JavaScript errors")
    print("6. 💾 Ensure enough disk space and memory")
    
    print("\n📞 If problems persist:")
    print("- Screenshot the error")
    print("- Copy browser console errors")
    print("- Share the terminal output")
    
    print("\n🎯 Expected behavior:")
    print("✅ Streamlit app starts successfully")
    print("✅ 'Run Optimization' page loads")
    print("✅ Optimization completes with 'optimal' status")
    print("✅ Results are displayed")

if __name__ == "__main__":
    print("🎯 OPTIMIZATION QUICK START")
    print("=" * 40)
    
    # Show troubleshooting first
    show_troubleshooting()
    
    # Ask user if they want to start
    try:
        response = input("\n🚀 Start Streamlit app? (y/n): ").lower().strip()
        if response in ['y', 'yes', '']:
            start_streamlit_app()
        else:
            print("❌ Cancelled. Run this script again when ready.")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
