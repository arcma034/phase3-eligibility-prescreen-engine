# tests/test_engine.py
import pytest
from eligibility.engine import run_rules
from eligibility.rules import rule_prior_anti_cd38, rule_prior_pomalidomide
from eligibility.rules import rule_ecog_le_2
from eligibility.rules import rule_crcl_ge_30
from eligibility.rules import rule_washout_anti_myeloma_tx
from eligibility.rules import rule_measurable_disease_apollo
from eligibility.rules import rule_prior_pi_len_and_pr
from eligibility.rules import rule_pd_on_or_after_last_regimen
from eligibility.rules import rule_len_refractory_if_1lot
from eligibility.rules import rule_safety_exclusion_bucket
from eligibility.rules import rule_lab_threshold_bucket


@pytest.mark.parametrize(
    "patient, expected",
    [
        ({"prior_anti_cd38": True}, "NOT_ELIGIBLE"),
        ({"prior_anti_cd38": None}, "UNCERTAIN"),
        ({"prior_anti_cd38": False}, "PASS"),
    ],
)
def test_rule1_prior_anti_cd38(patient, expected):
    assert rule_prior_anti_cd38(patient)["verdict"] == expected


@pytest.mark.parametrize(
    "patient, expected",
    [
        ({"prior_pomalidomide": True}, "NOT_ELIGIBLE"),
        ({"prior_pomalidomide": None}, "UNCERTAIN"),
        ({"prior_pomalidomide": False}, "PASS"),
    ],
)
def test_rule2_prior_pomalidomide(patient, expected):
    assert rule_prior_pomalidomide(patient)["verdict"] == expected


def test_engine_not_eligible_stops_early():
    patient = {"prior_anti_cd38": True, "prior_pomalidomide": None}
    out = run_rules(patient, [rule_prior_anti_cd38, rule_prior_pomalidomide], stop_on_first_not_eligible=True)
    assert out["verdict"] == "NOT_ELIGIBLE"


def test_engine_uncertain_collects_missing():
    patient = {"prior_anti_cd38": None, "prior_pomalidomide": None}
    out = run_rules(patient, [rule_prior_anti_cd38, rule_prior_pomalidomide])
    assert out["verdict"] == "UNCERTAIN"
    assert "prior_anti_cd38 (是否用过抗CD38单抗)" in out["missing"]
    assert "prior_pomalidomide (是否用过泊马度胺)" in out["missing"]


def test_engine_pass():
    patient = {"prior_anti_cd38": False, "prior_pomalidomide": False}
    out = run_rules(patient, [rule_prior_anti_cd38, rule_prior_pomalidomide])
    assert out["verdict"] == "PASS"


@pytest.mark.parametrize(
    "patient, expected",
    [
        ({"ecog": None}, "UNCERTAIN"),
        ({"ecog": "2"}, "PASS"),
        ({"ecog": 2}, "PASS"),
        ({"ecog": 3}, "NOT_ELIGIBLE"),
        ({"ecog": "unknown"}, "UNCERTAIN"),
    ],
)
def test_rule3_ecog(patient, expected):
    assert rule_ecog_le_2(patient)["verdict"] == expected

import pytest

@pytest.mark.parametrize(
    "patient, expected",
    [
        ({"crcl_ml_min": None}, "UNCERTAIN"),
        ({"crcl_ml_min": 25}, "NOT_ELIGIBLE"),
        ({"crcl_ml_min": 30}, "PASS"),
        # 计算兜底：用 Cockcroft–Gault（随便给一组能算出 >=30 的）
        ({"age_years": 60, "weight_kg": 70, "sex": "M", "scr_mg_dl": 1.0}, "PASS"),
        # SI 单位换算：88.4 μmol/L = 1.0 mg/dL
        ({"age_years": 60, "weight_kg": 70, "sex": "F", "scr_umol_l": 88.4}, "PASS"),
    ],
)
def test_rule4_crcl(patient, expected):
    assert rule_crcl_ge_30(patient)["verdict"] == expected

