from __future__ import annotations

from typing import TypedDict, List, Dict, Literal, Optional


VerdictStyle = Literal["INCLUSION", "EXCLUSION", "MIXED", "META"]
ImplementationStatus = Literal["implemented", "partial", "planned"]


class RuleMeta(TypedDict):
    rule_id: str
    short_name: str
    trial: str
    category: str
    rule_type: VerdictStyle
    protocol_section: str
    protocol_basis: List[str]
    required_fields: List[str]
    optional_fields: List[str]
    decision_logic: str
    status: ImplementationStatus
    notes: str


TRIAL_META: Dict[str, str] = {
    "trial_name": "APOLLO",
    "disease": "Relapsed/Refractory Multiple Myeloma",
    "engine_scope": (
        "PoC trial-matching / prescreen engine. "
        "Implements high-value eligibility rules first, not full protocol coverage."
    ),
    "output_semantics": (
        "PASS = meets implemented rule; "
        "NOT_ELIGIBLE = fails implemented rule; "
        "UNCERTAIN = cannot adjudicate due to missing key field(s)."
    ),
    "design_principles": (
        "1) 优先实现高判别力主干规则；"
        "2) 排除项可聚合为 safety bucket；"
        "3) 实验室阈值可聚合为 lab bucket；"
        "4) 缺失关键信息时输出 UNCERTAIN，而不是假设通过。"
    ),
}


