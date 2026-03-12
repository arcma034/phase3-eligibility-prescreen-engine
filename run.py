from eligibility.engine import run_rules
from eligibility.rules import (
    rule_measurable_disease_apollo,    # R6
    rule_prior_pi_len_and_pr,          # R7
    rule_pd_on_or_after_last_regimen,  # R8
    rule_len_refractory_if_1lot,       # R9
    rule_prior_anti_cd38,              # R1
    rule_prior_pomalidomide,           # R2
    rule_ecog_le_2,                    # R3
    rule_crcl_ge_30,                   # R4
    rule_washout_anti_myeloma_tx,      # R5
    rule_safety_exclusion_bucket,      # R10
    rule_lab_threshold_bucket,
)

if __name__ == "__main__":
    patient_example = {
        # R1
        "prior_anti_cd38": False,
        # R2
        "prior_pomalidomide": False,
        # R3
        "ecog": 2,

        # R4：方式1：直接给 CrCl
        "crcl_ml_min": 55,

        # 方式2（可选）：不给 crcl_ml_min，让它按 Appendix 6 计算
        # "age_years": 60,
        # "weight_kg": 70,
        # "sex": "F",
        # "scr_umol_l": 88.4,
        
        # R5：举例（可改不同值看 PASS/UNCERTAIN/NOT_ELIGIBLE）
        "days_since_last_anti_myeloma_tx": 30,
        "last_tx_half_life_days": 2,
        
        # R6
        "mm_isotype": "IgG",
        "serum_m_protein_g_dl": 1.1,
        "urine_m_protein_mg_24h": 50,

        # R7
        "prior_has_anti_myeloma_tx": True,
        "prior_exposed_pi": True,
        "prior_exposed_lenalidomide": True,
        "prior_best_response": "PR",

        # R8
        "pd_on_or_after_last_regimen": True,

        # R9
        "prior_lines_of_therapy": 1,
        "len_completion_date": "2026-01-01",
        "pd_date": "2026-03-02",

        # R10
        "active_infection": False,
        "major_cardiovascular_exclusion": False,
        "major_surgery_within_14d": False,
        "radiotherapy_within_14d": False,
        
        # R11
        "anc_x10e9_l": 1.3,
        "hb_g_dl": 8.4,
        "platelets_x10e9_l": 85,
        "bone_marrow_plasma_cells_percent": 35,
        "alt_x_uln": 1.2,
        "ast_x_uln": 1.1,
        "total_bilirubin_x_uln": 1.0,
        "hb_supported_by_transfusion": False,
        "plt_supported_by_transfusion": False,
        "gilbert_exception": False,
    }

    result = run_rules(
    patient=patient_example,
    rules=[
        rule_measurable_disease_apollo,
        rule_prior_pi_len_and_pr,
        rule_pd_on_or_after_last_regimen,   
        rule_len_refractory_if_1lot, 
        rule_prior_anti_cd38,
        rule_prior_pomalidomide,
        rule_washout_anti_myeloma_tx,
        rule_safety_exclusion_bucket,  
        rule_ecog_le_2,
        rule_crcl_ge_30,
        rule_lab_threshold_bucket,   
    ],
    stop_on_first_not_eligible=True,
    )

    print(result)