"""
NetSage AI - AI Diagnosis Engine

This module:
1. Loads troubleshooting cases.
2. Loads the diagnosis prompt.
3. Loads deterministic rule-check results.
4. Sends evidence to Gemini.
5. Receives structured JSON.
6. Validates the AI response.
7. Compares AI diagnosis with the expected fault.
8. Saves progress after EVERY case.
9. Can resume from previous results.
10. Handles Gemini 503/429 errors safely.
11. Never fabricates an AI diagnosis when Gemini is unavailable.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

PROMPT_FILE = (
    BASE_DIR
    / "prompts"
    / "diagnose_prompt.md"
)

CASES_FILE = (
    DATA_DIR
    / "cases.csv"
)

RULE_RESULTS_FILE = (
    DATA_DIR
    / "rule_check_results.csv"
)

OUTPUT_FILE = (
    DATA_DIR
    / "diagnoses.csv"
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv(BASE_DIR / ".env", override=True)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Check the .env file."
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=API_KEY
)

MODEL_NAME = "gemini-3.5-flash"


# =========================================================
# STRUCTURED AI RESPONSE
# =========================================================

class DiagnosisResult(BaseModel):

    root_cause: str = Field(
        description=(
            "Most likely network root cause."
        )
    )

    confidence: str = Field(
        description=(
            "Confidence level: High, Medium, or Low."
        )
    )

    evidence: list[str] = Field(
        description=(
            "Evidence taken directly from "
            "the supplied case."
        )
    )

    osi_layer: str = Field(
        description=(
            "Primary OSI layer involved."
        )
    )

    next_command: list[str] = Field(
        description=(
            "Cisco commands that should "
            "be used next."
        )
    )

    fix_steps: list[str] = Field(
        description=(
            "Ordered troubleshooting or "
            "remediation steps."
        )
    )

    human_review_required: bool = Field(
        description=(
            "Must always be true."
        )
    )


# =========================================================
# LOAD PROMPT
# =========================================================

def load_prompt():

    if not PROMPT_FILE.exists():

        raise FileNotFoundError(
            f"Prompt file not found: "
            f"{PROMPT_FILE}"
        )

    return PROMPT_FILE.read_text(
        encoding="utf-8"
    )


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    if not CASES_FILE.exists():

        raise FileNotFoundError(
            f"Cases file not found: "
            f"{CASES_FILE}"
        )

    if not RULE_RESULTS_FILE.exists():

        raise FileNotFoundError(
            f"Rule checker results not found: "
            f"{RULE_RESULTS_FILE}"
        )

    cases = pd.read_csv(
        CASES_FILE
    )

    rule_results = pd.read_csv(
        RULE_RESULTS_FILE
    )

    return cases, rule_results


# =========================================================
# BUILD CASE PROMPT
# =========================================================

def build_case_prompt(
    case,
    rule_result,
    system_prompt
):

    rule_findings = rule_result.get(
        "rule_findings",
        "No deterministic rule violation detected"
    )

    return f"""
{system_prompt}

# CASE TO DIAGNOSE

Case ID:
{case["case_id"]}

Category:
{case["category"]}

Severity:
{case["severity"]}

Symptom:
{case["symptom"]}

Topology:
{case["topology_note"]}

Cisco Show-Command Evidence:
{case["show_outputs"]}

Deterministic Rule Checker Findings:
{rule_findings}

# IMPORTANT INSTRUCTIONS

Analyze the supplied evidence carefully.

Your diagnosis must be based ONLY on:

1. Symptom
2. Topology
3. Cisco evidence
4. Deterministic rule findings

Every evidence item must be supported by
the supplied case.

Do not invent:

- Cisco command output
- IP addresses
- VLANs
- routes
- ACL entries
- interfaces
- network devices
- configuration

If the evidence is incomplete, lower the confidence.

human_review_required MUST be true.

