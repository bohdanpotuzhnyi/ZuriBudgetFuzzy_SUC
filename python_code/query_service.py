"""Bridges natural-language questions with the summarization API."""

from datetime import datetime, timezone
from typing import Any, Dict

from nlu import parse_question
from summarizer import FIELD_TO_DEPT, YEARS, answer_request


def answer_question(question: str) -> Dict[str, Any]:
    """Parse a free-text question, run the summarizer, and return metadata.

    Note: the returned `response` already embeds the parsed request under `response["request"]`,
    including any NLU confidence/candidate fields, so we avoid duplicating it at the top level.
    """
    parsed_request = parse_question(
        question,
        years_available=YEARS,
        field_to_dept=FIELD_TO_DEPT,
        dept_names=list(FIELD_TO_DEPT.values()),
    )
    response = answer_request(parsed_request)
    return {
        "raw_question": question,
        "asked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "nlu_interpretation": parsed_request,
        "response": response,
    }
