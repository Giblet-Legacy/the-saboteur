"""canary_loud.py — exits 1 with a named error. Must be judged PASS."""
import sys
print("CANARY: refused, reason=test")
sys.exit(1)
