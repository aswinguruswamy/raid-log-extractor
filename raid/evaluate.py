"""Score the tool's RAID items against the correct answers (story S2-04, KAN-18).

Matching: a tool item matches an expected item when the tool's source quote and
the expected evidence share most of their words. Each tool item and each
expected item can match only once (greedy, best overlap first).

Scores:
  recall(type)    = expected items of that type that the tool found with an accepted type
  precision(type) = tool items of that type that match an expected item of an accepted type
  invented owner  = an owner name that does not appear anywhere in the notes
  invented date   = a due date that does not appear anywhere in the notes
  guessed owner   = an owner given where the notes name nobody for that item
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .schema import NOT_STATED, ItemType

MATCH_THRESHOLD = 0.6
_WORD = re.compile(r"[a-z0-9]+")


def _words(text: str) -> List[str]:
    return _WORD.findall(text.lower().replace("’", "'"))


def overlap(evidence: str, quote: str) -> float:
    """Share of the evidence words that are also in the quote (1.0 when one contains the other)."""
    ev, qt = " ".join(_words(evidence)), " ".join(_words(quote))
    if not ev or not qt:
        return 0.0
    if ev in qt or qt in ev:
        return 1.0
    ev_set, qt_set = set(ev.split()), set(qt.split())
    return len(ev_set & qt_set) / len(ev_set)


def same_person(expected: str, found: str) -> bool:
    """'Mei Lin' and 'Mei' are the same person; 'Not stated' only matches 'Not stated'."""
    if expected == NOT_STATED or found == NOT_STATED:
        return expected == found
    exp, fnd = _words(expected), _words(found)
    return bool(exp and fnd) and (exp[0] == fnd[0] or set(exp) <= set(fnd) or set(fnd) <= set(exp))


def accepted_types(expected: dict) -> List[str]:
    return [expected["type"]] + list(expected.get("also_accept_types", []))


@dataclass
class SampleScore:
    sample: str
    expected: List[dict]
    found: List[dict]
    pairs: List[Tuple[int, int, float]] = field(default_factory=list)  # (expected index, found index, overlap)
    invented_owners: List[str] = field(default_factory=list)
    invented_dates: List[str] = field(default_factory=list)
    guessed_owners: List[str] = field(default_factory=list)

    def matched_expected(self) -> Dict[int, int]:
        return {e: f for e, f, _ in self.pairs}

    def matched_found(self) -> Dict[int, int]:
        return {f: e for e, f, _ in self.pairs}


def score_sample(sample: str, notes: str, expected: List[dict], found: List[dict]) -> SampleScore:
    """Match one sample's tool items to its expected items and check owners and dates."""
    candidates = []
    for e, exp in enumerate(expected):
        for f, item in enumerate(found):
            score = overlap(exp["evidence"], item.get("source_quote", ""))
            if score >= MATCH_THRESHOLD:
                candidates.append((score, e, f))
    result = SampleScore(sample=sample, expected=expected, found=found)
    used_e, used_f = set(), set()
    for score, e, f in sorted(candidates, key=lambda c: (-c[0], c[1], c[2])):
        if e not in used_e and f not in used_f:
            used_e.add(e), used_f.add(f)
            result.pairs.append((e, f, score))

    notes_lower = notes.lower()
    for f, item in enumerate(found):
        owner, due = item.get("owner", NOT_STATED), item.get("due_date", NOT_STATED)
        if owner != NOT_STATED and not any(w in notes_lower for w in _words(owner) if len(w) > 1):
            result.invented_owners.append(f"{owner} ({item.get('description', '')[:60]})")
        if due != NOT_STATED and due not in notes:
            result.invented_dates.append(f"{due} ({item.get('description', '')[:60]})")
        e = result.matched_found().get(f)
        if e is not None and expected[e]["owner"] == NOT_STATED and owner != NOT_STATED:
            result.guessed_owners.append(f"{owner} for '{expected[e]['summary']}'")
    return result


@dataclass
class TypeScore:
    expected: int = 0
    found: int = 0
    recall_hits: int = 0
    precision_hits: int = 0

    @property
    def recall(self) -> Optional[float]:
        return self.recall_hits / self.expected if self.expected else None

    @property
    def precision(self) -> Optional[float]:
        return self.precision_hits / self.found if self.found else None


@dataclass
class Report:
    samples: List[SampleScore]
    by_type: Dict[str, TypeScore]
    total: TypeScore
    owner_checked: int = 0
    owner_correct: int = 0
    date_checked: int = 0
    date_correct: int = 0

    @property
    def invented_owners(self) -> List[str]:
        return [o for s in self.samples for o in s.invented_owners]

    @property
    def invented_dates(self) -> List[str]:
        return [d for s in self.samples for d in s.invented_dates]

    @property
    def guessed_owners(self) -> List[str]:
        return [g for s in self.samples for g in s.guessed_owners]


def build_report(samples: List[SampleScore]) -> Report:
    by_type = {t.value: TypeScore() for t in ItemType}
    total = TypeScore()
    report = Report(samples=samples, by_type=by_type, total=total)

    for s in samples:
        matched_e, matched_f = s.matched_expected(), s.matched_found()
        for e, exp in enumerate(s.expected):
            by_type[exp["type"]].expected += 1
            total.expected += 1
            f = matched_e.get(e)
            if f is not None and s.found[f]["type"] in accepted_types(exp):
                by_type[exp["type"]].recall_hits += 1
                total.recall_hits += 1
        for f, item in enumerate(s.found):
            by_type[item["type"]].found += 1
            total.found += 1
            e = matched_f.get(f)
            if e is not None and item["type"] in accepted_types(s.expected[e]):
                by_type[item["type"]].precision_hits += 1
                total.precision_hits += 1
        for e, f, _ in s.pairs:
            exp, item = s.expected[e], s.found[f]
            if exp["owner"] != NOT_STATED or item.get("owner", NOT_STATED) != NOT_STATED:
                report.owner_checked += 1
                report.owner_correct += same_person(exp["owner"], item.get("owner", NOT_STATED))
            if exp["due_date"] != NOT_STATED or item.get("due_date", NOT_STATED) != NOT_STATED:
                report.date_checked += 1
                report.date_correct += exp["due_date"] == item.get("due_date", NOT_STATED)
    return report


def misses_and_extras(sample: SampleScore) -> Tuple[List[str], List[str], List[str]]:
    """Expected items the tool missed, tool items with no match, and type mix-ups."""
    matched_e, matched_f = sample.matched_expected(), sample.matched_found()
    misses = [f"{exp['type']}: {exp['summary']}" for e, exp in enumerate(sample.expected) if e not in matched_e]
    extras = [f"{it['type']}: {it.get('description', '')}" for f, it in enumerate(sample.found) if f not in matched_f]
    mixups = [
        f"expected {sample.expected[e]['type']}, tool said {sample.found[f]['type']}: {sample.expected[e]['summary']}"
        for e, f, _ in sample.pairs
        if sample.found[f]["type"] not in accepted_types(sample.expected[e])
    ]
    return misses, extras, mixups
