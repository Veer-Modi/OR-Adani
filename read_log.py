try:
    with open(r"c:\Users\khush\Downloads\clinker-pro\OR-Adani\logs\app.log", "r") as f:
        lines = f.readlines()
        print("".join(lines[-200:]))
except Exception as e:
    print(f"Error reading log: {e}")
