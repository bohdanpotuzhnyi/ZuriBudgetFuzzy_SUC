import json
from typing import List, Dict, Any

import streamlit as st

from query_service import answer_question


st.set_page_config(page_title="Zürich Budget Q&A", page_icon="💰", layout="wide")
st.title("Zürich Budget Summaries")
st.write(
    "Ask a question in natural language to see how the NLU layer interprets it and how the summarizer responds."
)


def add_to_history(entry: Dict[str, Any]) -> None:
    history: List[Dict[str, Any]] = st.session_state.setdefault("history", [])
    history.insert(0, entry)
    # Keep history short to avoid bloating the session
    if len(history) > 10:
        history.pop()


with st.form("qa_form", clear_on_submit=False):
    question = st.text_area(
        "Ask something about Zürich's budget",
        placeholder="Example: Which departments increased their share since 2019?",
    )
    submitted = st.form_submit_button("Submit")

if submitted:
    question = (question or "").strip()
    if not question:
        st.warning("Please enter a question before submitting.")
    else:
        with st.spinner("Querying summarizer..."):
            result = answer_question(question)
        add_to_history(result)
        st.success("Answer received. Scroll down to inspect details.")
        resp_msg = (result.get("response") or {}).get("message")
        if resp_msg:
            st.markdown("**Answer from server**")
            st.info(resp_msg)

history = st.session_state.get("history", [])
if history:
    st.subheader("Recent Queries")
    for idx, entry in enumerate(history, start=1):
        with st.expander(f"{idx}. {entry['raw_question']}", expanded=(idx == 1)):
            st.markdown(f"**Asked at:** {entry['asked_at']}")
            st.markdown("**API response**")
            st.json(entry["response"])
else:
    st.info("No questions asked yet. Submit one above to see the logs.")
