"""canary_same.py — fails exactly as on a clean copy. Must be judged FAIL (v2): nothing new was caught."""
import sys
print("CANARY: refused, reason=test")
sys.exit(1)
