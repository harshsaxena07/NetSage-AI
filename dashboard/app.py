"""
NetSage AI - Streamlit Dashboard

Cisco Network Troubleshooting Assistant

Features:
- Case selection
- Cisco evidence display
- Deterministic rule checker results
- AI diagnosis display
- Confidence
- Recommended Cisco commands
- Fix steps
- Human review
- Evaluation metrics
"""

from pathlib import Path

import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

CASES_FILE = DATA_DIR / "cases.csv"

RULE_FILE = DATA_DIR / "rule_check_results.csv"

DIAGNOSES_FILE = DATA_DIR / "diagnoses.csv"

REVIEW_FILE = DATA_DIR / "human_review.csv"


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="NetSage AI",
    page_icon="🌐",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-top: 0;
    }

    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
    }

    .evidence-box {
        background-color: #f5f7fa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ddd;
    }

    .review-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">NetSage AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Cisco Network Troubleshooting Assistant'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_cases():

    if not CASES_FILE.exists():

        return pd.DataFrame()

    return pd.read_csv(
        CASES_FILE
    )


@st.cache_data
def load_rules():

    if not RULE_FILE.exists():

        return pd.DataFrame()

    return pd.read_csv(
        RULE_FILE
    )


@st.cache_data
def load_diagnoses():

    if not DIAGNOSES_FILE.exists():

        return pd.DataFrame()

    try:

        return pd.read_csv(
            DIAGNOSES_FILE
        )

    except pd.errors.EmptyDataError:

        return pd.DataFrame()


def load_reviews():

    if not REVIEW_FILE.exists():

        return pd.DataFrame(
            columns=[
                "case_id",
                "decision",
                "corrected_diagnosis",
                "reviewer_reason"
            ]
        )

    try:

        return pd.read_csv(
            REVIEW_FILE
        )

    except pd.errors.EmptyDataError:

        return pd.DataFrame(
            columns=[
                "case_id",
                "decision",
                "corrected_diagnosis",
                "reviewer_reason"
            ]
        )


cases = load_cases()

rules = load_rules()

diagnoses = load_diagnoses()

reviews = load_reviews()


# =========================================================
# CHECK DATA
# =========================================================

if cases.empty:

    st.error(
        "cases.csv could not be loaded."
    )

    st.stop()


# =========================================================
# DASHBOARD METRICS
# =========================================================

total_cases = len(cases)

if diagnoses.empty:

    ai_diagnosed = 0

    correct = 0

    incorrect = 0

    unavailable = 0

else:

    ai_diagnosed = int(
        (
            diagnoses["evaluation"]
            != "AI_UNAVAILABLE"
        ).sum()
    )

    correct = int(
        (
            diagnoses["evaluation"]
            == "Correct"
        ).sum()
    )

    incorrect = int(
        (
            diagnoses["evaluation"]
            == "Incorrect"
        ).sum()
    )

    unavailable = int(
        (
            diagnoses["evaluation"]
            == "AI_UNAVAILABLE"
        ).sum()
    )


# =========================================================
# TOP METRICS
# =========================================================

st.markdown(
    "### Project Overview"
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Total Cases",
        total_cases
    )

with col2:

    st.metric(
        "AI Diagnosed",
        ai_diagnosed
    )

with col3:

    st.metric(
        "Correct",
        correct
    )

with col4:

    st.metric(
        "AI Unavailable",
        unavailable
    )


st.divider()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "Case Selection"
)

categories = sorted(
    cases["category"]
    .dropna()
    .unique()
    .tolist()
)

selected_category = st.sidebar.selectbox(
    "Filter by category",
    ["All"] + categories
)


if selected_category == "All":

    filtered_cases = cases

else:

    filtered_cases = cases[
        cases["category"]
        == selected_category
    ]


case_ids = (
    filtered_cases["case_id"]
    .astype(str)
    .tolist()
)

if not case_ids:

    st.warning(
        "No cases available for this category."
    )

    st.stop()


selected_case_id = st.sidebar.selectbox(
    "Select case",
    case_ids
)


# =========================================================
# SELECT CASE
# =========================================================

case = cases[
    cases["case_id"].astype(str)
    == selected_case_id
].iloc[0]


# =========================================================
# CASE INFORMATION
# =========================================================

st.markdown(
    "### Case Information"
)

col1, col2, col3 = st.columns(3)

with col1:

    st.write("**Case ID**")

    st.write(
        case["case_id"]
    )

with col2:

    st.write("**Category**")

    st.write(
        case["category"]
    )

with col3:

    st.write("**Severity**")

    st.write(
        case["severity"]
    )


st.write("**Symptom**")

st.info(
    case["symptom"]
)


st.write("**Topology**")

st.write(
    case["topology_note"]
)


# =========================================================
# CISCO EVIDENCE
# =========================================================

st.markdown(
    "### Cisco Evidence"
)

st.code(
    str(case["show_outputs"]),
    language="text"
)


# =========================================================
# RULE CHECKER
# =========================================================

st.markdown(
    "### Deterministic Rule Checker"
)

rule_match = rules[
    rules["case_id"].astype(str)
    == selected_case_id
]


if rule_match.empty:

    st.success(
        "No deterministic rule violation detected."
    )

else:

    finding = rule_match.iloc[0][
        "rule_findings"
    ]

    if pd.isna(finding) or not str(
        finding
    ).strip():

        st.success(
            "No deterministic rule violation detected."
        )

    else:

        st.warning(
            str(finding)
        )


# =========================================================
# AI DIAGNOSIS
# =========================================================

