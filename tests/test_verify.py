"""The verifier catches a writer that does not follow the procedure."""
import sys; sys.path.insert(0, "src")
from salesagent.graph import nodes

def _state(cands, surv):
    return {"condition_id": "T7", "candidates": cands, "survivor": surv}

def test_out_of_order_and_no_stop_are_caught():
    bad = [{"text": "a", "died_at": "R2", "checks": [{"id": "R2", "pass": False}]},
           {"text": "b", "died_at": "R1", "checks": [{"id": "R1", "pass": False}, {"id": "R2", "pass": True}]},
           {"text": "c", "died_at": None, "checks": [{"id": f"R{i}", "pass": True} for i in range(1, 7)]}]
    v = nodes.verify(_state(bad, "c"))["verification"]
    assert not v["adherence"] and len(v["issues"]) >= 2

def test_survivor_must_pass_all_six():
    c = [{"text": "x", "died_at": None, "checks": [{"id": f"R{i}", "pass": True} for i in range(1, 5)]}] * 3
    assert not nodes.verify(_state(c, "x"))["verification"]["adherence"]

def test_model_answer_with_thinking_blocks_is_read_as_text():
    from salesagent.models import parse_json, text_of
    blocks = [{"type": "thinking", "thinking": ""}, {"type": "text", "text": '{"survivor": "x"}'}]
    assert text_of(blocks) == '{"survivor": "x"}' and parse_json(blocks)["survivor"] == "x"

def test_subject_line_is_extracted_from_labelled_answers():
    from salesagent.models import extract_line
    shapes = {  # shapes Fable 5.1 actually returned on 26 Sep
        "Three new states, one payroll process?": "Three new states, one payroll process?",
        "**Subject:** Three new states — before the 120 hires land\n\n*(Why: ...)*": "Three new states — before the 120 hires land",
        "Subject: Three new states, 120 open roles — one payroll process for all of them?": "Three new states, 120 open roles — one payroll process for all of them?",
        "**Subject line:**\n\n> 3 new states, 3 new payroll rulebooks\n\n**Why this one (brief):** ...": "3 new states, 3 new payroll rulebooks",
        "**Subject line:**\n\n**Three new states — three more payroll processes for LogiTrans?**\n\n**Why this one:**": "Three new states — three more payroll processes for LogiTrans?",
        "**Subject line:** Three new states — payroll compliance before the first hire lands\n\n**Why:**": "Three new states — payroll compliance before the first hire lands",
    }
    for raw, want in shapes.items():
        assert extract_line(raw) == want, raw
