# eligibility/rules.py
from __future__ import annotations
from typing import Callable, Dict, Any

RuleResult = Dict[str, Any]

from datetime import date

def _parse_iso_date_yyyy_mm_dd(s) -> date | None:
    """Parse 'YYYY-MM-DD' into datetime.date; return None if invalid/missing."""
    if s is None:
        return None
    try:
        return date.fromisoformat(str(s).strip())
    except ValueError:
        return None

def rule_prior_anti_cd38(patient: dict) -> RuleResult:
    """
    第1条纳排规则：既往用过 anti-CD38 单抗 => 一票否决
    三态输出：NOT_ELIGIBLE / UNCERTAIN / PASS
    """
    prior = patient.get("prior_anti_cd38")  # True / False / None

    if prior is True:
        return {
            "rule_id": "R1_prior_anti_cd38",
            "verdict": "NOT_ELIGIBLE",
            "reason": "EXC: prior anti-CD38 therapy",
            "missing": [],
        }

    if prior is None:
        return {
            "rule_id": "R1_prior_anti_cd38",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": ["prior_anti_cd38 (是否用过抗CD38单抗)"],
        }

    return {
        "rule_id": "R1_prior_anti_cd38",
        "verdict": "PASS",
        "reason": "No prior anti-CD38 found",
        "missing": [],
    }


def rule_prior_pomalidomide(patient: dict) -> RuleResult:
    """
    第2条示例纳排规则：既往用过泊马度胺(pomalidomide) => 一票否决
    你后续可以按这个模板继续加 R3/R4...
    """
    prior = patient.get("prior_pomalidomide")  # True / False / None

    if prior is True:
        return {
            "rule_id": "R2_prior_pomalidomide",
            "verdict": "NOT_ELIGIBLE",
            "reason": "EXC: prior pomalidomide exposure",
            "missing": [],
        }

    if prior is None:
        return {
            "rule_id": "R2_prior_pomalidomide",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": ["prior_pomalidomide (是否用过泊马度胺)"],
        }

    return {
        "rule_id": "R2_prior_pomalidomide",
        "verdict": "PASS",
        "reason": "No prior pomalidomide found",
        "missing": [],
    }


def rule_ecog_le_2(patient: dict) -> RuleResult:
    """
    第3条示例纳排规则：ECOG <= 2 才通过；ECOG >= 3 一票否决
    缺失/无法解析 -> UNCERTAIN
    """
    raw = patient.get("ecog")  # 期望 int，也可能是字符串 "2" 或 None

    if raw is None:
        return {
            "rule_id": "R3_ecog_le_2",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": ["ecog (ECOG体能状态评分，0-4)"],
        }

    # 尝试把字符串转成整数
    try:
        ecog = int(raw)
    except (TypeError, ValueError):
        return {
            "rule_id": "R3_ecog_le_2",
            "verdict": "UNCERTAIN",
            "reason": "Invalid field type/value",
            "missing": ["ecog (ECOG体能状态评分，0-4)"],
        }

    if ecog >= 3:
        return {
            "rule_id": "R3_ecog_le_2",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"EXC: ECOG too high ({ecog})",
            "missing": [],
        }

    # ecog 为 0/1/2
    return {
        "rule_id": "R3_ecog_le_2",
        "verdict": "PASS",
        "reason": f"ECOG acceptable ({ecog})",
        "missing": [],
    }


def _to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _compute_crcl_cockcroft_gault(age_years: float, weight_kg: float, sex: str, scr_mg_dl: float) -> float | None:
    """
    Appendix 6 (Cockcroft–Gault):
    CrCl = (140 - age) * weight(kg) * (0.85 if female) / (72 * SCr[mg/dL])
    """
    if scr_mg_dl <= 0:
        return None
    sex_norm = (sex or "").strip().upper()
    female_factor = 0.85 if sex_norm in {"F", "FEMALE", "WOMAN"} else 1.0
    return (140.0 - age_years) * weight_kg * female_factor / (72.0 * scr_mg_dl)