import pytest

@pytest.mark.parametrize(
    "patient, expected",
    [
        ({"days_since_last_anti_myeloma_tx": None}, "UNCERTAIN"),
        ({"days_since_last_anti_myeloma_tx": 7}, "NOT_ELIGIBLE"),  # <14天必排除
        ({"days_since_last_anti_myeloma_tx": 14}, "UNCERTAIN"),    # >=14但缺半衰期 -> 不确定
        ({"days_since_last_anti_myeloma_tx": 30, "last_tx_half_life_days": 2}, "PASS"),  # required=max(14,10)=14
        ({"days_since_last_anti_myeloma_tx": 20, "last_tx_half_life_days": 5}, "NOT_ELIGIBLE"),  # required=max(14,25)=25
        # 激素例外：允许
        ({"emergency_short_steroid_course": True, "steroid_dex_equiv_mg_per_day": 40, "steroid_course_days": 4,
          "days_since_last_anti_myeloma_tx": 0}, "PASS"),
    ],
)
def test_rule5_washout(patient, expected):
    assert rule_washout_anti_myeloma_tx(patient)["verdict"] == expected

import pytest

@pytest.mark.parametrize(
    "patient, expected",
    [
        # urine criterion works regardless of isotype
        ({"urine_m_protein_mg_24h": 250}, "PASS"),

        # IgG
        ({"mm_isotype": "IgG", "serum_m_protein_g_dl": 1.2, "urine_m_protein_mg_24h": 10}, "PASS"),
        ({"mm_isotype": "IgG", "serum_m_protein_g_dl": 0.8, "urine_m_protein_mg_24h": 10}, "NOT_ELIGIBLE"),

        # IgA (non-IgG intact immunoglobulin)
        ({"mm_isotype": "IgA", "serum_m_protein_g_dl": 0.8, "urine_m_protein_mg_24h": 10}, "PASS"),

        # ambiguous serum 0.8 without isotype -> UNCERTAIN
        ({"serum_m_protein_g_dl": 0.8, "urine_m_protein_mg_24h": 10}, "UNCERTAIN"),

        # Light chain route
        ({"mm_isotype": "LIGHT_CHAIN", "serum_flc_mg_dl": 12, "flc_kappa_lambda_ratio": 10}, "PASS"),
        ({"mm_isotype": "LIGHT_CHAIN", "serum_flc_mg_dl": 8, "flc_kappa_lambda_ratio": 10}, "NOT_ELIGIBLE"),
        ({"mm_isotype": "LIGHT_CHAIN", "serum_flc_mg_dl": 12}, "UNCERTAIN"),
    ],
)
def test_rule6_measurable_disease(patient, expected):
    assert rule_measurable_disease_apollo(patient)["verdict"] == expected

import pytest

@pytest.mark.parametrize(
    "patient, expected",
    [
        # missing -> UNCERTAIN
        ({}, "UNCERTAIN"),

        # no prior tx -> NOT_ELIGIBLE
        ({
            "prior_has_anti_myeloma_tx": False,
            "prior_exposed_pi": True,
            "prior_exposed_lenalidomide": True,
            "prior_best_response": "PR",
        }, "NOT_ELIGIBLE"),

        # missing PI or Len exposure -> NOT_ELIGIBLE
        ({
            "prior_has_anti_myeloma_tx": True,
            "prior_exposed_pi": False,
            "prior_exposed_lenalidomide": True,
            "prior_best_response": "VGPR",
        }, "NOT_ELIGIBLE"),

        # response below PR -> NOT_ELIGIBLE
        ({
            "prior_has_anti_myeloma_tx": True,
            "prior_exposed_pi": True,
            "prior_exposed_lenalidomide": True,
            "prior_best_response": "SD",
        }, "NOT_ELIGIBLE"),

        # PR+ -> PASS
        ({
            "prior_has_anti_myeloma_tx": True,
            "prior_exposed_pi": True,
            "prior_exposed_lenalidomide": True,
            "prior_best_response": "PR",
        }, "PASS"),

        # aliases -> PASS
        ({
            "prior_has_anti_myeloma_tx": True,
            "prior_exposed_pi": True,
            "prior_exposed_lenalidomide": True,
            "prior_best_response": "Complete Response",
        }, "PASS"),
    ],
)
def test_rule7_prior_pi_len_pr(patient, expected):
    assert rule_prior_pi_len_and_pr(patient)["verdict"] == expected

