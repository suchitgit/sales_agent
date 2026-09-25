"""Text from stores is evidence, never instructions."""
import re
PATTERNS = [r"ignore (all |previous )?(rules|instructions)", r"^system\s*:", r"\bagent\s*:", r"write that"]

def sanitize(text: str) -> tuple[str, bool]:
    flagged = any(re.search(p, text, flags=re.I | re.M) for p in PATTERNS)
    return (f"[flagged as instruction-like; kept as data only] {text}" if flagged else text), flagged
