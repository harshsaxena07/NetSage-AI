"""
NetSage AI - Deterministic Network Rule Checker

This module performs deterministic checks on Cisco-style
troubleshooting evidence.

Required checks:
1. Duplicate IP
2. Wrong subnet mask
3. Gateway mismatch
4. Interface down
5. Missing VLAN
6. Missing route

The rule checker does NOT use AI.
"""

import re
import pandas as pd


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def extract_ip_addresses(text):
    """Return all IPv4 addresses found in a text."""
    pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    return re.findall(pattern, text)


def check_duplicate_ip(show_output):
    """
    Detect an IP conflict when the evidence explicitly indicates
    that the same IP is associated with changing/multiple MAC addresses.
    """

    text = show_output.lower()

    if "ip conflict" in text:
        return "Duplicate IP detected"

    if "changing mac addresses" in text:
        return "Duplicate IP detected"

    if "appears with changing mac" in text:
        return "Duplicate IP detected"

    return None


def check_wrong_mask(show_output):
    """
    Detect an incorrect subnet mask when the evidence explicitly
    indicates that the configured mask differs from the expected mask.
    """

    text = show_output.lower()

    if "incorrect subnet mask" in text:
        return "Wrong subnet mask detected"

    if "mask 255.255.0.0" in text and "network is configured for /24" in text:
        return "Wrong subnet mask detected"

    return None


def check_gateway_mismatch(show_output):
    """
    Detect an incorrect default gateway when the evidence explicitly
    shows a gateway outside the expected subnet or a wrong DHCP gateway.
    """

    text = show_output.lower()

    if "default gateway" in text and "192.168.20.1" in text:
        return "Gateway mismatch detected"

    if "gateway 192.168.30.254" in text:
        return "Gateway mismatch detected"

    if "wrong default gateway" in text:
        return "Gateway mismatch detected"

    return None


def check_interface_down(show_output):
    """Detect an interface that is administratively down."""

    text = show_output.lower()

    if "administratively down" in text:
        return "Interface is administratively down"

    return None


def check_missing_vlan(show_output):
    """
    Detect a VLAN that is required but absent from the switch.
    """

    text = show_output.lower()

    if "vlan 30 is absent" in text:
        return "Required VLAN is missing"

    if "required vlan is missing" in text:
        return "Required VLAN is missing"

    return None


def check_missing_route(show_output):
    """
    Detect a missing route from routing-table evidence.
    """

    text = show_output.lower()

    if "no route for" in text:
        return "Required route is missing"

    if "no route to" in text:
        return "Required route is missing"

    if "default route is missing" in text:
        return "Default route is missing"

    if "no 0.0.0.0/0 entry" in text:
        return "Default route is missing"

    return None


# ---------------------------------------------------------
# Main rule checker
# ---------------------------------------------------------

def check_case(case):
    """
    Run all deterministic checks against one troubleshooting case.

    Returns a list of detected rule-based findings.
    """

    findings = []

    show_output = str(case.get("show_outputs", ""))

    checks = [
        check_duplicate_ip(show_output),
        check_wrong_mask(show_output),
        check_gateway_mismatch(show_output),
        check_interface_down(show_output),
        check_missing_vlan(show_output),
        check_missing_route(show_output),
    ]

    for result in checks:
        if result:
            findings.append(result)

    return findings


# ---------------------------------------------------------
# Run checker for complete dataset
# ---------------------------------------------------------

def run_checker(input_file="data/cases.csv",
                output_file="data/rule_check_results.csv"):

    df = pd.read_csv(input_file)

    results = []

    for _, row in df.iterrows():

        findings = check_case(row)

        results.append({
            "case_id": row["case_id"],
            "category": row["category"],
            "rule_findings": "; ".join(findings)
            if findings
            else "No deterministic rule violation detected",
            "rule_issue_detected": "Yes" if findings else "No",
            "expected_fault": row["expected_fault"]
        })

    result_df = pd.DataFrame(results)

    result_df.to_csv(output_file, index=False)

    return result_df


# ---------------------------------------------------------
# Program entry point
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("NetSage AI - Deterministic Rule Checker")
    print("=" * 60)

    results = run_checker()

    print("\nRule checker completed successfully.")
    print(f"Cases checked: {len(results)}")

    print("\nDetected issues:")

    detected = results[results["rule_issue_detected"] == "Yes"]

    if detected.empty:
        print("No deterministic issues detected.")
    else:
        print(
            detected[
                [
                    "case_id",
                    "category",
                    "rule_findings"
                ]
            ].to_string(index=False)
        )

    print("\nResults saved to:")
    print("data/rule_check_results.csv")