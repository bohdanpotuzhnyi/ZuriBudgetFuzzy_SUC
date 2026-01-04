import json
import sys
from pathlib import Path

if __package__:
    from .parser import parse_question
else:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from nlu.parser import parse_question  # type: ignore

try:
    from summarizer import FIELD_TO_DEPT, YEARS
except ModuleNotFoundError:
    YEARS = list(range(2019, 2025))
    FIELD_TO_DEPT = {
        "education": "Schul- und Sportdepartement",
        "healthcare": "Gesundheits- und Umweltdepartement",
        "transport": "Tiefbau- und Entsorgungsdepartement",
        "energy": "Departement der Industriellen Betriebe",
        "digital infrastructure": "Departement der Industriellen Betriebe",
        "security": "Sicherheitsdepartement",
        "housing": "Hochbaudepartement",
        "presidency": "Präsidialdepartement",
        "administration": "Behörden und Gesamtverwaltung",
        "finance": "Finanzdepartement",
    }


def canonicalize(req: dict) -> dict:
    # ensure consistent format for comparison
    out = {
        "timeline": req.get("timeline", "all"),
        "field": req.get("field", "all"),
        "generalization_level": int(req.get("generalization_level", 1)),
    }
    # timeline dict normalization
    tl = out["timeline"]
    if isinstance(tl, dict) and "since" in tl:
        out["timeline"] = {"since": int(tl["since"])}
    elif isinstance(tl, int):
        out["timeline"] = {"since": tl}
    return out


def load_test_set() -> dict:
    test_path = Path(__file__).resolve().parent / "nlu_test_set.json"
    with test_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    data = load_test_set()
    items = data["items"]
    total = len(items)
    ok = 0

    for it in items:
        utter = it["utterance"]
        expected = canonicalize(it["expected"])

        pred = canonicalize(
            parse_question(
                utter,
                years_available=YEARS,
                field_to_dept=FIELD_TO_DEPT,
                dept_names=list(FIELD_TO_DEPT.values()),
            )
        )

        if pred == expected:
            ok += 1
        else:
            print(f"\nFAIL id={it['id']}")
            print("Q:       ", utter)
            print("Expected:", expected)
            print("Pred:    ", pred)

    print(f"\nAccuracy: {ok}/{total} = {ok/total:.1%}")


if __name__ == "__main__":
    main()