st.markdown(
    "### AI Diagnosis"
)

if diagnoses.empty:

    st.info(
        "AI diagnosis is not available yet. "
        "Run the diagnosis engine after the "
        "Gemini quota becomes available."
    )

    ai_row = None

else:

    diagnosis_match = diagnoses[
        diagnoses["case_id"].astype(str)
        == selected_case_id
    ]

    if diagnosis_match.empty:

        st.info(
            "This case has not been diagnosed by AI yet."
        )

        ai_row = None

    else:

        ai_row = diagnosis_match.iloc[0]


if ai_row is not None:

    evaluation = ai_row.get(
        "evaluation",
        ""
    )

    if evaluation == "AI_UNAVAILABLE":

        st.warning(
            "Gemini was unavailable for this case. "
            "Human review is required."
        )

    else:

        st.write(
            "**Root Cause**"
        )

        st.info(
            str(
                ai_row["root_cause"]
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                "**Confidence**"
            )

            confidence = str(
                ai_row["confidence"]
            )

            if confidence.lower() == "high":

                st.success(
                    confidence
                )

            elif confidence.lower() == "medium":

                st.warning(
                    confidence
                )

            else:

                st.error(
                    confidence
                )

        with col2:

            st.write(
                "**OSI Layer**"
            )

            st.write(
                ai_row["osi_layer"]
            )

        # -------------------------------------------------
        # Evidence
        # -------------------------------------------------

        st.write(
            "**AI Evidence**"
        )

        evidence = str(
            ai_row["evidence"]
        )

        for item in evidence.split(" | "):

            st.write(
                "• " + item
            )

        # -------------------------------------------------
        # Commands
        # -------------------------------------------------

        st.write(
            "**Recommended Next Command(s)**"
        )

        commands = str(
            ai_row["next_command"]
        )

        for command in commands.split(
            " | "
        ):

            st.code(
                command,
                language="text"
            )

        # -------------------------------------------------
        # Fix
        # -------------------------------------------------

        st.write(
            "**Recommended Fix Steps**"
        )

        fix_steps = str(
            ai_row["fix_steps"]
        )

        for step in fix_steps.split(
            " | "
        ):

            st.write(
                "• " + step
            )

        # -------------------------------------------------
        # Evaluation
        # -------------------------------------------------

        st.write(
            "**Evaluation**"
        )

        if evaluation == "Correct":

            st.success(
                "AI diagnosis matches the expected fault."
            )

        elif evaluation == "Incorrect":

            st.error(
                "AI diagnosis does not match "
                "the expected fault."
            )


# =========================================================
# EXPECTED ANSWER
# =========================================================

with st.expander(
    "Show expected answer"
):

    st.write(
        "**Expected Fault**"
    )

    st.write(
        case["expected_fault"]
    )

    st.write(
        "**Expected Next Command**"
    )

    st.code(
        str(
            case["expected_next_command"]
        ),
        language="text"
    )

    st.write(
        "**Expected Fix**"
    )

    st.write(
        case["expected_fix"]
    )


# =========================================================
# HUMAN REVIEW
# =========================================================

st.divider()

st.markdown(
    "### Human Review"
)

st.write(
    "AI output must be reviewed by a human "
    "before any network configuration change."
)


with st.form(
    key=f"review_form_{selected_case_id}"
):

    decision = st.radio(
        "Review decision",
        [
            "ACCEPTED",
            "EDITED",
            "REJECTED"
        ],
        horizontal=True
    )

    corrected_diagnosis = st.text_area(
        "Corrected diagnosis "
        "(required when editing)",
        value=""
    )

    reviewer_reason = st.text_area(
        "Reviewer reason",
        value=""
    )

    submitted = st.form_submit_button(
        "Save Human Review"
    )

    if submitted:

        if decision == "EDITED" and not (
            corrected_diagnosis.strip()
        ):

            st.error(
                "Please provide a corrected "
                "diagnosis for an EDITED decision."
            )

        else:

            new_review = pd.DataFrame([
                {

                    "case_id":
                        selected_case_id,

                    "decision":
                        decision,

                    "corrected_diagnosis":
                        corrected_diagnosis,

                    "reviewer_reason":
                        reviewer_reason
                }
            ])

            existing_reviews = load_reviews()

            # Remove old review for same case
            existing_reviews = (
                existing_reviews[
                    existing_reviews["case_id"].astype(str)
                    != selected_case_id
                ]
            )

            updated_reviews = pd.concat(
                [
                    existing_reviews,
                    new_review
                ],
                ignore_index=True
            )

            updated_reviews.to_csv(
                REVIEW_FILE,
                index=False
            )

            st.success(
                "Human review saved successfully."
            )

            st.cache_data.clear()


# =========================================================
# REVIEW HISTORY
# =========================================================

st.divider()

st.markdown(
    "### Human Review History"
)

reviews = load_reviews()

if reviews.empty:

    st.info(
        "No human reviews have been recorded yet."
    )

else:

    st.dataframe(
        reviews,
        width="stretch",
        hide_index=True
    )


# =========================================================
# PROJECT INFORMATION
# =========================================================

st.divider()

with st.expander(
    "About NetSage AI"
):

    st.write(
        """
        NetSage AI is a hybrid AI-assisted network
        troubleshooting system.

        It combines:

        • Deterministic configuration checks
        • Cisco show-command evidence
        • Generative AI diagnosis
        • Confidence reporting
        • Human-in-the-loop review
        • Transparent evaluation

        The system does not automatically apply
        network configuration changes.
        """
    )