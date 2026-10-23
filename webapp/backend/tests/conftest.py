import os
import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # webapp/backend
REPO = os.path.dirname(os.path.dirname(APP))
SAMPLE = os.path.join(APP, "tests", "data", "sample_project")
if APP not in sys.path:
    sys.path.insert(0, APP)
