import re

import pytest

from kravfangst import create_app

NO = {k: "nej" for k in ("t_kostnad", "t_omfattning", "t_strategi", "t_regelverk", "t_risk")}


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    return app.test_client()


def new_case(client, title="Exportera rapport"):
    r = client.post("/nytt", data={"titel": title, "bestallare": "Anna",
                                   "beskrivning": "Rapporten går inte att exportera."})
    assert r.status_code == 302
    return int(re.search(r"/arende/(\d+)/triage", r.location).group(1))


def test_intake_requires_fields(client):
    r = client.post("/nytt", data={"titel": ""})
    assert "Fyll i för att gå vidare" in r.get_data(as_text=True)


def test_breadcrumbs_lock_later_steps(client):
    case_id = new_case(client)
    page = client.get(f"/arende/{case_id}/triage").get_data(as_text=True)
    assert 'aria-current="step"' in page
    assert "Tjänstens steg" in page
    # Ett låst steg går inte att öppna direkt
    r = client.post(f"/arende/{case_id}/triage", data={**NO, "action": "save"})
    r = client.get(f"/arende/{case_id}/redo")
    assert r.status_code == 302


def test_service_b_produces_user_story(client):
    case_id = new_case(client)
    r = client.post(f"/arende/{case_id}/triage", data={**NO, "action": "next"})
    assert r.location.endswith(f"/arende/{case_id}/user_story")

    r = client.post(f"/arende/{case_id}/user_story", data={
        "roll": "handläggare", "vill": "exportera rapporten till Excel",
        "sa_att": "jag slipper skriva av siffror", "bakgrund": "Görs manuellt varje vecka",
        "paverkan": "Rapportmodulen", "ac_0_givet": "en öppen rapport",
        "ac_0_nar": "jag klickar Exportera", "ac_0_sa": "laddas en xlsx-fil ner",
        "action": "next"})
    assert r.location.endswith("/prioritera")
    r = client.post(f"/arende/{case_id}/prioritera", data={
        "storlek": "S (<1 v)", "prioritet": "Hög", "po_prioriterad": "on", "action": "next"})
    assert r.location.endswith("/redo")
    r = client.post(f"/arende/{case_id}/redo", data={
        "bestallare_godkand": "on", "redo_datum": "2026-10-20", "action": "next"})
    assert r.location.endswith("/resultat")

    page = client.get(f"/arende/{case_id}/resultat").get_data(as_text=True)
    assert "exportera rapporten till Excel" in page
    assert "laddas en xlsx-fil ner" in page
    assert "Redo för utveckling" in page and "Inte redo" not in page


def test_user_story_requires_complete_acceptance_criterion(client):
    case_id = new_case(client)
    client.post(f"/arende/{case_id}/triage", data={**NO, "action": "next"})
    r = client.post(f"/arende/{case_id}/user_story", data={
        "roll": "a", "vill": "b", "sa_att": "c", "ac_0_givet": "x", "action": "next"})
    assert r.status_code == 200
    assert "Acceptanskriterier" in r.get_data(as_text=True)


def test_escalation_moves_case_to_service_a(client):
    case_id = new_case(client)
    client.post(f"/arende/{case_id}/triage", data={**NO, "action": "next"})
    client.post(f"/arende/{case_id}/user_story", data={
        "roll": "kund", "vill": "x", "sa_att": "y", "ac_0_givet": "g", "ac_0_nar": "n",
        "ac_0_sa": "s", "action": "next"})
    r = client.post(f"/arende/{case_id}/prioritera", data={"eskalera": "on", "action": "next"})
    assert r.location.endswith("/problem")
    page = client.get(f"/arende/{case_id}/problem").get_data(as_text=True)
    assert "Tjänst A – Större initiativ" in page
    assert "Rapporten går inte att exportera." in page


def test_service_a_produces_executive_summary_with_prioscore(client):
    case_id = new_case(client, "Ny kundportal")
    r = client.post(f"/arende/{case_id}/triage", data={**NO, "t_strategi": "ja", "action": "next"})
    assert r.location.endswith("/problem")
    steps = {
        "problem": {"sponsor": "Bo", "problem": "P", "vem_problem": "Kunder", "effekter": "E",
                    "intressenter": "I"},
        "losning": {"losning": "L", "scope": "S", "mvp": "M", "resurser": "R"},
        "business_case": {"okade_intakter": "4000", "besparing": "1000", "livslangd_ar": "1",
                          "kostnad_implementering": "3000", "kostnad_lopande": "150",
                          "risker": "R", "matpunkter": "M"},
        "prioscore": {"v_ekonomi": "8", "v_kund": "8", "v_regel": "8", "v_tid": "8",
                      "c_teknik": "4", "c_beroenden": "4", "c_organisation": "4",
                      "c_osakerhet": "4", "s_1": "90", "s_2": "60", "s_3": "20"},
        "beslut": {"juridik_godkand": "on", "rekommendation": "Go", "beslut": "Go",
                   "beslutsdatum": "2026-11-01", "epics": "Inloggning\nMina sidor"},
    }
    for key, data in steps.items():
        r = client.post(f"/arende/{case_id}/{key}", data={**data, "action": "next"})
        assert r.status_code == 302, (key, r.get_data(as_text=True))

    page = client.get(f"/arende/{case_id}/resultat").get_data(as_text=True)
    assert "Executive summary" in page
    assert "1,24" in page  # prioscore
    assert "0,62" in page  # strategikoefficient
    assert "58,7 %" in page  # ROI
    assert "Redo för utveckling" in page and "Inte redo" not in page

    index = client.get("/").get_data(as_text=True)
    assert "Portfölj" in index and "Ny kundportal" in index


def test_goal_weights_must_sum_to_100(client):
    r = client.post("/mal", data={"id": ["1", "2", "3", ""], "name": ["A", "B", "C", ""],
                                  "weight": ["50", "30", "30", ""]})
    assert "summera till 100" in r.get_data(as_text=True)
    r = client.post("/mal", data={"id": ["1", "2", "3", ""], "name": ["A", "B", "", ""],
                                  "weight": ["50", "50", "0", ""]})
    assert r.status_code == 302
