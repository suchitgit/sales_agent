"""The runtime's central claim: from the source systems it rebuilds the blocks a human assembled by hand."""
import sys; sys.path.insert(0, "src")
from salesagent.blocks import fetch_all, build, golden

def test_every_block_matches_the_experiment():
    g = golden(build(fetch_all("sunidhi")))
    assert g and all(g.values()), f"blocks differing from the experiment: {[k for k, v in g.items() if not v]}"

def test_injection_never_in_a_block():
    b = build(fetch_all("sunidhi")); assert all("IGNORE" not in v for v in b.values())

def test_derived_is_computed_not_stored():
    import json; from salesagent import config
    assert not any("signal" in f.name for f in config.SOURCES.rglob("*.json")), "B3 must be computed, never stored"
