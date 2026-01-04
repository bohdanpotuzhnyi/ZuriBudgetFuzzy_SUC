import sys
import json

from query_service import answer_question


def main():
    if len(sys.argv) < 2:
        print("Usage: python ask.py 'your question here'")
        return 2

    question = " ".join(sys.argv[1:])
    result = answer_question(question)
    resp = result["response"]
    print("Interpreted request:")
    print(json.dumps(resp.get("request"), ensure_ascii=False, indent=2))
    print("\nResponse:")
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
