from kravfangst.scoring import business_case, prioscore, triage_service

GOALS = [{"id": 1, "name": "Mål 1", "weight": 40},
         {"id": 2, "name": "Mål 2", "weight": 35},
         {"id": 3, "name": "Mål 3", "weight": 25}]


def scores(value, complexity):
    data = {k: value for k in ("v_ekonomi", "v_kund", "v_regel", "v_tid")}
    data.update({k: complexity for k in ("c_teknik", "c_beroenden", "c_organisation", "c_osakerhet")})
    return data


def test_triage_one_yes_gives_a():
    answers = {k: "nej" for k in ("t_kostnad", "t_omfattning", "t_strategi", "t_regelverk", "t_risk")}
    assert triage_service(answers) == "B"
    answers["t_risk"] = "ja"
    assert triage_service(answers) == "A"


def test_triage_incomplete_is_none():
    assert triage_service({"t_kostnad": "ja"}) is None


def test_prioscore_matches_presentation_example():
    # Exemplet i presentationen: 8 × 0,62 ÷ 4 = 1,24
    data = scores(8, 4) | {"s_1": 90, "s_2": 60, "s_3": 20}
    p = prioscore(data, GOALS)
    assert p.value == 8
    assert p.complexity == 4
    assert p.alignment == 62
    assert p.coefficient == 0.62
    assert p.score == 1.24
    assert p.level == "Prioritera vid kapacitet"


def test_prioscore_weights_value_criteria():
    data = scores(5, 5) | {"v_ekonomi": 10, "s_1": 100, "s_2": 100, "s_3": 100}
    # 10×0,4 + 5×0,3 + 5×0,2 + 5×0,1 = 7
    assert prioscore(data, GOALS).value == 7


def test_prioscore_levels():
    full = {"s_1": 100, "s_2": 100, "s_3": 100}
    assert prioscore(scores(9, 3) | full, GOALS).level == "Hög prioritet"
    assert prioscore(scores(3, 9) | full, GOALS).level == "Utmana eller omforma"


def test_prioscore_incomplete_and_out_of_range():
    assert prioscore({}, GOALS).score is None
    assert prioscore(scores(11, 4) | {"s_1": 1, "s_2": 1, "s_3": 1}, GOALS).value is None


def test_business_case_matches_template_example():
    # Mallens exempel: affärsvärde 5 000, kostnad 3 000 + 150 → ROI 59 %
    bc = business_case({"okade_intakter": 4000, "besparing": 1000, "livslangd_ar": 1,
                        "kostnad_implementering": 3000, "kostnad_lopande": 150})
    assert bc.business_value == 5000
    assert bc.total_cost == 3150
    assert round(bc.roi) == 59


def test_business_case_without_cost_has_no_roi():
    assert business_case({}).roi is None
