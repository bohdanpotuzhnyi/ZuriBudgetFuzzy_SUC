import os
import json
import sys

from .zurich_budget_linguistic_summaries import answer_request


def main() -> int:
    # Expect cached CSVs for offline demo. If missing, guide the user.
    csv_path = "zrh_budget_by_dept_year.csv"
    if not os.path.exists(csv_path):
        print(
            "Cached CSV not found. For an offline demo, first generate it by running:\n"
            "  python3 summarizer/zurich_budget_linguistic_summaries.py\n\n"
            "Alternatively, install dependencies and allow network access to fetch from the API:\n"
            "  pip install pandas numpy requests\n",
            file=sys.stderr,
        )
        # Continue anyway; the underlying loader may still fetch from API if available

    examples = [
        (
            "How is the government planning money for education?",
            {"timeline": "all", "field": "education", "generalization_level": 1},
        ),
        (
            "So what are they spending more on now?",
            {"timeline": "all", "field": "all", "generalization_level": 1},
        ),
        (
            "Education since 2019?",
            {"timeline": {"since": 2019}, "field": "education", "generalization_level": 2},
        ),
    ]

    for i, (question, req) in enumerate(examples, start=1):
        print(f"\nExample {i}")
        print(f"Q: {question}")
        print("Request:")
        print(json.dumps(req, ensure_ascii=False))
        try:
            resp = answer_request(req)
        except Exception as e:
            print(f"Error: {e}")
            continue
        print("Response:")
        print(json.dumps(resp, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
