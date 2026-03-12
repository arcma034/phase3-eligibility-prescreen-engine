def screen_step1(patient: dict) -> dict:
    """
    第1条纳排规则：既往用过 anti-CD38 单抗 => 一票否决
    输出三态：
      - NOT_ELIGIBLE：触发排除
      - UNCERTAIN：信息缺失
      - PASS：通过这一条（不等于最终Eligible）
    """
    prior = patient.get("prior_anti_cd38")  # True / False / None

    if prior is True:
        return {"verdict": "NOT_ELIGIBLE", "reason": "EXC: prior anti-CD38 therapy", "missing": []}

    if prior is None:
        return {"verdict": "UNCERTAIN", "reason": "Missing key field",
                "missing": ["prior_anti_cd38 (是否用过抗CD38单抗)"]}

    return {"verdict": "PASS", "reason": "No prior anti-CD38 found", "missing": []}


if __name__ == "__main__":
    patient_example = {"prior_anti_cd38": None}  # 改成 True / False 试试
    print(screen_step1(patient_example))