def rule_crcl_ge_30(patient: dict) -> RuleResult:
    """
    R4 (APOLLO Inclusion 10g): Screening creatinine clearance (CrCl) >= 30 mL/min.
    Prefer direct crcl_ml_min; otherwise compute via Cockcroft–Gault (Appendix 6) if inputs exist.
    """
    # 1) 优先直接读取 CrCl
    raw_crcl = patient.get("crcl_ml_min")
    crcl = _to_float(raw_crcl)

    # 2) 如果没有 CrCl，尝试按 Appendix 6 计算
    if crcl is None:
        age = _to_float(patient.get("age_years"))
        wt = _to_float(patient.get("weight_kg"))
        sex = patient.get("sex")

        scr_mg_dl = _to_float(patient.get("scr_mg_dl"))
        if scr_mg_dl is None:
            # SI 单位 μmol/L 转 mg/dL：除以 88.4（Appendix 6）
            scr_umol_l = _to_float(patient.get("scr_umol_l"))
            if scr_umol_l is not None:
                scr_mg_dl = scr_umol_l / 88.4

        if age is not None and wt is not None and sex is not None and scr_mg_dl is not None:
            crcl = _compute_crcl_cockcroft_gault(age, wt, str(sex), scr_mg_dl)

    # 3) 仍然无法获得 CrCl → UNCERTAIN
    if crcl is None:
        return {
            "rule_id": "R4_crcl_ge_30",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": [
                "crcl_ml_min (筛选期CrCl，mL/min；APOLLO要求≥30)",
                "或用于计算：age_years, weight_kg, sex, scr_mg_dl/scr_umol_l",
            ],
        }

    # 4) 判定阈值
    if crcl < 30:
        return {
            "rule_id": "R4_crcl_ge_30",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"INC FAIL: CrCl < 30 mL/min ({crcl:.1f})",
            "missing": [],
        }

    return {
        "rule_id": "R4_crcl_ge_30",
        "verdict": "PASS",
        "reason": f"CrCl acceptable (>=30, {crcl:.1f})",
        "missing": [],
    }


def rule_washout_anti_myeloma_tx(patient: dict) -> RuleResult:
    """
    R5 (APOLLO Exclusion 3):
    Exclude if anti-myeloma treatment was received within 2 weeks OR within 5 PK half-lives
    (whichever is longer) prior to randomization.
    Exception: emergency short course corticosteroids (dexamethasone-equivalent 40 mg/day max 4 days)
    for palliative treatment before C1D1.
    """

    # ---- Exception path: emergency short steroid course ----
    if patient.get("emergency_short_steroid_course") is True:
        dex = patient.get("steroid_dex_equiv_mg_per_day")
        days = patient.get("steroid_course_days")

        if dex is None or days is None:
            return {
                "rule_id": "R5_washout_anti_myeloma_tx",
                "verdict": "UNCERTAIN",
                "reason": "Missing key field for steroid exception",
                "missing": [
                    "steroid_dex_equiv_mg_per_day (地塞米松当量 mg/day)",
                    "steroid_course_days (激素使用天数)",
                ],
            }

        try:
            dex_f = float(dex)
            days_i = int(days)
        except (TypeError, ValueError):
            return {
                "rule_id": "R5_washout_anti_myeloma_tx",
                "verdict": "UNCERTAIN",
                "reason": "Invalid field type/value for steroid exception",
                "missing": [
                    "steroid_dex_equiv_mg_per_day (地塞米松当量 mg/day)",
                    "steroid_course_days (激素使用天数)",
                ],
            }

        if dex_f <= 40 and days_i <= 4:
            return {
                "rule_id": "R5_washout_anti_myeloma_tx",
                "verdict": "PASS",
                "reason": f"Allowed steroid exception (dex-eq {dex_f:.1f} mg/day, {days_i} days)",
                "missing": [],
            }
        # 若标记为紧急激素但不满足例外条件，则按常规 washout 判断（不直接放行）

    # ---- Standard washout path ----
    raw_days_since = patient.get("days_since_last_anti_myeloma_tx")
    if raw_days_since is None:
        return {
            "rule_id": "R5_washout_anti_myeloma_tx",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": ["days_since_last_anti_myeloma_tx (距随机日前最近一次抗骨髓瘤治疗的间隔，天)"],
        }

    try:
        days_since = float(raw_days_since)
    except (TypeError, ValueError):
        return {
            "rule_id": "R5_washout_anti_myeloma_tx",
            "verdict": "UNCERTAIN",
            "reason": "Invalid field type/value",
            "missing": ["days_since_last_anti_myeloma_tx (天，需为数字)"],
        }

    # 如果 < 14 天：无论半衰期是多少，都必然违反“2周”要求 → 直接排除
    if days_since < 14:
        return {
            "rule_id": "R5_washout_anti_myeloma_tx",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"EXC: Washout not met (days_since={days_since:.1f}; required>=14d OR >=5*half-life)",
            "missing": [],
        }

    # >=14 天时，还要验证“5个半衰期（若更长）”
    raw_hl = patient.get("last_tx_half_life_days")
    if raw_hl is None:
        # 不能确认“更长者”到底是不是>14天 → 诚实地给 UNCERTAIN
        return {
            "rule_id": "R5_washout_anti_myeloma_tx",
            "verdict": "UNCERTAIN",
            "reason": "Half-life missing; cannot confirm 5 half-lives requirement",
            "missing": ["last_tx_half_life_days (最近一次治疗的半衰期，天；用于计算5个半衰期)"],
        }

    try:
        hl_days = float(raw_hl)
    except (TypeError, ValueError):
        return {
            "rule_id": "R5_washout_anti_myeloma_tx",
            "verdict": "UNCERTAIN",
            "reason": "Invalid half-life type/value",
            "missing": ["last_tx_half_life_days (天，需为数字)"],
        }

    required = max(14.0, 5.0 * hl_days)
    required_detail = f"required=max(14, 5*hl) where hl={hl_days:.2f}d => {required:.1f}d"

    if days_since < required:
        return {
            "rule_id": "R5_washout_anti_myeloma_tx",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"EXC: Washout not met (days_since={days_since:.1f}d < {required_detail})",
            "missing": [],
        }

    return {
        "rule_id": "R5_washout_anti_myeloma_tx",
        "verdict": "PASS",
        "reason": f"Washout met (days_since={days_since:.1f}d >= {required_detail})",
        "missing": [],
    }