import pytest

@pytest.mark.parametrize(
    "patient, expected",
    [
        ({"pd_on_or_after_last_regimen": True}, "PASS"),
        ({"pd_on_or_after_last_regimen": False}, "NOT_ELIGIBLE"),
        ({"pd_on_or_after_last_regimen": None}, "UNCERTAIN"),
        ({}, "UNCERTAIN"),
    ],
)
def test_rule8_pd_on_or_after_last_regimen(patient, expected):
    assert rule_pd_on_or_after_last_regimen(patient)["verdict"] == expected

import pytest

@pytest.mark.parametrize(
    "patient, expected",
    [
        ({}, "UNCERTAIN"),
        ({"prior_lines_of_therapy": None}, "UNCERTAIN"),

        # >=2 lines -> not applicable -> PASS
        ({"prior_lines_of_therapy": 2}, "PASS"),

        # 1 line with explicit flag
        ({"prior_lines_of_therapy": 1, "len_refractory": True}, "PASS"),
        ({"prior_lines_of_therapy": 1, "len_refractory": False}, "NOT_ELIGIBLE"),

        # 1 line with computed days
        ({"prior_lines_of_therapy": 1, "days_from_len_completion_to_pd": 30}, "PASS"),
        ({"prior_lines_of_therapy": 1, "days_from_len_completion_to_pd": 60}, "PASS"),
        ({"prior_lines_of_therapy": 1, "days_from_len_completion_to_pd": 61}, "NOT_ELIGIBLE"),

        # 1 line but missing refractory evidence
        ({"prior_lines_of_therapy": 1}, "UNCERTAIN"),

        ({"prior_lines_of_therapy": 1, "len_completion_date": "2026-01-01", "pd_date": "2026-02-15"}, "PASS"),  # 45天
        ({"prior_lines_of_therapy": 1, "len_completion_date": "2026-01-01", "pd_date": "2026-03-05"}, "NOT_ELIGIBLE"),  # 63天
    ],
)
def test_rule9_len_refractory_if_1lot(patient, expected):
    assert rule_len_refractory_if_1lot(patient)["verdict"] == expected

@pytest.mark.parametrize(
    "patient, expected",
    [
        (
            {
                "active_infection": False,
                "major_cardiovascular_exclusion": False,
                "major_surgery_within_14d": False,
                "radiotherapy_within_14d": False,
            },
            "PASS",
        ),
        (
            {
                "active_infection": True,
                "major_cardiovascular_exclusion": False,
                "major_surgery_within_14d": False,
                "radiotherapy_within_14d": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "active_infection": False,
                "major_cardiovascular_exclusion": True,
                "major_surgery_within_14d": False,
                "radiotherapy_within_14d": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "active_infection": False,
                "major_cardiovascular_exclusion": False,
                "major_surgery_within_14d": True,
                "radiotherapy_within_14d": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "active_infection": False,
                "major_cardiovascular_exclusion": False,
                "major_surgery_within_14d": False,
                "radiotherapy_within_14d": True,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "active_infection": None,
                "major_cardiovascular_exclusion": False,
                "major_surgery_within_14d": False,
                "radiotherapy_within_14d": False,
            },
            "UNCERTAIN",
        ),
    ],
)

