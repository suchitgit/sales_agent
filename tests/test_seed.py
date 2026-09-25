import json, sys; sys.path.insert(0, "src")
from salesagent import config
def test_seed_files_present():
    for f in ["prospects.json","crm_notes.json","capability_catalogue.json","decision_cases.json","judgement_rules.json","traces.json","knowledge_graph.json","rep_profile.json"]:
        assert (config.SEED / f).exists(), f
def test_traces_are_six_and_five():
    t = json.load(open(config.SEED / "traces.json")); assert [x["id"] for x in t["reader"]] == ["R1","R2","R3","R4","R5","R6"]; assert len(t["seller"]) == 5
def test_choice_sets_recorded():
    for c in json.load(open(config.SEED / "decision_cases.json")): assert c["chosen"] in c["choice_set"]
def test_null_prospect_exists():
    assert any(p["expect"] == "decline" for p in json.load(open(config.SEED / "prospects.json")))
def test_her_experience_is_marked_in_data_and_never_flagged():
    from salesagent.guards.sanitize import sanitize
    notes = json.load(open(config.SEED / "crm_notes.json"))
    marked = {n["id"] for n in notes if n.get("her_experience")}
    assert {"n2", "n3"} <= marked and not marked & {"n1", "n6", "n11"}
    assert not any(sanitize(n["text"])[1] for n in notes if n.get("her_experience"))
def test_known_winners_are_written_by_a_person():
    known = json.load(open(config.SEED / "known_winners.json"))
    prospects = {p["id"] for p in json.load(open(config.SEED / "prospects.json"))}
    assert known and all(v["written_by"] == "human" and v["line"] and pid in prospects for pid, v in known.items())