def _to_float_or_none(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _is_abnormal_flc_ratio(patient: dict) -> bool | None:
    """
    Prefer explicit boolean if provided.
    Otherwise infer from numeric ratio using a common reference range (0.26-1.65).
    Returns:
      True/False if can decide, None if missing/unparseable.
    """
    explicit = patient.get("flc_ratio_abnormal")
    if explicit is True:
        return True
    if explicit is False:
        return False

    ratio = _to_float_or_none(patient.get("flc_kappa_lambda_ratio"))
    if ratio is None:
        return None

    return (ratio < 0.26) or (ratio > 1.65)


def rule_measurable_disease_apollo(patient: dict) -> RuleResult:
    """
    R6 (APOLLO Inclusion #3): Measurable disease definition (modified IMWG per protocol).
    """
    iso = patient.get("mm_isotype")
    iso_norm = (str(iso).strip().upper() if iso is not None else None)

    serum_m = _to_float_or_none(patient.get("serum_m_protein_g_dl"))         # g/dL
    urine_m = _to_float_or_none(patient.get("urine_m_protein_mg_24h"))       # mg/24h
    flc = _to_float_or_none(patient.get("serum_flc_mg_dl"))                  # mg/dL

    # --- Any isotype: urine M-protein >=200 qualifies ---
    if urine_m is not None and urine_m >= 200:
        return {
            "rule_id": "R6_measurable_disease",
            "verdict": "PASS",
            "reason": f"Measurable disease (urine M-protein {urine_m:.1f} mg/24h >= 200)",
            "missing": [],
        }

    # --- Serum M-protein route depends on isotype ---
    # Serum >= 1.0 g/dL always satisfies IgG threshold (and is also strong evidence of measurability).
    if serum_m is not None and serum_m >= 1.0:
        return {
            "rule_id": "R6_measurable_disease",
            "verdict": "PASS",
            "reason": f"Measurable disease (serum M-protein {serum_m:.2f} g/dL >= 1.0)",
            "missing": [],
        }

    # Serum in [0.5, 1.0): only qualifies for non-IgG intact immunoglobulin MM (IgA/IgD/IgE/IgM)
    if serum_m is not None and 0.5 <= serum_m < 1.0:
        if iso_norm in {"IGA", "IGD", "IGE", "IGM"}:
            return {
                "rule_id": "R6_measurable_disease",
                "verdict": "PASS",
                "reason": f"Measurable disease (isotype {iso_norm}, serum M-protein {serum_m:.2f} g/dL >= 0.5)",
                "missing": [],
            }
        if iso_norm == "IGG":
            # IgG needs >=1.0; urine already checked <200
            return {
                "rule_id": "R6_measurable_disease",
                "verdict": "NOT_ELIGIBLE",
                "reason": f"INC FAIL: IgG requires serum M-protein >=1.0 or urine >=200 (got serum={serum_m:.2f}, urine<{200})",
                "missing": [],
            }
        # isotype missing/unknown -> cannot decide
        return {
            "rule_id": "R6_measurable_disease",
            "verdict": "UNCERTAIN",
            "reason": "Isotype missing; cannot apply serum threshold (0.5-1.0 g/dL depends on Ig class)",
            "missing": ["mm_isotype (IgG/IgA/IgD/IgE/IgM/LIGHT_CHAIN)"],
        }

    # --- Light chain route: only for LIGHT_CHAIN and when no measurable serum/urine M-protein ---
    if iso_norm == "LIGHT_CHAIN":
        ratio_abn = _is_abnormal_flc_ratio(patient)

        if flc is None or ratio_abn is None:
            return {
                "rule_id": "R6_measurable_disease",
                "verdict": "UNCERTAIN",
                "reason": "Missing FLC inputs for light-chain measurable disease",
                "missing": [
                    "serum_flc_mg_dl (血清FLC, mg/dL)",
                    "flc_ratio_abnormal 或 flc_kappa_lambda_ratio (κ/λ 比值或其是否异常)",
                ],
            }

        if flc >= 10 and ratio_abn is True:
            return {
                "rule_id": "R6_measurable_disease",
                "verdict": "PASS",
                "reason": f"Measurable disease (light chain: FLC {flc:.1f} mg/dL >=10 and ratio abnormal)",
                "missing": [],
            }

        return {
            "rule_id": "R6_measurable_disease",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"INC FAIL: light chain criteria not met (FLC={flc:.1f} mg/dL, ratio_abnormal={ratio_abn})",
            "missing": [],
        }

    # --- If we reach here, we don't have enough evidence of measurability ---
    # If key measurements are missing, be honest -> UNCERTAIN. Otherwise -> NOT_ELIGIBLE.
    if serum_m is None and urine_m is None and flc is None:
        return {
            "rule_id": "R6_measurable_disease",
            "verdict": "UNCERTAIN",
            "reason": "Missing M-protein / urine M-protein / FLC data",
            "missing": [
                "serum_m_protein_g_dl (g/dL)",
                "urine_m_protein_mg_24h (mg/24h)",
                "mm_isotype (IgG/IgA/IgD/IgE/IgM/LIGHT_CHAIN)",
                "serum_flc_mg_dl (mg/dL) (if light chain MM)",
            ],
        }

    # Data present but below thresholds and not light-chain route -> not measurable
    return {
        "rule_id": "R6_measurable_disease",
        "verdict": "NOT_ELIGIBLE",
        "reason": "INC FAIL: measurable disease criteria not met (per protocol thresholds)",
        "missing": [],
    }

def _normalize_response(resp: str | None) -> str | None:
    if resp is None:
        return None
    s = str(resp).strip().upper()
    # 常见写法兼容
    aliases = {
        "SCR": "SCR",
        "S-CR": "SCR",
        "STRINGENT CR": "SCR",
        "CR": "CR",
        "COMPLETE RESPONSE": "CR",
        "VGPR": "VGPR",
        "VERY GOOD PARTIAL RESPONSE": "VGPR",
        "PR": "PR",
        "PARTIAL RESPONSE": "PR",
        "MR": "MR",
        "MINIMAL RESPONSE": "MR",
        "SD": "SD",
        "STABLE DISEASE": "SD",
        "PD": "PD",
        "PROGRESSIVE DISEASE": "PD",
        "NE": "NE",
        "NOT EVALUABLE": "NE",
        "UNKNOWN": None,
        "NA": None,
        "N/A": None,
    }
    return aliases.get(s, s)


def _is_pr_or_better(resp_norm: str | None) -> bool | None:
    """
    PR+ := PR, VGPR, CR, sCR
    If resp missing/unknown -> None (UNCERTAIN)
    """
    if resp_norm is None:
        return None
    resp_norm = resp_norm.upper()
    if resp_norm in {"SCR", "CR", "VGPR", "PR"}:
        return True
    if resp_norm in {"MR", "SD", "PD", "NE"}:
        return False
    # 不认识的标签 -> 不确定
    return None


def rule_prior_pi_len_and_pr(patient: dict) -> RuleResult:
    """
    R7 (APOLLO Inclusion #4):
    - must have received prior anti-myeloma treatment
    - prior treatment must have included BOTH a PI-containing regimen AND a lenalidomide-containing regimen
    - must have had response PR or better to prior therapy (investigator-assessed per modified IMWG)

    Source: APOLLO Prot_SAP_001.pdf, Section 5.1 inclusion criterion #4.
    """
    has_tx = patient.get("prior_has_anti_myeloma_tx")
    pi = patient.get("prior_exposed_pi")
    len_ = patient.get("prior_exposed_lenalidomide")
    resp_raw = patient.get("prior_best_response")

    missing = []
    if has_tx is None:
        missing.append("prior_has_anti_myeloma_tx (是否接受过既往抗骨髓瘤治疗)")
    if pi is None:
        missing.append("prior_exposed_pi (既往是否包含蛋白酶体抑制剂PI方案)")
    if len_ is None:
        missing.append("prior_exposed_lenalidomide (既往是否包含来那度胺lenalidomide方案)")
    if resp_raw is None:
        missing.append("prior_best_response (既往治疗最佳疗效：PR/VGPR/CR 等)")

    if missing:
        return {
            "rule_id": "R7_prior_PI_len_PRplus",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field(s) for Inclusion #4",
            "missing": missing,
        }

    # 1) 必须有既往抗骨髓瘤治疗
    if has_tx is not True:
        return {
            "rule_id": "R7_prior_PI_len_PRplus",
            "verdict": "NOT_ELIGIBLE",
            "reason": "INC FAIL: no prior anti-myeloma treatment",
            "missing": [],
        }

    # 2) 必须同时满足 PI 暴露 + Len 暴露
    if (pi is not True) or (len_ is not True):
        return {
            "rule_id": "R7_prior_PI_len_PRplus",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"INC FAIL: prior regimen must include BOTH PI and lenalidomide (pi={pi}, len={len_})",
            "missing": [],
        }

    # 3) 既往疗效必须 PR+
    resp_norm = _normalize_response(resp_raw)
    pr_plus = _is_pr_or_better(resp_norm)

    if pr_plus is None:
        return {
            "rule_id": "R7_prior_PI_len_PRplus",
            "verdict": "UNCERTAIN",
            "reason": f"Cannot interpret prior_best_response ({resp_raw}) for PR+ check",
            "missing": ["prior_best_response (应为 PR/VGPR/CR/sCR/SD/PD 等)"],
        }

    if pr_plus is False:
        return {
            "rule_id": "R7_prior_PI_len_PRplus",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"INC FAIL: prior response not PR+ (got {resp_norm})",
            "missing": [],
        }

    return {
        "rule_id": "R7_prior_PI_len_PRplus",
        "verdict": "PASS",
        "reason": f"Meets Inclusion #4 (PI+Len exposure and prior response PR+; resp={resp_norm})",
        "missing": [],
    }

def rule_pd_on_or_after_last_regimen(patient: dict) -> RuleResult:
    """
    R8 (APOLLO Inclusion #5):
    Subject must have progressive disease (PD) on or after the last regimen,
    as assessed by investigator per modified IMWG.

    Source: APOLLO Prot_SAP_001.pdf, Section 5.1 inclusion criterion #5.
    """
    flag = patient.get("pd_on_or_after_last_regimen")  # True / False / None

    if flag is True:
        return {
            "rule_id": "R8_PD_on_or_after_last_regimen",
            "verdict": "PASS",
            "reason": "Meets Inclusion #5: PD on/after last regimen",
            "missing": [],
        }

    if flag is None:
        return {
            "rule_id": "R8_PD_on_or_after_last_regimen",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": ["pd_on_or_after_last_regimen (是否在最近一次方案期间或之后出现PD)"],
        }

    return {
        "rule_id": "R8_PD_on_or_after_last_regimen",
        "verdict": "NOT_ELIGIBLE",
        "reason": "INC FAIL: no documented PD on/after last regimen",
        "missing": [],
    }

def rule_len_refractory_if_1lot(patient: dict) -> RuleResult:
    """
    R9 (APOLLO Inclusion #6):
    Subjects who received only 1 line of prior treatment must have demonstrated PD
    on or within 60 days of completion of the lenalidomide-containing regimen
    (i.e., lenalidomide refractory).
    """

    raw_lines = patient.get("prior_lines_of_therapy")
    if raw_lines is None:
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": ["prior_lines_of_therapy (既往治疗线数)"],
        }

    try:
        lines = int(raw_lines)
    except (TypeError, ValueError):
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "UNCERTAIN",
            "reason": "Invalid field type/value",
            "missing": ["prior_lines_of_therapy (既往治疗线数，需为整数)"],
        }

    if lines < 1:
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "NOT_ELIGIBLE",
            "reason": f"INC FAIL: invalid prior lines ({lines})",
            "missing": [],
        }

    # 如果 >=2 线：该条款不适用 -> 直接 PASS
    if lines >= 2:
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "PASS",
            "reason": f"Not applicable (prior_lines={lines} >=2)",
            "missing": [],
        }

    # lines == 1：必须 len-refractory（PD on/within 60 days of completion）
    flag = patient.get("len_refractory")  # True/False/None

    if flag is True:
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "PASS",
            "reason": "Meets Inclusion #6: len-refractory with 1 prior line",
            "missing": [],
        }
    if flag is False:
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "NOT_ELIGIBLE",
            "reason": "INC FAIL: 1 prior line but NOT len-refractory",
            "missing": [],
        }

        # 没有显式 bool，就尝试用 days 或日期计算
    raw_days = patient.get("days_from_len_completion_to_pd")

    days = None

    # 1) 优先用预先计算好的天数
    if raw_days is not None:
        try:
            days = float(raw_days)
        except (TypeError, ValueError):
            return {
                "rule_id": "R9_len_refractory_if_1lot",
                "verdict": "UNCERTAIN",
                "reason": "Invalid field type/value",
                "missing": ["days_from_len_completion_to_pd (需为数字，单位：天)"],
            }

    # 2) 如果没有 days，尝试用日期字段计算
    if days is None:
        len_dt = _parse_iso_date_yyyy_mm_dd(patient.get("len_completion_date"))
        pd_dt = _parse_iso_date_yyyy_mm_dd(patient.get("pd_date"))
        if len_dt is not None and pd_dt is not None:
            # pd_dt - len_dt：<=60 即满足（负数表示 PD 在完成前/期间，也属于“on/within 60 days”）
            days = float((pd_dt - len_dt).days)

    # 3) 仍无法得出 days -> UNCERTAIN
    if days is None:
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "UNCERTAIN",
            "reason": "Missing key field",
            "missing": [
                "len_refractory (是否len-refractory，True/False)",
                "或 days_from_len_completion_to_pd (PD距len完成的天数，<=60即满足)",
                "或 len_completion_date + pd_date (YYYY-MM-DD)",
            ],
        }

    # 4) 判定阈值：<=60 PASS，否则 NOT_ELIGIBLE
    if days <= 60:
        return {
            "rule_id": "R9_len_refractory_if_1lot",
            "verdict": "PASS",
            "reason": f"Meets Inclusion #6: PD on/within 60 days of len completion (days={days:.1f})",
            "missing": [],
        }

    return {
        "rule_id": "R9_len_refractory_if_1lot",
        "verdict": "NOT_ELIGIBLE",
        "reason": f"INC FAIL: PD not on/within 60 days of len completion (days={days:.1f} > 60)",
        "missing": [],
    }

