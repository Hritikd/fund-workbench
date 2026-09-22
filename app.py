from __future__ import annotations

import json
import os

import streamlit as st

from fund_workbench.analysis import (
    build_screening_memo,
    generate_diligence_questions,
    memo_to_markdown,
)
from fund_workbench.evidence import build_ledger, detect_contradictions
from fund_workbench.io import dump_json, source_from_file
from fund_workbench.llm import has_api_key
from fund_workbench.models import Source, SourceType, Thesis
from fund_workbench.samples import sample_sources, sample_thesis, sample_updates
from fund_workbench.updates import (
    compare_updates,
    comparison_to_markdown,
    parse_update,
)

st.set_page_config(page_title="Fund Workbench", page_icon="◫", layout="wide")
st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 2rem;}
    .hero {padding: 1.3rem 1.5rem; border: 1px solid #d9d5ca; border-radius: 14px;
           background: linear-gradient(130deg, #fff 0%, #eeeaff 100%); margin-bottom: 1.2rem;}
    .hero h1 {margin: 0; letter-spacing: -0.04em;}
    .hero p {margin: .4rem 0 0; color: #4d5661;}
    .status {display: inline-block; padding: .2rem .55rem; border-radius: 999px;
             background: #e9e5ff; color: #40318a; font-size: .8rem;}
    [data-testid="stMetric"] {background: white; border: 1px solid #dedbd2; padding: .8rem; border-radius: 10px;}
    </style>
    <div class="hero">
      <span class="status">OPEN SOURCE · LOCAL FIRST</span>
      <h1>Fund Workbench</h1>
      <p>Turn scattered opportunity evidence into traceable briefs, better questions, and follow-up queues.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "sources" not in st.session_state:
    st.session_state.sources = []
if "ledger" not in st.session_state:
    st.session_state.ledger = None

with st.sidebar:
    st.header("Workspace")
    company = st.text_input("Company or opportunity", value="Northstar Robotics")
    if st.button("Load synthetic demo", width="stretch"):
        st.session_state.sources = sample_sources()
        st.session_state.ledger = None
        st.rerun()
    st.caption("The demo uses a fictional company and requires no API key.")
    st.divider()
    api_ready = has_api_key()
    st.write(f"AI extraction: {'available' if api_ready else 'no API key detected'}")
    use_ai = st.toggle("Use AI structured extraction", value=False, disabled=not api_ready)
    if api_ready:
        st.caption(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-6-astra')}")
    st.caption("Uploaded content is processed in memory. This app does not implement persistent storage.")

tab_evidence, tab_memo, tab_questions, tab_updates = st.tabs(
    ["1 · Evidence ledger", "2 · Screening brief", "3 · Diligence planner", "4 · Portfolio updates"]
)

with tab_evidence:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Add evidence")
        uploaded = st.file_uploader(
            "Upload a pitch deck, update, notes, or research",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
        )
        upload_type = st.selectbox("Uploaded source type", list(SourceType), format_func=lambda x: x.value)
        pasted_title = st.text_input("Pasted source title", value="Additional notes")
        pasted_type = st.selectbox("Pasted source type", list(SourceType), index=2, format_func=lambda x: x.value)
        pasted_content = st.text_area("Paste optional source text", height=150)
        if st.button("Add sources", type="primary"):
            added: list[Source] = []
            for item in uploaded or []:
                added.append(source_from_file(item.name, item.getvalue(), upload_type))
            if pasted_content.strip():
                added.append(
                    Source(
                        id=f"pasted-{len(st.session_state.sources) + 1}",
                        title=pasted_title,
                        source_type=pasted_type,
                        content=pasted_content,
                    )
                )
            st.session_state.sources.extend(added)
            st.session_state.ledger = None
            st.success(f"Added {len(added)} source(s).")
    with right:
        st.subheader(f"Sources · {len(st.session_state.sources)}")
        if not st.session_state.sources:
            st.info("Load the synthetic demo or add at least one source.")
        for source in st.session_state.sources:
            with st.expander(f"{source.title} · {source.source_type.value}"):
                st.write(source.content[:2500])
                if source.url:
                    st.caption(source.url)
        clear_col, build_col = st.columns(2)
        if clear_col.button("Clear sources", width="stretch"):
            st.session_state.sources = []
            st.session_state.ledger = None
            st.rerun()
        if build_col.button(
            "Build evidence ledger",
            width="stretch",
            type="primary",
            disabled=not st.session_state.sources,
        ):
            try:
                with st.spinner("Extracting and validating claims…"):
                    st.session_state.ledger = build_ledger(company, st.session_state.sources, ai=use_ai)
            except Exception as exc:
                st.error(f"Extraction failed: {exc}")

    ledger = st.session_state.ledger
    if ledger:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Claims", len(ledger.claims))
        col2.metric("Sources", len(ledger.sources))
        col3.metric("Mode", ledger.mode)
        col4.metric("Possible conflicts", len(detect_contradictions(ledger.claims)))
        rows = [
            {
                "topic": claim.topic,
                "status": claim.status.value,
                "statement": claim.statement,
                "source": claim.source_id,
                "confidence": claim.confidence,
            }
            for claim in ledger.claims
        ]
        st.dataframe(rows, width="stretch", hide_index=True)
        st.download_button(
            "Download evidence ledger (JSON)",
            dump_json(ledger),
            file_name="evidence-ledger.json",
            mime="application/json",
        )

with tab_memo:
    st.subheader("Build a reviewable screening brief")
    if not st.session_state.ledger:
        st.info("Build an evidence ledger first.")
    else:
        defaults = sample_thesis()
        thesis_name = st.text_input("Thesis name", value=defaults.name)
        required = st.text_input("Required terms (comma-separated)", value=", ".join(defaults.required_terms))
        preferred = st.text_input("Preferred terms", value=", ".join(defaults.preferred_terms))
        excluded = st.text_input("Excluded terms", value=", ".join(defaults.excluded_terms))
        if st.button("Generate screening brief", type="primary"):
            thesis = Thesis(
                name=thesis_name,
                required_terms=[item.strip() for item in required.split(",") if item.strip()],
                preferred_terms=[item.strip() for item in preferred.split(",") if item.strip()],
                excluded_terms=[item.strip() for item in excluded.split(",") if item.strip()],
            )
            st.session_state.memo = build_screening_memo(st.session_state.ledger, thesis)
        if memo := st.session_state.get("memo"):
            st.warning("The routing score is a transparent keyword triage aid, not an investment score.")
            st.markdown(memo_to_markdown(memo))
            st.download_button(
                "Download screening brief (Markdown)",
                memo_to_markdown(memo),
                file_name="screening-brief.md",
                mime="text/markdown",
            )

with tab_questions:
    st.subheader("Find the next conversation, not a synthetic verdict")
    if not st.session_state.ledger:
        st.info("Build an evidence ledger first.")
    else:
        questions = generate_diligence_questions(st.session_state.ledger)
        for index, question in enumerate(questions, 1):
            st.markdown(
                f"**{index}. {question.question}**  \n`{question.priority}` · {question.category}  \n{question.reason}"
            )
        st.download_button(
            "Download questions (JSON)",
            json.dumps([question.model_dump() for question in questions], indent=2),
            file_name="diligence-questions.json",
            mime="application/json",
        )

with tab_updates:
    st.subheader("Compare portfolio updates without losing the follow-up")
    default_previous, default_current = sample_updates()
    sample_previous = """Metrics
ARR: 15
Paying factories: 12
Monthly retention: 95%

Wins
- Completed first automotive pilot

Risks
- Security review is delaying one expansion

Asks
- Introductions to two automotive suppliers"""
    sample_current = """Metrics
ARR: 18
Paying factories: 14
Monthly retention: 96%

Wins
- Converted two pilots to annual contracts

Risks
- Hardware supplier delay threatens September deployments

Asks
- Backup hardware supplier introductions
- Security review template"""
    previous_col, current_col = st.columns(2)
    with previous_col:
        previous_period = st.text_input("Previous period", value=default_previous.period)
        previous_text = st.text_area("Previous update", value=sample_previous, height=300)
    with current_col:
        current_period = st.text_input("Current period", value=default_current.period)
        current_text = st.text_area("Current update", value=sample_current, height=300)
    if st.button("Compare updates", type="primary"):
        previous = parse_update(company, previous_period, previous_text)
        current = parse_update(company, current_period, current_text)
        st.session_state.comparison = compare_updates(previous, current)
    if comparison := st.session_state.get("comparison"):
        st.markdown(comparison_to_markdown(comparison))
        st.download_button(
            "Download comparison (Markdown)",
            comparison_to_markdown(comparison),
            file_name="portfolio-update-comparison.md",
            mime="text/markdown",
        )

st.divider()
st.caption(
    "Fund Workbench supports human review. It does not make investment decisions, verify confidential claims, "
    "or replace legal, financial, security, or technical diligence."
)
