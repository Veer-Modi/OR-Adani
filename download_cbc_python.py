import os
import urllib.request
import zipfile
import ssl
import shutil

def install_cbc():
    print("Starting CBC download...")
    
    # Target directory
    solver_dir = r"C:\solvers\cbc"
    if not os.path.exists(solver_dir):
        os.makedirs(solver_dir)
        
    url = "https://ampl.com/dl/open/cbc/cbc-win64.zip"
    zip_path = os.path.join(os.environ["TEMP"], "cbc-win64.zip")
    
    # Create SSL context to handle legacy/strict server config
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(url, context=ctx) as response, open(zip_path, 'wb') as out_file:
            print("Downloading...")
            shutil.copyfileobj(response, out_file)
        print("Download complete.")
        
        print(f"Extracting to {solver_dir}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(solver_dir)
        print("Extraction complete.")
        
        # Verify executable exists
        bin_dir = os.path.join(solver_dir, "cbc-win64", "bin")  # Note: verify structure inside zip
        if not os.path.exists(bin_dir):
             # Try direct structure
             bin_dir = os.path.join(solver_dir, "bin")
             
        exe_path = os.path.join(bin_dir, "cbc.exe")
        if os.path.exists(exe_path):
            print(f"CBC executable found at: {exe_path}")
            return exe_path
        else:
             # Search for it
             for root, dirs, files in os.walk(solver_dir):
                 if "cbc.exe" in files:
                     print(f"CBC executable found at: {os.path.join(root, 'cbc.exe')}")
                     return os.path.join(root, 'cbc.exe')
             print("Error: cbc.exe not found in extracted files.")
             return None

    except Exception as e:
        print(f"Error during installation: {e}")
        return None

if __name__ == "__main__":
    install_cbc()