def rule_safety_exclusion_bucket(patient: dict) -> RuleResult:
    """
    R10: Safety exclusion bucket (pre-screen style)

    设计目标：
    - 更像真实预筛，而不是把所有安全性条款拆得过碎
    - 任何硬排命中 -> NOT_ELIGIBLE
    - 若无硬排但关键信息缺失 -> UNCERTAIN
    - 全部安全项均无问题 -> PASS

    当前 bucket 包含：
    1) 活动性感染
    2) 重大心血管排除
    3) 14天内大手术
    4) 14天内放疗（运营化扩展字段）
    """

    checks = [
        (
            "active_infection",
            "R10_active_infection",
            "EXC: active infection",
            "active_infection (是否存在活动性感染)"
        ),
        (
            "major_cardiovascular_exclusion",
            "R10_major_cardiovascular",
            "EXC: major cardiovascular risk/exclusion",
            "major_cardiovascular_exclusion (是否存在重大心血管硬排)"
        ),
        (
            "major_surgery_within_14d",
            "R10_major_surgery_14d",
            "EXC: major surgery within 14 days",
            "major_surgery_within_14d (14天内是否做过大手术)"
        ),
        (
            "radiotherapy_within_14d",
            "R10_radiotherapy_14d",
            "EXC: radiotherapy within 14 days",
            "radiotherapy_within_14d (14天内是否接受过放疗)"
        ),
    ]

    missing = []
    triggered = []

    for field, sub_id, reason, missing_label in checks:
        value = patient.get(field)

        if value is True:
            triggered.append({
                "sub_rule_id": sub_id,
                "field": field,
                "reason": reason,
            })
        elif value is None:
            missing.append(missing_label)
        elif value is False:
            pass
        else:
            # 类型不合法，按缺失处理
            missing.append(missing_label)

    if triggered:
        reasons = "; ".join(x["reason"] for x in triggered)
        return {
            "rule_id": "R10_safety_exclusion_bucket",
            "verdict": "NOT_ELIGIBLE",
            "reason": reasons,
            "missing": [],
            "triggered": triggered,
        }

    if missing:
        return {
            "rule_id": "R10_safety_exclusion_bucket",
            "verdict": "UNCERTAIN",
            "reason": "Missing key safety exclusion field(s)",
            "missing": missing,
            "triggered": [],
        }

    return {
        "rule_id": "R10_safety_exclusion_bucket",
        "verdict": "PASS",
        "reason": "No safety exclusion triggered in implemented bucket",
        "missing": [],
        "triggered": [],
    }