RULE_MAPPING: Dict[str, RuleMeta] = {
    "R1_prior_anti_cd38": {
        "rule_id": "R1_prior_anti_cd38",
        "short_name": "既往抗CD38暴露排除",
        "trial": "APOLLO",
        "category": "treatment_history",
        "rule_type": "EXCLUSION",
        "protocol_section": "Exclusion criteria / prior therapy history",
        "protocol_basis": [
            "患者不应既往接受过抗CD38单抗治疗。",
        ],
        "required_fields": [
            "prior_anti_cd38",
        ],
        "optional_fields": [],
        "decision_logic": (
            "prior_anti_cd38 == True -> NOT_ELIGIBLE; "
            "prior_anti_cd38 == False -> PASS; "
            "缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "高区分度治疗史排除项，适合早期预筛。",
    },

    "R2_prior_pomalidomide": {
        "rule_id": "R2_prior_pomalidomide",
        "short_name": "既往泊马度胺暴露排除",
        "trial": "APOLLO",
        "category": "treatment_history",
        "rule_type": "EXCLUSION",
        "protocol_section": "Exclusion criteria / prior therapy history",
        "protocol_basis": [
            "患者不应既往接受过泊马度胺治疗。",
        ],
        "required_fields": [
            "prior_pomalidomide",
        ],
        "optional_fields": [],
        "decision_logic": (
            "prior_pomalidomide == True -> NOT_ELIGIBLE; "
            "prior_pomalidomide == False -> PASS; "
            "缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "与 R1 一样，属于高价值一票否决治疗史条款。",
    },

    "R3_ecog_le_2": {
        "rule_id": "R3_ecog_le_2",
        "short_name": "ECOG体能状态",
        "trial": "APOLLO",
        "category": "performance_status",
        "rule_type": "INCLUSION",
        "protocol_section": "Inclusion criteria / baseline functional status",
        "protocol_basis": [
            "ECOG 体能状态要求 ≤ 2。",
        ],
        "required_fields": [
            "ecog",
        ],
        "optional_fields": [],
        "decision_logic": (
            "ecog <= 2 -> PASS; "
            "ecog > 2 -> NOT_ELIGIBLE; "
            "缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "基础状态门槛，临床预筛常见核心字段。",
    },

    "R4_crcl_ge_30": {
        "rule_id": "R4_crcl_ge_30",
        "short_name": "肾功能阈值",
        "trial": "APOLLO",
        "category": "organ_function",
        "rule_type": "INCLUSION",
        "protocol_section": "Inclusion criteria / renal function",
        "protocol_basis": [
            "肌酐清除率（CrCl）需达到方案要求阈值。",
        ],
        "required_fields": [
            "crcl_ml_min",
        ],
        "optional_fields": [],
        "decision_logic": (
            "crcl_ml_min >= 30 -> PASS; "
            "crcl_ml_min < 30 -> NOT_ELIGIBLE; "
            "缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "已单独实现，因此 R11 不再重复纳入 CrCl。",
    },

    "R5_washout_anti_myeloma_tx": {
        "rule_id": "R5_washout_anti_myeloma_tx",
        "short_name": "近期抗骨髓瘤治疗洗脱期",
        "trial": "APOLLO",
        "category": "time_window",
        "rule_type": "EXCLUSION",
        "protocol_section": "Exclusion criteria / washout requirements",
        "protocol_basis": [
            "入组前既往抗骨髓瘤治疗需满足规定洗脱期。",
        ],
        "required_fields": [
            "days_since_last_anti_myeloma_tx",
            "last_tx_half_life_days",
        ],
        "optional_fields": [],
        "decision_logic": (
            "若距离上次治疗时间满足 washout -> PASS; "
            "不满足 -> NOT_ELIGIBLE; "
            "关键信息缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "体现时间窗逻辑，不只是静态阈值判断。",
    },

    "R6_measurable_disease": {
        "rule_id": "R6_measurable_disease",
        "short_name": "可测量疾病",
        "trial": "APOLLO",
        "category": "disease_definition",
        "rule_type": "INCLUSION",
        "protocol_section": "Inclusion criteria / measurable disease",
        "protocol_basis": [
            "受试者需满足可测量疾病标准。",
            "通常可由血清 M 蛋白、尿 M 蛋白或游离轻链等路径判定。",
        ],
        "required_fields": [
            "serum_m_protein_g_dl",
            "urine_m_protein_mg_24h",
            "serum_flc_mg_dl",
            "serum_flc_ratio_abnormal",
        ],
        "optional_fields": [],
        "decision_logic": (
            "任一可测量疾病路径达标 -> PASS; "
            "已知均不达标 -> NOT_ELIGIBLE; "
            "信息不足无法判定 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "疾病定义主干规则之一。",
    },

    "R7_prior_PI_len_PRplus": {
        "rule_id": "R7_prior_PI_len_PRplus",
        "short_name": "既往PI+Len且曾获PR及以上",
        "trial": "APOLLO",
        "category": "treatment_history",
        "rule_type": "INCLUSION",
        "protocol_section": "Inclusion criteria / prior regimen history",
        "protocol_basis": [
            "既往接受过蛋白酶体抑制剂（PI）和来那度胺（Len）。",
            "并且在至少一种既往方案中达到 PR 或更好疗效。",
        ],
        "required_fields": [
            "prior_pi_exposure",
            "prior_len_exposure",
            "best_response_category",
        ],
        "optional_fields": [],
        "decision_logic": (
            "PI 暴露 + Len 暴露 + 最佳疗效 >= PR -> PASS; "
            "明确不满足 -> NOT_ELIGIBLE; "
            "信息缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "决定目标人群是否符合试验既往治疗背景。",
    },

    "R8_pd_on_or_after_last_regimen": {
        "rule_id": "R8_pd_on_or_after_last_regimen",
        "short_name": "末线治疗期间或之后发生进展",
        "trial": "APOLLO",
        "category": "disease_status",
        "rule_type": "INCLUSION",
        "protocol_section": "Inclusion criteria / progression status",
        "protocol_basis": [
            "患者需在最后一线治疗期间或之后出现疾病进展（PD）。",
        ],
        "required_fields": [
            "progressed_on_or_after_last_regimen",
        ],
        "optional_fields": [],
        "decision_logic": (
            "progressed_on_or_after_last_regimen == True -> PASS; "
            "== False -> NOT_ELIGIBLE; "
            "缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "与 R7 一起构成复发/难治目标人群主干。",
    },

    "R9_len_refractory_if_1lot": {
        "rule_id": "R9_len_refractory_if_1lot",
        "short_name": "若仅1线治疗则需Len难治",
        "trial": "APOLLO",
        "category": "treatment_history",
        "rule_type": "INCLUSION",
        "protocol_section": "Inclusion criteria / line-specific requirement",
        "protocol_basis": [
            "若患者仅接受过 1 线治疗，则需满足来那度胺难治。",
        ],
        "required_fields": [
            "number_of_prior_lines",
            "len_refractory",
        ],
        "optional_fields": [],
        "decision_logic": (
            "若 prior_lines > 1，则该条直接 PASS；"
            "若 prior_lines == 1，则 len_refractory == True 才 PASS；"
            "若不满足 -> NOT_ELIGIBLE；"
            "缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": "体现条件分支型方案逻辑，而非单阈值。",
    },

    "R10_safety_exclusion_bucket": {
        "rule_id": "R10_safety_exclusion_bucket",
        "short_name": "安全性排除桶",
        "trial": "APOLLO",
        "category": "safety_exclusion",
        "rule_type": "MIXED",
        "protocol_section": "Exclusion criteria / safety-focused prescreen bucket",
        "protocol_basis": [
            "活动性感染。",
            "重大心血管排除。",
            "14天内大手术。",
            "近期放疗（作为预筛场景下的运营化扩展字段）。",
        ],
        "required_fields": [
            "active_infection",
            "major_cardiovascular_exclusion",
            "major_surgery_within_14d",
            "radiotherapy_within_14d",
        ],
        "optional_fields": [],
        "decision_logic": (
            "任一硬排命中 -> NOT_ELIGIBLE; "
            "均未命中且字段齐全 -> PASS; "
            "无硬排但有关键字段缺失 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": (
            "这是 prescreen 风格聚合规则。"
            "其中近期放疗字段属于贴近真实工作流的运营化扩展，不等同于逐字复刻 protocol 原文。"
        ),
    },

    "R11_lab_threshold_bucket": {
        "rule_id": "R11_lab_threshold_bucket",
        "short_name": "实验室阈值桶",
        "trial": "APOLLO",
        "category": "laboratory_thresholds",
        "rule_type": "MIXED",
        "protocol_section": "Inclusion criteria / laboratory thresholds",
        "protocol_basis": [
            "ANC 达到阈值。",
            "Hb 达到阈值，且不能依赖输血补到达标。",
            "PLT 达到阈值，且阈值与骨髓浆细胞比例相关，不能依赖输血补到达标。",
            "ALT / AST 不高于规定 ULN 倍数。",
            "总胆红素不高于规定 ULN 倍数，Gilbert 例外单独处理。",
        ],
        "required_fields": [
            "anc_x10e9_l",
            "hb_g_dl",
            "platelets_x10e9_l",
            "bone_marrow_plasma_cells_percent",
            "alt_x_uln",
            "ast_x_uln",
            "total_bilirubin_x_uln",
            "hb_supported_by_transfusion",
            "plt_supported_by_transfusion",
            "gilbert_exception",
        ],
        "optional_fields": [],
        "decision_logic": (
            "任一已知实验室阈值不达标 -> NOT_ELIGIBLE; "
            "全部达标 -> PASS; "
            "若未见失败但缺关键化验字段 -> UNCERTAIN"
        ),
        "status": "implemented",
        "notes": (
            "该桶不再重复纳入 CrCl，避免与 R4 重复判定。"
            "它展示的是 screening labs 的聚合审阅思路。"
        ),
    },
}


RULE_ORDER: List[str] = [
    "R6_measurable_disease",
    "R7_prior_PI_len_PRplus",
    "R8_pd_on_or_after_last_regimen",
    "R9_len_refractory_if_1lot",
    "R1_prior_anti_cd38",
    "R2_prior_pomalidomide",
    "R5_washout_anti_myeloma_tx",
    "R10_safety_exclusion_bucket",
    "R3_ecog_le_2",
    "R4_crcl_ge_30",
    "R11_lab_threshold_bucket",
]


SCREENING_LAYERS: Dict[str, List[str]] = {
    "人群定义主干": [
        "R6_measurable_disease",
        "R7_prior_PI_len_PRplus",
        "R8_pd_on_or_after_last_regimen",
        "R9_len_refractory_if_1lot",
    ],
    "既往暴露一票否决": [
        "R1_prior_anti_cd38",
        "R2_prior_pomalidomide",
    ],
    "时间窗与近期治疗": [
        "R5_washout_anti_myeloma_tx",
    ],
    "安全性预筛": [
        "R10_safety_exclusion_bucket",
    ],
    "基础状态与器官功能": [
        "R3_ecog_le_2",
        "R4_crcl_ge_30",
    ],
    "实验室入组门槛": [
        "R11_lab_threshold_bucket",
    ],
}

