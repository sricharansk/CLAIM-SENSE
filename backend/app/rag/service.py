"""Policy knowledge service: index lifecycle, clause retrieval with citations, grounded answers."""
from __future__ import annotations

import re
import threading

from sqlalchemy.orm import Session

from .. import llm
from ..config import settings
from ..models import PolicyClause
from .retriever import HybridIndex, expand_query, word_tokens

_index = HybridIndex()
_lock = threading.Lock()
_built = False


def rebuild_index(db: Session) -> int:
    global _built
    rows = db.query(PolicyClause).all()
    with _lock:
        _index.build([(c.id, c.version_id, f"{c.title}. {c.section}. {c.text}") for c in rows])
        _built = True
    return len(rows)


def _ensure(db: Session) -> None:
    if not _built:
        rebuild_index(db)


def citation(c: PolicyClause) -> dict:
    v = c.version
    return {
        "clause_id": c.id, "clause_ref": c.clause_ref, "title": c.title, "section": c.section, "page": c.page,
        "policy": v.policy.name, "product_code": v.policy.product_code, "version": v.version,
        "document": v.source_file, "text": c.text,
    }


def retrieve(db: Session, query: str, version_ids: set[int] | None = None, k: int = 5) -> list[dict]:
    _ensure(db)
    with _lock:
        hits = _index.search(query, version_ids, k)
    out = []
    for h in hits:
        c = db.get(PolicyClause, h.key)
        if c is None:
            continue
        out.append({**citation(c), "score": h.score, "bm25": h.bm25, "cosine": h.cosine,
                    "bm25_rank": h.bm25_rank, "vector_rank": h.vector_rank})
    return out


def clause_by_ref(db: Session, version_id: int, ref: str) -> PolicyClause | None:
    return db.query(PolicyClause).filter_by(version_id=version_id, clause_ref=ref).first()


def _best_sentences(question: str, text: str, limit: int = 2) -> list[str]:
    q = set(word_tokens(question))
    sents = [s.strip() for s in re.split(r"(?<=[.;])\s+", text) if s.strip()]
    ranked = sorted(sents, key=lambda s: -len(q & set(word_tokens(s))))
    return [s for s in ranked[:limit] if q & set(word_tokens(s))]


# Words nearly every clause shares; matching only these is not evidence that a clause answers the question.
GENERIC = set(word_tokens("policy policies insurer insurers insured insurance claim claims cover covers covered coverage "
                          "payable pay paid pays amount amounts charge charges expense expenses benefit benefits much many"))


def answer(db: Session, question: str, version_ids: set[int] | None = None, k: int = 4) -> dict:
    """Evidence-first answer. Refuses when retrieval finds no sufficiently relevant clause, or when the only
    overlap with the question is generic insurance vocabulary."""
    hits = retrieve(db, question, version_ids, k)
    focus = set(word_tokens(expand_query(question))) - GENERIC
    strong = [h for h in hits if h["score"] >= settings.rag_min_score
              and focus & set(word_tokens(f"{h['title']} {h['text']}"))]
    if not strong:
        return {"question": question, "grounded": False, "mode": "refusal",
                "answer": "I could not find policy wording that answers this question, so I will not guess. "
                          "Try naming the benefit, exclusion or condition you are asking about.",
                "citations": hits[:2]}
    quotes, seen = [], set()
    for h in strong[:3]:
        for s in _best_sentences(expand_query(question), h["text"]):
            if s not in seen:  # the same sentence often appears in several wording versions
                seen.add(s)
                quotes.append((s, h))
    if not quotes:
        quotes = [(strong[0]["text"], strong[0])]
    extractive = " ".join(f"{s} [{h['product_code']} v{h['version']} §{h['clause_ref']}, p.{h['page']}]" for s, h in quotes[:3])
    narrative = llm.grounded_answer(question, strong[:3]) if llm.enabled() else None
    return {"question": question, "grounded": True, "mode": "llm" if narrative else "extractive",
            "answer": narrative or extractive, "citations": strong}