Return ONLY the required structured JSON response.
"""


# =========================================================
# DIAGNOSE ONE CASE
# =========================================================

def diagnose_case(
    case,
    rule_result,
    system_prompt
):

    prompt = build_case_prompt(
        case,
        rule_result,
        system_prompt
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type":
                "application/json",

            "response_json_schema":
                DiagnosisResult.model_json_schema(),
        },
    )

    result = DiagnosisResult.model_validate_json(
        response.text
    )

    return result


# =========================================================
# COMPARE AI WITH EXPECTED ANSWER
# =========================================================

def compare_with_expected(
    ai_result,
    expected_fault
):

    ai_text = (
        ai_result.root_cause
        .lower()
    )

    expected_text = (
        str(expected_fault)
        .lower()
    )

    keywords = []

    if "vlan" in expected_text:
        keywords.append("vlan")

    if "gateway" in expected_text:
        keywords.append("gateway")

    if "dhcp" in expected_text:
        keywords.append("dhcp")

    if "dns" in expected_text:
        keywords.append("dns")

    if "route" in expected_text:
        keywords.append("route")

    if "acl" in expected_text:
        keywords.append("acl")

    if "nat" in expected_text:
        keywords.append("nat")

    if "wireless" in expected_text:
        keywords.append("wireless")

    matched = any(
        keyword in ai_text
        for keyword in keywords
    )

    if matched:

        return "Correct"

    return "Incorrect"


# =========================================================
# FIND EXISTING SUCCESSFUL RESULTS
# =========================================================

def load_existing_results():

    if not OUTPUT_FILE.exists():

        return [], set()

    try:

        existing_df = pd.read_csv(
            OUTPUT_FILE
        )

    except pd.errors.EmptyDataError:

        return [], set()

    except Exception as error:

        print(
            "Warning: Could not read existing "
            f"diagnoses.csv: {error}"
        )

        return [], set()

    if existing_df.empty:

        return [], set()

    results = (
        existing_df
        .to_dict("records")
    )

    # Only successfully diagnosed cases
    # are skipped.
    #
    # AI_UNAVAILABLE and Error cases will
    # be retried later.

    completed_ids = set(
        existing_df[
            existing_df["evaluation"]
            == "Correct"
        ]["case_id"]
        .astype(str)
    )

    # Also skip successfully diagnosed
    # incorrect cases because they are
    # still legitimate AI results that
    # should be evaluated/reviewed rather
    # than regenerated automatically.

    completed_ids.update(
        existing_df[
            existing_df["evaluation"]
            == "Incorrect"
        ]["case_id"]
        .astype(str)
    )

    return results, completed_ids


# =========================================================
# CREATE AI-UNAVAILABLE RECORD
# =========================================================

def create_unavailable_record(
    case,
    rule_result,
    error
):

    return {

        "case_id":
            str(case["case_id"]),

        "category":
            case["category"],

        "root_cause":
            "AI diagnosis unavailable",

        "confidence":
            "Low",

        "evidence":
            "Gemini API unavailable: "
            + str(error),

        "osi_layer":
            case["osi_layer"],

        "next_command":
            case["expected_next_command"],

        "fix_steps":
            case["expected_fix"],

        "human_review_required":
            True,

        "rule_findings":
            rule_result.get(
                "rule_findings",
                ""
            ),

        "expected_fault":
            case["expected_fault"],

        "evaluation":
            "AI_UNAVAILABLE"
    }


# =========================================================
# SAVE RESULTS
# =========================================================

def save_results(results):

    result_df = pd.DataFrame(
        results
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    return result_df


# =========================================================
# RUN ALL CASES
# =========================================================

def run_all_cases():

    print("=" * 70)
    print(
        "NetSage AI - AI Diagnosis Engine"
    )
    print("=" * 70)

    system_prompt = load_prompt()

    cases, rule_results = load_data()

    print(
        f"\nCases loaded: {len(cases)}"
    )

    # -----------------------------------------------------
    # Load previous progress
    # -----------------------------------------------------

    results, completed_ids = (
        load_existing_results()
    )

    if completed_ids:

        print(
            "\nExisting completed AI "
            f"diagnoses: {len(completed_ids)}"
        )

        print(
            "These cases will be skipped."
        )

    # -----------------------------------------------------
    # Process every case
    # -----------------------------------------------------

    for index, case in cases.iterrows():

        case_id = str(
            case["case_id"]
        )

        # -------------------------------------------------
        # Skip cases already diagnosed
        # -------------------------------------------------

        if case_id in completed_ids:

            print(
                f"\n[{index + 1}/"
                f"{len(cases)}] "
                f"{case_id} already completed "
                "- SKIPPING"
            )

            continue

        print(
            f"\n[{index + 1}/"
            f"{len(cases)}] "
            f"Diagnosing {case_id}..."
        )

        # -------------------------------------------------
        # Get rule checker result
        # -------------------------------------------------

        rule_match = rule_results[
            rule_results["case_id"]
            == case_id
        ]

        if rule_match.empty:

            rule_result = {

                "rule_findings":
                    "No deterministic rule "
                    "violation detected"
            }

        else:

            rule_result = (
                rule_match
                .iloc[0]
                .to_dict()
            )

        # -------------------------------------------------
        # Call Gemini
        # -------------------------------------------------

        try:

            ai_result = diagnose_case(
                case,
                rule_result,
                system_prompt
            )

            evaluation = (
                compare_with_expected(
                    ai_result,
                    case["expected_fault"]
                )
            )

            record = {

                "case_id":
                    case_id,

                "category":
                    case["category"],

                "root_cause":
                    ai_result.root_cause,

                "confidence":
                    ai_result.confidence,

                "evidence":
                    " | ".join(
                        ai_result.evidence
                    ),

                "osi_layer":
                    ai_result.osi_layer,

                "next_command":
                    " | ".join(
                        ai_result.next_command
                    ),

                "fix_steps":
                    " | ".join(
                        ai_result.fix_steps
                    ),

                "human_review_required":
                    ai_result.human_review_required,

                "rule_findings":
                    rule_result.get(
                        "rule_findings",
                        ""
                    ),

                "expected_fault":
                    case["expected_fault"],

                "evaluation":
                    evaluation
            }

            # Remove any previous failed
            # record for this same case.
            results = [
                item
                for item in results
                if str(item["case_id"])
                != case_id
            ]

            results.append(
                record
            )

            completed_ids.add(
                case_id
            )

            print(
                f"   Result: {evaluation}"
            )

        # -------------------------------------------------
        # Gemini unavailable / API error
        # -------------------------------------------------

        except Exception as error:

            error_text = str(error)

            print(
                "   AI unavailable:"
            )

            print(
                f"   {error_text}"
            )

            # We do NOT pretend this is
            # an AI diagnosis.
            #
            # Instead, save a transparent
            # AI_UNAVAILABLE record.

            unavailable_record = (
                create_unavailable_record(
                    case,
                    rule_result,
                    error_text
                )
            )

            # Remove an older unavailable
            # record for the same case.

            results = [
                item
                for item in results
                if str(item["case_id"])
                != case_id
            ]

            results.append(
                unavailable_record
            )

        # -------------------------------------------------
        # SAVE AFTER EVERY CASE
        # -------------------------------------------------

        result_df = save_results(
            results
        )

        print(
            f"   Progress saved: "
            f"{len(result_df)} cases"
        )

    # =====================================================
    # FINAL SUMMARY
    # =====================================================

    result_df = save_results(
        results
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "DIAGNOSIS PROCESS COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "\nResults saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nEvaluation summary:"
    )

    if not result_df.empty:

        print(
            result_df[
                "evaluation"
            ]
            .value_counts()
            .to_string()
        )

    print(
        "\nTotal saved cases:"
        f" {len(result_df)}"
    )

    return result_df


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    run_all_cases()