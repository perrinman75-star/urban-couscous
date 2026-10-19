"""Beräkningar för triage, prioscore och ROI.

Prioscore = Affärsvärde × Strategikoefficient ÷ Komplexitet

* Affärsvärde och komplexitet är viktade snitt av poäng 1–10.
* Strategikoppling är summan av (målets vikt × initiativets bidrag) i procent,
  och koefficienten är den summan delad med 100 (0–1).
"""

from dataclasses import dataclass

VALUE_CRITERIA = [
    ("v_ekonomi", "Ekonomisk effekt (intäkt/besparing)", 0.40),
    ("v_kund", "Kund- och användarnytta", 0.30),
    ("v_regel", "Regelefterlevnad & riskreducering", 0.20),
    ("v_tid", "Tidskritikalitet", 0.10),
]

COMPLEXITY_CRITERIA = [
    ("c_teknik", "Teknisk komplexitet", 0.25),
    ("c_beroenden", "Beroenden & integrationer", 0.25),
    ("c_organisation", "Organisatorisk förändring", 0.25),
    ("c_osakerhet", "Osäkerhet & ny teknik", 0.25),
]

TRIAGE_QUESTIONS = [
    ("t_kostnad", "Kostnad", "Uppskattad insats över ~300 timmar eller extern investering?"),
    ("t_omfattning", "Omfattning", "Berörs flera system, team eller verksamhetsområden?"),
    ("t_strategi", "Strategi", "Är det en ny förmåga, tjänst eller kundgrupp?"),
    ("t_regelverk", "Regelverk",
     "Påverkas juridik, compliance, informationssäkerhet eller personuppgifter väsentligt?"),
    ("t_risk", "Risk", "Skulle ett misslyckande ge stor påverkan på kunder eller verksamhet?"),
]

HIGH_PRIORITY = 1.5
MEDIUM_PRIORITY = 1.0


def triage_service(answers):
    """Ett enda ja ger Tjänst A, annars Tjänst B. None om något är obesvarat."""
    values = [answers.get(key) for key, _, _ in TRIAGE_QUESTIONS]
    if any(v not in ("ja", "nej") for v in values):
        return None
    return "A" if "ja" in values else "B"


def _score(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if 1 <= score <= 10 else None


def weighted_score(data, criteria):
    """Viktat snitt av poäng 1–10, eller None om något kriterium saknas."""
    scores = [_score(data.get(key)) for key, _, _ in criteria]
    if any(s is None for s in scores):
        return None
    return round(sum(s * w for s, (_, _, w) in zip(scores, criteria)), 2)


def strategy_alignment(data, goals):
    """Strategikoppling i procent (0–100) givet målens vikter och bidrag."""
    if not goals:
        return None
    total = 0.0
    for goal in goals:
        try:
            contribution = float(data.get(f"s_{goal['id']}"))
        except (TypeError, ValueError):
            return None
        contribution = min(max(contribution, 0.0), 100.0)
        total += goal["weight"] / 100 * contribution
    return round(total, 1)


@dataclass
class Prioscore:
    value: float | None
    complexity: float | None
    alignment: float | None

    @property
    def coefficient(self):
        return None if self.alignment is None else round(self.alignment / 100, 2)

    @property
    def score(self):
        if None in (self.value, self.complexity, self.alignment):
            return None
        return round(self.value * self.coefficient / self.complexity, 2)

    @property
    def level(self):
        if self.score is None:
            return None
        if self.score >= HIGH_PRIORITY:
            return "Hög prioritet"
        if self.score >= MEDIUM_PRIORITY:
            return "Prioritera vid kapacitet"
        return "Utmana eller omforma"


def prioscore(data, goals):
    return Prioscore(
        value=weighted_score(data, VALUE_CRITERIA),
        complexity=weighted_score(data, COMPLEXITY_CRITERIA),
        alignment=strategy_alignment(data, goals),
    )


def _amount(data, key):
    try:
        return float(data.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class BusinessCase:
    business_value: float
    total_cost: float

    @property
    def roi(self):
        """ROI i procent: (affärsvärde − kostnad) ÷ kostnad."""
        if self.total_cost <= 0:
            return None
        return round((self.business_value - self.total_cost) / self.total_cost * 100, 1)


def business_case(data):
    """Affärsvärde och kostnad över investeringens livstid (tkr)."""
    years = max(_amount(data, "livslangd_ar"), 1)
    value = (_amount(data, "okade_intakter") + _amount(data, "besparing")) * years
    cost = _amount(data, "kostnad_implementering") + _amount(data, "kostnad_lopande") * years
    return BusinessCase(business_value=value, total_cost=cost)
