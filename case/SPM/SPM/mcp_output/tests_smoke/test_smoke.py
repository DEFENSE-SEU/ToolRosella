import importlib, sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

source_dir = os.path.join(os.getcwd(), "source")
if os.path.exists(source_dir):
    sys.path.insert(0, source_dir)


print("NO_PACKAGE - No testable package found")