def _to_float_or_none(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def rule_lab_threshold_bucket(patient: dict) -> RuleResult:
    """
    R11 (APOLLO Inclusion #10 subset):
    Lab threshold bucket for ANC / Hb / PLT / AST / ALT / total bilirubin.
    
    说明：
    - CrCl 已由 R4 单独处理，这里不重复纳入
    - Hb / PLT 不能靠输血“补到达标”
    - TBil 的 Gilbert 例外通过 gilbert_exception 标记处理
    """

    missing = []
    triggered = []

    anc = _to_float_or_none(patient.get("anc_x10e9_l"))
    hb = _to_float_or_none(patient.get("hb_g_dl"))
    plt = _to_float_or_none(patient.get("platelets_x10e9_l"))
    bm_pc = _to_float_or_none(patient.get("bone_marrow_plasma_cells_percent"))
    alt_x = _to_float_or_none(patient.get("alt_x_uln"))
    ast_x = _to_float_or_none(patient.get("ast_x_uln"))
    tbil_x = _to_float_or_none(patient.get("total_bilirubin_x_uln"))

    hb_tx = patient.get("hb_supported_by_transfusion")
    plt_tx = patient.get("plt_supported_by_transfusion")
    gilbert = patient.get("gilbert_exception")

    # ---- ANC ----
    if anc is None:
        missing.append("anc_x10e9_l (ANC，x10^9/L；要求>=1.0)")
    elif anc < 1.0:
        triggered.append({
            "sub_rule_id": "R11_anc",
            "field": "anc_x10e9_l",
            "reason": f"INC FAIL: ANC < 1.0 x10^9/L ({anc:.2f})",
        })

    # ---- Hb ----
    if hb is None:
        missing.append("hb_g_dl (Hb，g/dL；要求>=7.5，且不能靠输血达标)")
    elif hb < 7.5:
        triggered.append({
            "sub_rule_id": "R11_hb",
            "field": "hb_g_dl",
            "reason": f"INC FAIL: Hb < 7.5 g/dL ({hb:.2f})",
        })

    if hb_tx is None:
        missing.append("hb_supported_by_transfusion (Hb是否靠输血补到达标)")
    elif hb_tx is True:
        triggered.append({
            "sub_rule_id": "R11_hb_transfusion",
            "field": "hb_supported_by_transfusion",
            "reason": "INC FAIL: Hb threshold supported by transfusion",
        })

    # ---- PLT ----
    if plt is None:
        missing.append("platelets_x10e9_l (PLT，x10^9/L)")
    if bm_pc is None:
        missing.append("bone_marrow_plasma_cells_percent (骨髓浆细胞百分比，用于决定PLT阈值)")
    if plt_tx is None:
        missing.append("plt_supported_by_transfusion (PLT是否靠输血补到达标)")

    if plt is not None and bm_pc is not None:
        required_plt = 50.0 if bm_pc >= 50.0 else 75.0
        if plt < required_plt:
            triggered.append({
                "sub_rule_id": "R11_plt",
                "field": "platelets_x10e9_l",
                "reason": (
                    f"INC FAIL: PLT < required threshold "
                    f"({plt:.1f} < {required_plt:.1f}; marrow plasma cells={bm_pc:.1f}%)"
                ),
            })

    if plt_tx is True:
        triggered.append({
            "sub_rule_id": "R11_plt_transfusion",
            "field": "plt_supported_by_transfusion",
            "reason": "INC FAIL: PLT threshold supported by transfusion",
        })

    # ---- ALT ----
    if alt_x is None:
        missing.append("alt_x_uln (ALT/ULN；要求<=2.5)")
    elif alt_x > 2.5:
        triggered.append({
            "sub_rule_id": "R11_alt",
            "field": "alt_x_uln",
            "reason": f"INC FAIL: ALT > 2.5 xULN ({alt_x:.2f})",
        })

    # ---- AST ----
    if ast_x is None:
        missing.append("ast_x_uln (AST/ULN；要求<=2.5)")
    elif ast_x > 2.5:
        triggered.append({
            "sub_rule_id": "R11_ast",
            "field": "ast_x_uln",
            "reason": f"INC FAIL: AST > 2.5 xULN ({ast_x:.2f})",
        })

    # ---- TBil ----
    if tbil_x is None:
        missing.append("total_bilirubin_x_uln (总胆红素/ULN；要求<=1.5，Gilbert例外)")
    if gilbert is None:
        missing.append("gilbert_exception (是否属于Gilbert例外)")

    if tbil_x is not None and gilbert is not None:
        if (gilbert is False) and (tbil_x > 1.5):
            triggered.append({
                "sub_rule_id": "R11_tbil",
                "field": "total_bilirubin_x_uln",
                "reason": f"INC FAIL: total bilirubin > 1.5 xULN ({tbil_x:.2f})",
            })

    if triggered:
        return {
            "rule_id": "R11_lab_threshold_bucket",
            "verdict": "NOT_ELIGIBLE",
            "reason": "; ".join(x["reason"] for x in triggered),
            "missing": [],
            "triggered": triggered,
        }

    if missing:
        return {
            "rule_id": "R11_lab_threshold_bucket",
            "verdict": "UNCERTAIN",
            "reason": "Missing key lab threshold field(s)",
            "missing": missing,
            "triggered": [],
        }

    return {
        "rule_id": "R11_lab_threshold_bucket",
        "verdict": "PASS",
        "reason": "All implemented lab thresholds met",
        "missing": [],
        "triggered": [],
    }