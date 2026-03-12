# Phase III Eligibility Prescreen Engine

A rule-based clinical trial prescreening proof of concept for oncology eligibility assessment.

This project converts protocol-style eligibility criteria into executable rules and returns an auditable prescreen result: **PASS**, **NOT_ELIGIBLE**, or **UNCERTAIN**. It is designed as a lightweight, explainable screening engine rather than a black-box classifier.

## Overview

Clinical trial prescreening is often slow, manual, and difficult to audit. Eligibility criteria are written in protocol language, while patient information is incomplete, scattered, or unstructured.

This project is a practical PoC that demonstrates how protocol logic can be operationalized into a structured rule engine.

Given a patient record, the engine:

- evaluates implemented eligibility rules one by one,
- returns a tri-state verdict,
- explains which rules passed or failed,
- highlights missing fields that prevent confident screening.

The current version focuses on **high-yield prescreen rules** rather than full protocol coverage.

## Why I built this

I wanted to turn a real-world screening workflow into something:

- **structured**: criteria become explicit rules rather than vague text,
- **testable**: each rule can be validated independently,
- **explainable**: every verdict has a reason,
- **extensible**: new rules can be added without rewriting the engine.

This project reflects how I think about product and operations problems in regulated settings: break down ambiguous requirements, define decision logic, handle uncertainty explicitly, and keep the output reviewable by humans.

## What the engine does

For each patient input, the engine outputs:

- a **final verdict**
  - `PASS`
  - `NOT_ELIGIBLE`
  - `UNCERTAIN`
- a **summary reason**
- a list of **missing fields**
- a rule-by-rule **details** section for audit and review

Example output:

```python
{
  "verdict": "PASS",
  "reason": "Passed all implemented rules (not final eligibility)",
  "missing": [],
  "details": [
    {
      "rule_id": "R6_measurable_disease",
      "verdict": "PASS",
      "reason": "Measurable disease (serum M-protein 1.10 g/dL >= 1.0)",
      "missing": []
    },
    {
      "rule_id": "R7_prior_PI_len_PRplus",
      "verdict": "PASS",
      "reason": "Meets prior exposure and response requirement",
      "missing": []
    }
  ]
}
