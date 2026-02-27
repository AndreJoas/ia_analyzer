# logger.py
import json
# =========================================================
# DEBUG LOGGER BONITO
# =========================================================
import time

def log_step(step, data=None):
    print("\n" + "="*60)
    print(f"🚀 STEP: {step}")
    if data is not None:
        print("📦 DATA:")
        try:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(data)
    print("="*60 + "\n")