"""
NetSage AI - Evaluation Engine

Evaluates AI diagnosis results against the known
expected faults.

This module does NOT call Gemini.

It works entirely from saved CSV files.
"""

from pathlib import Path

import pandas as pd


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DIAGNOSES_FILE = DATA_DIR / "diagnoses.csv"

CASES_FILE = DATA_DIR / "cases.csv"

OUTPUT_FILE = DATA_DIR / "evaluation_report.csv"


# =========================================================
# LOAD DATA
# =========================================================

def load_diagnoses():

    if not DIAGNOSES_FILE.exists():

        raise FileNotFoundError(
            "diagnoses.csv does not exist yet.\n"
            "Run the diagnosis engine after the "
            "Gemini quota becomes available."
        )

    try:

        df = pd.read_csv(
            DIAGNOSES_FILE
        )

    except pd.errors.EmptyDataError:

        raise RuntimeError(
            "diagnoses.csv is empty."
        )

    if df.empty:

        raise RuntimeError(
            "diagnoses.csv contains no records."
        )

    return df


def load_cases():

    if not CASES_FILE.exists():

        raise FileNotFoundError(
            f"Cases file not found: {CASES_FILE}"
        )

    return pd.read_csv(
        CASES_FILE
    )


# =========================================================
# OVERALL METRICS
# =========================================================

def calculate_overall_metrics(df):

    total = len(df)

    correct = int(
        (df["evaluation"] == "Correct")
        .sum()
    )

    incorrect = int(
        (df["evaluation"] == "Incorrect")
        .sum()
    )

    unavailable = int(
        (df["evaluation"] == "AI_UNAVAILABLE")
        .sum()
    )

    errors = int(
        (df["evaluation"] == "Error")
        .sum()
    )

    evaluated = correct + incorrect

    if evaluated > 0:

        accuracy = (
            correct / evaluated
        ) * 100

    else:

        accuracy = 0.0

    return {

        "total_cases":
            total,

        "correct":
            correct,

        "incorrect":
            incorrect,

        "ai_unavailable":
            unavailable,

        "errors":
            errors,

        "evaluated_cases":
            evaluated,

        "accuracy_percent":
            round(
                accuracy,
                2
            )
    }


# =========================================================
# CATEGORY METRICS
# =========================================================

def calculate_category_metrics(df):

    rows = []

    for category, group in (
        df.groupby("category")
    ):

        correct = int(
            (
                group["evaluation"]
                == "Correct"
            ).sum()
        )

        incorrect = int(
            (
                group["evaluation"]
                == "Incorrect"
            ).sum()
        )

        unavailable = int(
            (
                group["evaluation"]
                == "AI_UNAVAILABLE"
            ).sum()
        )

        evaluated = (
            correct + incorrect
        )

        if evaluated > 0:

            accuracy = (
                correct / evaluated
            ) * 100

        else:

            accuracy = 0.0

        rows.append({

            "category":
                category,

            "total_cases":
                len(group),

            "correct":
                correct,

            "incorrect":
                incorrect,

            "ai_unavailable":
                unavailable,

            "accuracy_percent":
                round(
                    accuracy,
                    2
                )
        })

    return pd.DataFrame(
        rows
    )


# =========================================================
# CONFIDENCE METRICS
# =========================================================

def calculate_confidence_metrics(df):

    confidence = (
        df["confidence"]
        .fillna("Unknown")
        .value_counts()
        .reset_index()
    )

    confidence.columns = [
        "confidence",
        "count"
    ]

    return confidence


# =========================================================
# RULE CHECKER SUMMARY
# =========================================================

def calculate_rule_summary(df):

    rule_df = df[
        df["rule_findings"]
        .fillna("")
        .str.strip()
        != ""
    ]

    return {

        "cases_with_rule_findings":
            len(rule_df),

        "cases_without_rule_findings":
            len(df) - len(rule_df)
    }


# =========================================================
# HUMAN REVIEW SUMMARY
# =========================================================

def calculate_review_summary(df):

    if "human_review_required" not in df:

        return {

            "human_review_required":
                0,

            "human_review_not_required":
                len(df)
        }

    review_required = int(
        (
            df["human_review_required"]
            .astype(str)
            .str.lower()
            == "true"
        ).sum()
    )

    return {

        "human_review_required":
            review_required,

        "human_review_not_required":
            len(df) - review_required
    }


# =========================================================
# BUILD REPORT
# =========================================================

def build_report():

    print("=" * 70)
    print(
        "NetSage AI - Evaluation Engine"
    )
    print("=" * 70)

    df = load_diagnoses()

    print(
        f"\nDiagnosis records loaded: "
        f"{len(df)}"
    )

    # -----------------------------------------------------
    # Overall
    # -----------------------------------------------------

    overall = (
        calculate_overall_metrics(df)
    )

    print(
        "\nOVERALL RESULTS"
    )

    print(
        "-" * 40
    )

    for key, value in overall.items():

        print(
            f"{key}: {value}"
        )

    # -----------------------------------------------------
    # Category
    # -----------------------------------------------------

    category_df = (
        calculate_category_metrics(df)
    )

    print(
        "\nCATEGORY PERFORMANCE"
    )

    print(
        category_df.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    confidence_df = (
        calculate_confidence_metrics(df)
    )

    print(
        "\nCONFIDENCE DISTRIBUTION"
    )

    print(
        confidence_df.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # Rule summary
    # -----------------------------------------------------

    rule_summary = (
        calculate_rule_summary(df)
    )

    print(
        "\nRULE CHECKER"
    )

    for key, value in (
        rule_summary.items()
    ):

        print(
            f"{key}: {value}"
        )

    # -----------------------------------------------------
    # Human review
    # -----------------------------------------------------

    review_summary = (
        calculate_review_summary(df)
    )

    print(
        "\nHUMAN REVIEW"
    )

    for key, value in (
        review_summary.items()
    ):

        print(
            f"{key}: {value}"
        )

    # -----------------------------------------------------
    # Save category report
    # -----------------------------------------------------

    category_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "\nCategory evaluation saved to:"
    )

    print(
        OUTPUT_FILE
    )

    # -----------------------------------------------------
    # Save detailed text report
    # -----------------------------------------------------

    text_report = (
        DATA_DIR
        / "evaluation_summary.txt"
    )

    with open(
        text_report,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "NetSage AI Evaluation Report\n"
        )

        file.write(
            "=" * 50
            + "\n\n"
        )

        file.write(
            "Overall Results\n"
        )

        file.write(
            "-" * 30
            + "\n"
        )

        for key, value in (
            overall.items()
        ):

            file.write(
                f"{key}: {value}\n"
            )

        file.write(
            "\n\nCategory Performance\n"
        )

        file.write(
            category_df.to_string(
                index=False
            )
        )

        file.write(
            "\n\nConfidence Distribution\n"
        )

        file.write(
            confidence_df.to_string(
                index=False
            )
        )

        file.write(
            "\n\nRule Checker Summary\n"
        )

        for key, value in (
            rule_summary.items()
        ):

            file.write(
                f"{key}: {value}\n"
            )

        file.write(
            "\n\nHuman Review Summary\n"
        )

        for key, value in (
            review_summary.items()
        ):

            file.write(
                f"{key}: {value}\n"
            )

    print(
        "\nDetailed report saved to:"
    )

    print(
        text_report
    )

    print(
        "\nEvaluation complete."
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    build_report()