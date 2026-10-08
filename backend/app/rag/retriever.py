"""Hybrid retrieval over policy clauses.

Two independent rankers are fused with reciprocal rank fusion (RRF):
  * BM25 over word tokens (exact policy vocabulary: "deductible", "cataract");
  * TF-IDF cosine over character 3-5 grams (robust to inflections and spelling:
    "hospitalised" vs "hospitalisation", "co-pay" vs "co-payment").
Both are pure Python so the demo runs without a model download or API key. An
embedding retriever can be added as a third ranker behind the same interface.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

STOPWORDS = set("""a an and are as at be by for from has have if in into is it its of on or that the this to was
were will with any all not no than then there these those such which who whom what when where why how
i me my we our you your he she they them their his her do does did shall may can""".split())
WORD_RE = re.compile(r"[a-z0-9]+")
# Small insurance query-expansion map: lay terms -> policy vocabulary.
SYNONYMS = {
    "drunk": "alcohol influence intoxication", "drink": "alcohol influence", "drinking": "alcohol influence",
    "dui": "alcohol influence", "copay": "co-payment", "excess": "deductible", "pregnancy": "maternity childbirth",
    "baby": "maternity childbirth", "plastic surgery": "cosmetic", "first year": "waiting period months",
    "car": "vehicle", "bike": "vehicle", "crash": "collision accident", "stolen": "theft",
    "hospital room": "room rent", "documents": "documents required", "paperwork": "documents required",
}


def expand_query(q: str) -> str:
    low = q.lower()
    extra = [v for k, v in SYNONYMS.items() if re.search(rf"\b{re.escape(k)}\b", low)]
    return q + (" " + " ".join(extra) if extra else "")


def _stem(tok: str) -> str:
    for suf in ("isation", "ization", "ations", "ation", "ments", "ment", "ings", "ing", "ies", "ed", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 3:
            return tok[: -len(suf)] + ("y" if suf == "ies" else "")
    return tok


def word_tokens(text: str) -> list[str]:
    return [_stem(t) for t in WORD_RE.findall(text.lower()) if t not in STOPWORDS]


def char_ngrams(text: str, lo: int = 3, hi: int = 5) -> Counter:
    grams: Counter = Counter()
    for w in WORD_RE.findall(text.lower()):
        if w in STOPWORDS:
            continue
        w = f" {w} "
        for n in range(lo, hi + 1):
            for i in range(len(w) - n + 1):
                grams[w[i:i + n]] += 1
    return grams


@dataclass
class Doc:
    key: int  # policy_clauses.id
    group: int  # policy_versions.id
    text: str
    tokens: list[str] = field(default_factory=list)
    grams: Counter = field(default_factory=Counter)


@dataclass
class Hit:
    key: int
    score: float  # fused, normalised to 0..1 against the best possible fused score
    bm25: float
    cosine: float
    bm25_rank: int | None
    vector_rank: int | None


class HybridIndex:
    k1, b, rrf_k = 1.5, 0.75, 60

    def __init__(self) -> None:
        self.docs: list[Doc] = []
        self.df: Counter = Counter()
        self.gram_df: Counter = Counter()
        self.avgdl = 0.0
        self.gram_norms: dict[int, float] = {}

    def build(self, items: list[tuple[int, int, str]]) -> None:
        self.docs = [Doc(k, g, t, word_tokens(t), char_ngrams(t)) for k, g, t in items]
        self.df = Counter(tok for d in self.docs for tok in set(d.tokens))
        self.gram_df = Counter(gm for d in self.docs for gm in d.grams)
        self.avgdl = sum(len(d.tokens) for d in self.docs) / max(len(self.docs), 1)
        self.gram_norms = {d.key: math.sqrt(sum((c * self._gidf(g)) ** 2 for g, c in d.grams.items())) or 1.0
                           for d in self.docs}

    def _idf(self, tok: str) -> float:
        n, df = len(self.docs), self.df.get(tok, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def _gidf(self, gram: str) -> float:
        return math.log((1 + len(self.docs)) / (1 + self.gram_df.get(gram, 0))) + 1

    def _bm25(self, q: list[str], d: Doc) -> float:
        tf = Counter(d.tokens)
        dl = len(d.tokens) or 1
        score = 0.0
        for t in set(q):
            if t in tf:
                f = tf[t]
                score += self._idf(t) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return score

    def _cosine(self, qg: Counter, qnorm: float, d: Doc) -> float:
        dot = sum(c * self._gidf(g) * d.grams.get(g, 0) * self._gidf(g) for g, c in qg.items())
        return dot / (qnorm * self.gram_norms[d.key])

    def search(self, query: str, groups: set[int] | None = None, k: int = 5) -> list[Hit]:
        pool = [d for d in self.docs if groups is None or d.group in groups]
        if not pool:
            return []
        query = expand_query(query)
        q = word_tokens(query)
        qg = char_ngrams(query)
        qnorm = math.sqrt(sum((c * self._gidf(g)) ** 2 for g, c in qg.items())) or 1.0
        bm = {d.key: self._bm25(q, d) for d in pool}
        cs = {d.key: self._cosine(qg, qnorm, d) for d in pool}
        bm_rank = {key: i + 1 for i, key in enumerate(sorted((x for x in bm if bm[x] > 0), key=lambda x: -bm[x]))}
        cs_rank = {key: i + 1 for i, key in enumerate(sorted((x for x in cs if cs[x] > 0.05), key=lambda x: -cs[x]))}
        weights = (1.5, 1.0)  # exact policy vocabulary (BM25) is weighted above fuzzy n-gram similarity
        best = sum(weights) / (self.rrf_k + 1)
        hits = []
        for d in pool:
            fused = sum(w / (self.rrf_k + r[d.key]) for w, r in zip(weights, (bm_rank, cs_rank), strict=False) if d.key in r)
            if fused:
                # relevance gate: fused rank score scaled by how strongly the clause actually matches
                strength = min(1.0, cs[d.key] * 2.5)
                hits.append(Hit(d.key, round(fused / best * strength, 4), round(bm[d.key], 4), round(cs[d.key], 4),
                                bm_rank.get(d.key), cs_rank.get(d.key)))
        hits.sort(key=lambda h: -h.score)
        return hits[:k]
