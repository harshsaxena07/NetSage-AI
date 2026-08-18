# NetSage AI - Responsible AI Log

## 1. Project Overview

NetSage AI is an AI-assisted Cisco network troubleshooting system.

The system analyzes network troubleshooting cases using:

- Reported network symptoms
- Network topology information
- Cisco show-command outputs
- Deterministic rule-checking results
- Generative AI reasoning

The purpose of the system is to assist a network engineer during troubleshooting.

NetSage AI does NOT automatically apply configuration changes to network devices.

---

# 2. Human-in-the-Loop Design

Human review is mandatory before any network configuration change.

The AI provides:

- Root cause hypothesis
- Confidence level
- Supporting evidence
- OSI layer
- Recommended Cisco commands
- Suggested troubleshooting/fix steps

A human network engineer must review the recommendation before taking action.

The dashboard provides three review decisions:

- ACCEPTED
- EDITED
- REJECTED

Human review decisions are stored in:

data/human_review.csv

This provides an audit trail of human decisions.

---

# 3. Evidence-Based Diagnosis

The AI is instructed to base its diagnosis only on the supplied evidence.

Evidence includes:

1. Reported symptom
2. Network topology
3. Cisco show-command output
4. Deterministic rule-checking findings

The system instructs the AI not to invent:

- IP addresses
- VLANs
- Routes
- ACL entries
- Interfaces
- Devices
- Cisco command output
- Configuration details

When evidence is incomplete, the AI should reduce its confidence.

---

# 4. Deterministic Rule Checker

NetSage AI does not depend entirely on generative AI.

A deterministic rule checker is used to identify known configuration problems.

Examples include:

- Missing VLAN
- Gateway mismatch
- Administratively down interface
- Duplicate IP address
- Incorrect subnet mask
- Missing DHCP gateway
- Missing route
- Missing default route

The deterministic checker provides an additional source of evidence for the AI diagnosis.

This hybrid approach improves transparency because the AI recommendation can be compared with deterministic findings.

---

# 5. Confidence Reporting

The AI diagnosis contains a confidence level:

- High
- Medium
- Low

Confidence is used to communicate how strongly the available evidence supports the diagnosis.

Confidence is not treated as proof of correctness.

A high-confidence AI recommendation still requires human review.

---

# 6. AI Failure Handling

NetSage AI depends on an external generative AI service.

The system therefore handles situations where the AI service is unavailable.

Possible causes include:

- Temporary service unavailability
- API quota exhaustion
- Rate limits
- Network/API errors

When Gemini is unavailable, the system does NOT fabricate an AI diagnosis.

Instead, it records:

AI_UNAVAILABLE

The system preserves the deterministic rule-checking evidence and marks the case for human review.

This is an example of graceful degradation.

---

# 7. API Quota Failure Observed During Development

During development, Gemini temporarily returned API availability/quota errors.

The system was modified so that an API failure does not terminate the complete diagnosis process.

The diagnosis engine now:

1. Attempts the AI diagnosis.
2. Records the result when successful.
3. Records AI_UNAVAILABLE when the AI service fails.
4. Saves progress after each case.
5. Allows previously completed cases to be skipped during future runs.

This prevents loss of previously processed cases.

---

# 8. No Automatic Network Changes

NetSage AI is an advisory system.

The system does not:

- Connect directly to Cisco devices
- Execute configuration commands
- Automatically change routing
- Automatically modify VLANs
- Automatically modify ACLs
- Automatically change NAT
- Automatically change DHCP configuration

The AI only recommends troubleshooting actions.

A qualified human must decide whether and how to apply a recommendation.

---

# 9. Human Review Audit Trail

Every human review is stored in:

data/human_review.csv

The review record contains:

- Case ID
- Review decision
- Corrected diagnosis
- Reviewer reason

This allows the project to maintain a basic audit trail.

---

# 10. Corrected AI Outputs

When an AI recommendation is found to be incorrect or incomplete, a human reviewer can select:

EDITED

and provide a corrected diagnosis.

The corrected diagnosis is stored with the review record.

This creates a mechanism for identifying and documenting AI errors.

At least five cases should be reviewed and corrected during final evaluation where the AI output requires correction.

---

# 11. Privacy Considerations

Network troubleshooting information may contain sensitive infrastructure information.

Examples include:

- IP addresses
- Device names
- Network topology
- Interface information
- Routing information
- Access-control information

The system should therefore avoid sending unnecessary sensitive information to external AI services.

For real production deployment:

- Sensitive infrastructure data should be sanitized where possible.
- API credentials must not be committed to source control.
- The .env file must remain private.
- Logs should not expose secrets.
- Production network configurations should not be shared unnecessarily.

---

# 12. API Key Security

The Gemini API key is stored using an environment variable:

GEMINI_API_KEY

The project uses a .env file during local development.

The API key must NOT be:

- Hard-coded into Python files
- Committed to Git
- Included in README files
- Included in screenshots
- Shared publicly

A .gitignore file should exclude:

.env

---

# 13. Limitations

NetSage AI has several limitations.

### AI limitations

Generative AI can:

- Misinterpret evidence
- Produce incorrect diagnoses
- Overlook relevant configuration details
- Generate plausible but incorrect explanations

Therefore AI output must not be treated as authoritative.

### Dataset limitations

The project uses a finite set of troubleshooting cases.

The results therefore do not represent every possible Cisco networking problem.

### External service limitations

Gemini availability and quota can affect AI diagnosis.

The system handles this by recording AI_UNAVAILABLE instead of fabricating results.

### Rule checker limitations

The deterministic checker only identifies problems represented by its implemented rules.

A problem not covered by a rule may remain undetected.

---

# 14. Responsible AI Principles Applied

NetSage AI follows these principles:

## Human Oversight

A human must review AI recommendations before network changes.

## Transparency

The system displays evidence, confidence, rule findings, and recommended actions.

## Reliability

The system handles AI/API failures rather than silently generating unsupported answers.

## Accountability

Human review decisions are stored for auditing.

## Safety

The system does not automatically modify network infrastructure.

## Privacy

API credentials and sensitive infrastructure information should be protected.

## Limitations Awareness

The system clearly distinguishes AI assistance from authoritative network engineering decisions.

---

# 15. Final Safety Principle

NetSage AI is an assistant, not an autonomous network administrator.

The final responsibility for a network configuration decision remains with the human network engineer.

AI recommendations should always be validated against the actual network state before implementation.