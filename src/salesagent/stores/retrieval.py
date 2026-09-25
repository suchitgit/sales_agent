"""Retrieval — stable truth: CRM notes and the capability catalogue. BM25 by default (no model needed);
vector search through an embeddings API when VOYAGE_API_KEY is set. Never a local model."""
from __future__ import annotations
import json, os
from rank_bm25 import BM25Okapi
from .. import config
from ..guards.sanitize import sanitize

_tok = lambda s: [w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split()]


class Retrieval:
    def __init__(self):
        self.notes = json.load(open(config.SEED / "crm_notes.json"))
        self.catalogue = json.load(open(config.SEED / "capability_catalogue.json"))
        self._bm25 = BM25Okapi([_tok(n["text"]) for n in self.notes])

    def search(self, query: str, prospect_id: str, k: int = 4) -> list[dict]:
        scores = self._bm25.get_scores(_tok(query))
        ranked = sorted(range(len(self.notes)), key=lambda i: -scores[i])
        out = []
        for i in ranked:
            n = self.notes[i]
            if n["prospect"] != prospect_id or scores[i] <= 0:
                continue
            clean, flagged = sanitize(n["text"])
            out.append({"id": n["id"], "text": clean, "score": round(float(scores[i]), 3), "flagged": flagged})
            if len(out) >= k:
                break
        # injection-like notes are surfaced regardless of score, so the guard is visible in the trace
        seen = {o["id"] for o in out}
        for n in self.notes:
            if n["prospect"] == prospect_id and n["id"] not in seen:
                clean, flagged = sanitize(n["text"])
                if flagged:
                    out.append({"id": n["id"], "text": clean, "score": 0.0, "flagged": True})
        return out

    def her_experiences(self, prospect_id: str) -> list[dict]:
        """Notes marked "her_experience": true in crm_notes.json — things she lived through, which the reader
        (playing her) must know. Selected by the data, not by id; flagged text never passes, marked or not."""
        out = []
        for n in self.notes:
            if n["prospect"] == prospect_id and n.get("her_experience"):
                clean, flagged = sanitize(n["text"])
                if not flagged:
                    out.append({"id": n["id"], "text": clean})
        return out

    def capabilities_for(self, pains: list[str]) -> list[str]:
        hits = []
        for cap in self.catalogue["provides"]:
            if any(p in " ".join(cap["pains"]) for p in pains):
                hits.append(cap["capability"])
        return hits
