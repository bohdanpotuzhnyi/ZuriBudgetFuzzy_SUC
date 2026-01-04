import re
from typing import Dict, List, Tuple, Optional

UML = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})

BRIEF_PATTERNS = [
    r"\bbrief\b",
    r"\bshort\b",
    r"\bquick\b",
    r"\bkurz\b",
    r"\bkurze\b",
    r"\buebersicht\b",
    r"\bübersicht\b",
]

DETAIL_PATTERNS = [
    r"\bdetailed\b",
    r"\bdetails\b",
    r"\bdetail\b",
    r"\bbreakdown\b",
    r"\bexplain\b",
    r"\bausfuehrlich\b",
    r"\bausführlich\b",
    r"\berklaer(en)?\b",
    r"\berklär(en)?\b",
    r"\bwinners\b",
    r"\blosers\b",
]

RECENT_PATTERNS = [
    r"\brecently\b",
    r"\blately\b",
    r"\brecent\b",
    r"\bkuerzlich\b",
    r"\bkürzlich\b",
    r"\bin letzter zeit\b",
]

ALL_INTENT_PATTERNS = [
    r"\bacross\b.*\bcity\b",
    r"\bwhole city\b",
    r"\bcity budget\b",
    r"\bspending more\b",
    r"\bmore on\b",
    r"\bbiggest increase\b",
    r"\bbiggest decreases?\b",
    r"\bwinners\b",
    r"\blosers\b",
    r"\bmovers?\b",
    r"\bshift\b",
    r"\bwo steigen\b",
    r"\bam staerksten\b",
    r"\bam stärksten\b",
    r"\bverlieren am meisten\b",
]

FIELD_PATTERNS = [
    (r"\beducation\b|\bschool(s)?\b|\bbildung\b|\bbildungs\w*\b|\bschule\b", "education", 0.95),
    (r"\bsport\b", "education", 0.70),
    (r"\bhealth\b|\bhealthcare\b|\bgesundheit\b|\bmedizin\b", "healthcare", 0.95),
    (r"\bumwelt\b", "healthcare", 0.70),
    (r"\btransport\b|\btraffic\b|\bverkehr\b|\bverkehrs\w*\b", "transport", 0.95),
    (r"\bpublic\s+transport\b|\broads?\b|\btram\b|\bentsorgung\b|\btiefbau\b", "transport", 0.95),
    (r"\benergy\b|\benergie\b|\bstrom\b|\bwasser\b|\butilities\b", "energy", 0.95),
    (r"\bdigital\b|\bdigitale?\b|\binfrastruktur\b|\binfrastructure\b", "digital infrastructure", 0.95),
    (r"\bsecurity\b|\bsafety\b|\bsicherheit\b|\bpolizei\b|\bpolice\b", "security", 0.95),
    (r"\bhousing\b|\bwohnen\b|\bwohnraum\b|\bconstruction\b|\bhochbau\b", "housing", 0.95),
    (
        r"\bpresidency\b|\bpraesidial\b|\bpräsidial\b|\bpraesidialdepartement\b|\bpräsidialdepartement\b",
        "presidency",
        0.95,
    ),
    (
        r"\badministration\b|\bverwaltung\b|\bbehoerden\b|\bbehörden\b|\bgesamtverwaltung\b",
        "administration",
        0.95,
    ),
    (r"\badministrative\b", "administration", 0.85),
    (r"\bfinance\b|\bfinanz(en)?\b", "finance", 0.95),
]


def normalize(text: str) -> str:
    t = text.lower().translate(UML)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def has_phrase(t_norm: str, phrase: str) -> bool:
    """Return True when a phrase appears as whole words in normalized text."""
    haystack = f" {t_norm} "
    needle = f" {phrase} "
    return needle in haystack


def parse_generalization_level(t_norm: str) -> int:
    if any(re.search(p, t_norm) for p in BRIEF_PATTERNS):
        return 0
    if any(re.search(p, t_norm) for p in DETAIL_PATTERNS):
        return 2
    return 1


def parse_timeline(t_norm: str, years_available: List[int], allow_recent_window: bool = True) -> Tuple[object, Optional[int]]:
    years = sorted(set(int(y) for y in re.findall(r"(19\d{2}|20\d{2})", t_norm)))
    since = None

    if ("since" in t_norm or "seit" in t_norm or "from" in t_norm) and years:
        since = years[0]

    m = re.search(r"\b(last|letzte|letzten)\s+(\d{1,2})\s+(years|jahre)\b", t_norm)
    if m and years_available:
        n = int(m.group(2))
        end = max(years_available)
        since = max(min(years_available), end - (n - 1))

    if since is None and len(years) >= 2:
        since = min(years)

    if since is None and allow_recent_window and years_available and any(re.search(p, t_norm) for p in RECENT_PATTERNS):
        end = max(years_available)
        since = max(min(years_available), end - 2)

    timeline = "all" if since is None else {"since": since}
    return timeline, since


def detect_all_intent(t_norm: str) -> bool:
    return any(re.search(p, t_norm) for p in ALL_INTENT_PATTERNS)


def disambiguate_dib(t_norm: str) -> str:
    if re.search(r"\bdigital\b|\bdigitale?\b|\binfrastruktur\b|\binfrastructure\b", t_norm):
        return "digital infrastructure"
    return "energy"


def parse_field(t_norm: str) -> Tuple[str, float, List[Tuple[str, float]]]:
    candidates: Dict[str, float] = {}

    def _register(field: str, score: float) -> None:
        candidates[field] = max(score, candidates.get(field, 0.0))

    if has_phrase(t_norm, "public transport") or has_phrase(t_norm, "public transportation") or has_phrase(t_norm, "roads"):
        _register("transport", 0.99)
    for pattern, field, score in FIELD_PATTERNS:
        if re.search(pattern, t_norm):
            _register(field, score)

    if not candidates:
        return "all", 0.20, [("all", 0.20)]

    hits = sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)
    best_field, best_score = hits[0]

    if len(hits) > 1 and best_score - hits[1][1] < 0.05:
        return "all", min(best_score, 0.40), hits
    return best_field, best_score, hits


def parse_question(
    question: str,
    years_available: List[int],
    field_to_dept: Dict[str, str],
    dept_names: List[str],
) -> Dict:
    t_norm = normalize(question)

    gen = parse_generalization_level(t_norm)
    is_all = detect_all_intent(t_norm)
    timeline, _ = parse_timeline(t_norm, years_available, allow_recent_window=not is_all)

    def _attach_meta(field: str, confidence: float, candidates: List[Tuple[str, float]]) -> Dict:
        payload = {"timeline": timeline, "field": field, "generalization_level": gen,
                   "field_confidence": float(confidence),
                   "field_candidates": [{"field": f, "confidence": float(score)} for f, score in candidates]}
        return payload

    if is_all:
        return _attach_meta("all", 0.95, [("all", 0.95)])

    dept_names_norm: Dict[str, List[str]] = {}
    for field_key, dept_name in field_to_dept.items():
        dept_names_norm.setdefault(normalize(dept_name), []).append(field_key)

    for dept_norm, fields in dept_names_norm.items():
        if dept_norm and dept_norm in t_norm:
            if len(fields) == 1:
                return _attach_meta(fields[0], 0.99, [(fields[0], 0.99)])
            if dept_norm == "departement der industriellen betriebe":
                field = disambiguate_dib(t_norm)
                return _attach_meta(field, 0.90, [(field, 0.90)])

    field, conf, hits = parse_field(t_norm)
    if conf < 0.5:
        field = "all"

    return _attach_meta(field, conf, hits)
