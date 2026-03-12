# cases/patient_fail_r10.py

PATIENT_FAIL_R10 = {
    # -----------------------------
    # 基本标识（非规则必需，仅方便阅读）
    # -----------------------------
    "patient_id": "APOLLO_DEMO_FAIL_R10_001",
    "diagnosis": "RRMM",

    # -----------------------------
    # R1: 既往 anti-CD38 暴露排除
    # -----------------------------
    "prior_anti_cd38": False,

    # -----------------------------
    # R2: 既往 pomalidomide 暴露排除
    # -----------------------------
    "prior_pomalidomide": False,

    # -----------------------------
    # R3: ECOG <= 2
    # -----------------------------
    "ecog": 1,

    # -----------------------------
    # R4: CrCl >= 30 mL/min
    # -----------------------------
    "crcl_ml_min": 62,

    # -----------------------------
    # R5: washout
    # -----------------------------
    "days_since_last_anti_myeloma_tx": 45,
    "last_tx_half_life_days": 2,

    # -----------------------------
    # R6: measurable disease
    # 这里走 serum M-protein 路径
    # -----------------------------
    "serum_m_protein_g_dl": 1.4,
    "urine_m_protein_mg_24h": 40,
    "serum_flc_mg_dl": 6.0,
    "serum_flc_ratio_abnormal": False,

    # -----------------------------
    # R7: PI + Len + PR及以上
    # -----------------------------
    "prior_pi_exposure": True,
    "prior_len_exposure": True,
    "best_response_category": "VGPR",

    # -----------------------------
    # R8: PD on/after last regimen
    # -----------------------------
    "progressed_on_or_after_last_regimen": True,

    # -----------------------------
    # R9: 若仅1线，则需len-refractory
    # 这里直接给2线，避免卡这个分支
    # -----------------------------
    "number_of_prior_lines": 2,
    "len_refractory": False,

    # -----------------------------
    # R10: safety exclusion bucket
    # 这里故意命中活动感染
    # -----------------------------
    "active_infection": True,
    "major_cardiovascular_exclusion": False,
    "major_surgery_within_14d": False,
    "radiotherapy_within_14d": False,

    # -----------------------------
    # R11: lab threshold bucket
    # 其他实验室都设成通过，确保失败来源清晰来自R10
    # -----------------------------
    "anc_x10e9_l": 1.5,
    "hb_g_dl": 8.8,
    "platelets_x10e9_l": 90,
    "bone_marrow_plasma_cells_percent": 30,
    "alt_x_uln": 1.2,
    "ast_x_uln": 1.0,
    "total_bilirubin_x_uln": 1.1,

    "hb_supported_by_transfusion": False,
    "plt_supported_by_transfusion": False,
    "gilbert_exception": False,
}