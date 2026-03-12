PATIENT_PASS_R1_R11 = {
    # -----------------------------
    # 基本标识（非规则必需，仅方便阅读）
    # -----------------------------
    "patient_id": "APOLLO_DEMO_001",
    "diagnosis": "RRMM",

    # -----------------------------
    # R1: 既往 anti-CD38 暴露排除
    # True -> NOT_ELIGIBLE
    # False -> PASS
    # -----------------------------
    "prior_anti_cd38": False,

    # -----------------------------
    # R2: 既往 pomalidomide 暴露排除
    # True -> NOT_ELIGIBLE
    # False -> PASS
    # -----------------------------
    "prior_pomalidomide": False,

    # -----------------------------
    # R3: ECOG <= 2
    # -----------------------------
    "ecog": 1,

    # -----------------------------
    # R4: CrCl >= 30 mL/min
    # -----------------------------
    "crcl_ml_min": 65,

    # -----------------------------
    # R5: 抗骨髓瘤治疗 washout
    # 这里给一个明显安全的值，避免卡边界
    # -----------------------------
    "days_since_last_anti_myeloma_tx": 60,
    "last_tx_half_life_days": 2,

    # -----------------------------
    # R6: measurable disease
    # 任一路径满足即可
    # 这里用 serum M-protein 路径满足
    # -----------------------------
    "serum_m_protein_g_dl": 1.2,
    "urine_m_protein_mg_24h": 50,
    "serum_flc_mg_dl": 5.0,
    "serum_flc_ratio_abnormal": False,

    # -----------------------------
    # R7: 既往 PI + Len 暴露，且曾获得 PR 及以上
    # -----------------------------
    "prior_pi_exposure": True,
    "prior_len_exposure": True,
    "best_response_category": "PR",

    # -----------------------------
    # R8: 最后一线治疗期间或之后发生 PD
    # -----------------------------
    "progressed_on_or_after_last_regimen": True,

    # -----------------------------
    # R9: 若仅 1 线治疗，则需 len-refractory
    # 这里设为 2 线，直接满足
    # -----------------------------
    "number_of_prior_lines": 2,
    "len_refractory": False,

    # -----------------------------
    # R10: safety exclusion bucket
    # 任一 True -> NOT_ELIGIBLE
    # -----------------------------
    "active_infection": False,
    "major_cardiovascular_exclusion": False,
    "major_surgery_within_14d": False,
    "radiotherapy_within_14d": False,

    # -----------------------------
    # R11: lab threshold bucket
    # -----------------------------
    "anc_x10e9_l": 1.3,
    "hb_g_dl": 8.6,
    "platelets_x10e9_l": 85,
    "bone_marrow_plasma_cells_percent": 35,
    "alt_x_uln": 1.1,
    "ast_x_uln": 1.0,
    "total_bilirubin_x_uln": 1.0,

    "hb_supported_by_transfusion": False,
    "plt_supported_by_transfusion": False,
    "gilbert_exception": False,
}