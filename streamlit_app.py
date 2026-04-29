import subprocess
import sys

# Entry point wrapper for Streamlit Cloud
# This allows running from root while keeping code in app/ folder

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"])
