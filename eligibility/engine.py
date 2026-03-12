# eligibility/engine.py
from __future__ import annotations
from typing import Callable, Dict, Any, List

RuleFn = Callable[[dict], Dict[str, Any]]


def _dedup_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def run_rules(patient: dict, rules: List[RuleFn], stop_on_first_not_eligible: bool = True) -> Dict[str, Any]:
    """
    跑一组规则并汇总：
      - 任一 NOT_ELIGIBLE => 最终 NOT_ELIGIBLE（默认遇到第一个就停止）
      - 否则任一 UNCERTAIN => 最终 UNCERTAIN（合并 missing）
      - 全 PASS => PASS
    返回：
      verdict: PASS / UNCERTAIN / NOT_ELIGIBLE
      reason: 汇总原因
      missing: 缺失字段列表
      details: 每条规则结果（便于调试）
    """
    details: List[Dict[str, Any]] = []
    missing: List[str] = []
    final_verdict = "PASS"
    reasons: List[str] = []

    for rule in rules:
        r = rule(patient)
        details.append(r)

        v = r.get("verdict")
        if v == "NOT_ELIGIBLE":
            final_verdict = "NOT_ELIGIBLE"
            reasons.append(r.get("reason", "Excluded"))
            if stop_on_first_not_eligible:
                break

        elif v == "UNCERTAIN":
            if final_verdict != "NOT_ELIGIBLE":
                final_verdict = "UNCERTAIN"
            missing.extend(r.get("missing", []))

        else:
            # PASS：不改变 final_verdict
            pass

    missing = _dedup_keep_order(missing)

    if final_verdict == "NOT_ELIGIBLE":
        reason = "; ".join(reasons) if reasons else "Excluded by rule(s)"
    elif final_verdict == "UNCERTAIN":
        reason = "Missing required field(s) for screening"
    else:
        reason = "Passed all implemented rules (not final eligibility)"

    return {
        "verdict": final_verdict,
        "reason": reason,
        "missing": missing,
        "details": details,
    }