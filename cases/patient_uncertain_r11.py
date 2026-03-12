# cases/patient_uncertain_r11.py

PATIENT_UNCERTAIN_R11 = {
    # -----------------------------
    # 基本标识（非规则必需，仅方便阅读）
    # -----------------------------
    "patient_id": "APOLLO_DEMO_UNCERTAIN_R11_001",
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
    "crcl_ml_min": 58,

    # -----------------------------
    # R5: washout
    # -----------------------------
    "days_since_last_anti_myeloma_tx": 50,
    "last_tx_half_life_days": 2,

    # -----------------------------
    # R6: measurable disease
    # -----------------------------
    "serum_m_protein_g_dl": 1.1,
    "urine_m_protein_mg_24h": 30,
    "serum_flc_mg_dl": 4.8,
    "serum_flc_ratio_abnormal": False,

    # -----------------------------
    # R7: PI + Len + PR及以上
    # -----------------------------
    "prior_pi_exposure": True,
    "prior_len_exposure": True,
    "best_response_category": "PR",

    # -----------------------------
    # R8: PD on/after last regimen
    # -----------------------------
    "progressed_on_or_after_last_regimen": True,

    # -----------------------------
    # R9: 这里演示“1线但len-refractory”
    # 也就是这条仍然通过
    # -----------------------------
    "number_of_prior_lines": 1,
    "len_refractory": True,

    # -----------------------------
    # R10: safety exclusion bucket
    # 全部不命中
    # -----------------------------
    "active_infection": False,
    "major_cardiovascular_exclusion": False,
    "major_surgery_within_14d": False,
    "radiotherapy_within_14d": False,

    # -----------------------------
    # R11: lab threshold bucket
    # 故意制造缺失，触发 UNCERTAIN
    # -----------------------------
    "anc_x10e9_l": None,
    "hb_g_dl": 8.3,
    "platelets_x10e9_l": 82,
    "bone_marrow_plasma_cells_percent": 28,
    "alt_x_uln": 1.0,
    "ast_x_uln": 1.1,
    "total_bilirubin_x_uln": 1.0,

    "hb_supported_by_transfusion": False,
    "plt_supported_by_transfusion": False,
    "gilbert_exception": None,
}