def test_rule10_safety_exclusion_bucket(patient, expected):
    assert rule_safety_exclusion_bucket(patient)["verdict"] == expected
def test_rule10_multiple_triggers():
    patient = {
        "active_infection": True,
        "major_cardiovascular_exclusion": True,
        "major_surgery_within_14d": False,
        "radiotherapy_within_14d": False,
    }
    out = rule_safety_exclusion_bucket(patient)
    assert out["verdict"] == "NOT_ELIGIBLE"
    assert len(out["triggered"]) == 2

import pytest


@pytest.mark.parametrize(
    "patient, expected",
    [
        (
            {
                "anc_x10e9_l": 1.2,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 80,
                "bone_marrow_plasma_cells_percent": 30,
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.2,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "PASS",
        ),
        (
            {
                "anc_x10e9_l": 0.8,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 80,
                "bone_marrow_plasma_cells_percent": 30,
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.2,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "anc_x10e9_l": 1.2,
                "hb_g_dl": 7.4,
                "platelets_x10e9_l": 80,
                "bone_marrow_plasma_cells_percent": 30,
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.2,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "anc_x10e9_l": 1.2,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 70,
                "bone_marrow_plasma_cells_percent": 30,  # 需要 >=75
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.2,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "anc_x10e9_l": 1.2,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 55,
                "bone_marrow_plasma_cells_percent": 60,  # 需要 >=50
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.2,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "PASS",
        ),
        (
            {
                "anc_x10e9_l": 1.2,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 80,
                "bone_marrow_plasma_cells_percent": 30,
                "alt_x_uln": 2.6,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.2,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "anc_x10e9_l": 1.2,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 80,
                "bone_marrow_plasma_cells_percent": 30,
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.8,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "NOT_ELIGIBLE",
        ),
        (
            {
                "anc_x10e9_l": 1.2,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 80,
                "bone_marrow_plasma_cells_percent": 30,
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.8,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": True,
            },
            "PASS",
        ),
        (
            {
                "anc_x10e9_l": None,
                "hb_g_dl": 8.0,
                "platelets_x10e9_l": 80,
                "bone_marrow_plasma_cells_percent": 30,
                "alt_x_uln": 1.0,
                "ast_x_uln": 1.0,
                "total_bilirubin_x_uln": 1.2,
                "hb_supported_by_transfusion": False,
                "plt_supported_by_transfusion": False,
                "gilbert_exception": False,
            },
            "UNCERTAIN",
        ),
    ],
)
def test_rule11_lab_threshold_bucket(patient, expected):
    assert rule_lab_threshold_bucket(patient)["verdict"] == expected

def test_rule11_hb_supported_by_transfusion_fails():
    patient = {
        "anc_x10e9_l": 1.2,
        "hb_g_dl": 7.8,
        "platelets_x10e9_l": 80,
        "bone_marrow_plasma_cells_percent": 30,
        "alt_x_uln": 1.0,
        "ast_x_uln": 1.0,
        "total_bilirubin_x_uln": 1.2,
        "hb_supported_by_transfusion": True,
        "plt_supported_by_transfusion": False,
        "gilbert_exception": False,
    }
    out = rule_lab_threshold_bucket(patient)
    assert out["verdict"] == "NOT_ELIGIBLE"


def test_rule11_platelet_threshold_switches_by_marrow_pc():
    patient = {
        "anc_x10e9_l": 1.2,
        "hb_g_dl": 8.0,
        "platelets_x10e9_l": 60,
        "bone_marrow_plasma_cells_percent": 49.9,
        "alt_x_uln": 1.0,
        "ast_x_uln": 1.0,
        "total_bilirubin_x_uln": 1.2,
        "hb_supported_by_transfusion": False,
        "plt_supported_by_transfusion": False,
        "gilbert_exception": False,
    }
    out = rule_lab_threshold_bucket(patient)
    assert out["verdict"] == "NOT_ELIGIBLE"