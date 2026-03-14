import os
# os.environ["QT_QPA_PLATFORM"] = "offscreen"
from snappergui.application import start_ui
import sys

if __name__ == "__main__":
    try:
        start_ui()
    except Exception as e:
        print(f"Caught error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
