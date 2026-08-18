import pandas as pd

from diagnosis import (
    load_prompt,
    load_data,
    diagnose_case,
)


cases, rule_results = load_data()

case = cases[
    cases["case_id"] == "C017"
].iloc[0]

rule_result = rule_results[
    rule_results["case_id"] == "C017"
].iloc[0].to_dict()

prompt = load_prompt()

print("=" * 70)
print("Testing NetSage AI Diagnosis")
print("=" * 70)

print("\nCase:")
print(case["case_id"])

print("\nSymptom:")
print(case["symptom"])

print("\nRule findings:")
print(rule_result["rule_findings"])

print("\nCalling Gemini...\n")

result = diagnose_case(
    case,
    rule_result,
    prompt
)

print("=" * 70)
print("AI DIAGNOSIS")
print("=" * 70)

print("\nRoot Cause:")
print(result.root_cause)

print("\nConfidence:")
print(result.confidence)

print("\nEvidence:")

for item in result.evidence:
    print("-", item)

print("\nOSI Layer:")
print(result.osi_layer)

print("\nNext Command:")

for command in result.next_command:
    print("-", command)

print("\nFix Steps:")

for step in result.fix_steps:
    print("-", step)

print("\nHuman Review Required:")
print(result.human_review_required)