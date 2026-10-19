"""Stegen i de två kravfångsttjänsterna.

Tjänst A – större initiativ:  Intag › Triage › Problem & effekter › Lösning & scope
                              › Business case › Prioscore › Beslut › Executive summary
Tjänst B – mindre vidareutv.: Intag › Triage › User story › Prioritera
                              › Redo & återkoppla › Färdig user story
"""

from dataclasses import dataclass, field

from .scoring import COMPLEXITY_CRITERIA, TRIAGE_QUESTIONS, VALUE_CRITERIA

AC_ROWS = 5


@dataclass
class Field:
    name: str
    label: str
    type: str = "text"  # text, textarea, number, date, select, checkbox, ac_list
    required: bool = False
    help: str = ""
    choices: list = field(default_factory=list)
    placeholder: str = ""


@dataclass
class Step:
    key: str
    title: str
    intro: str
    kind: str = "form"  # form, triage, prioscore, result
    fields: list = field(default_factory=list)
    who: str = ""


INTAG = Step(
    "intag", "Intag", "Registrera behovet. Alla behov kommer in på samma ställe.",
    who="Initiativtagare / beställare",
    fields=[
        Field("titel", "Titel", required=True, placeholder="Kort namn på behovet"),
        Field("bestallare", "Beställare / initiativtagare", required=True),
        Field("system", "Berört system, produkt eller verksamhetsområde"),
        Field("beskrivning", "Beskriv behovet", "textarea", required=True,
              help="Vad fungerar inte eller saknas idag, och vem påverkas?"),
    ],
)

TRIAGE = Step(
    "triage", "Triage",
    "Ett enda ja leder till Tjänst A (större initiativ). Annars Tjänst B (mindre vidareutveckling).",
    kind="triage", who="Produktägare + portföljansvarig",
    fields=[Field(key, f"{label} – {question}", "select", required=True, choices=["ja", "nej"])
            for key, label, question in TRIAGE_QUESTIONS]
    + [Field("triage_overstyr", "Överstyr tjänst", "select", choices=["", "A", "B"],
             help="Används bara vid tveksamhet – motivera nedan."),
       Field("triage_motivering", "Motivering till överstyrning", "textarea")],
)

STEPS_A = [
    Step("problem", "Problem & effekter", "Workshop 1 med verksamheten.",
         who="Workshop 1 – verksamhet",
         fields=[
             Field("sponsor", "Sponsor", required=True),
             Field("problem", "Vad är problemet?", "textarea", required=True),
             Field("vem_problem", "Vem har problemet?", "textarea", required=True),
             Field("varfor_viktigt", "Varför är det viktigt – varför nu?", "textarea"),
             Field("effekter", "Vad vill vi uppnå? Finansiella och icke-finansiella effekter",
                   "textarea", required=True),
             Field("intressenter", "Intressenter och deras prioriterade behov", "textarea",
                   required=True),
         ]),
    Step("losning", "Lösning & scope", "Workshop 2 med verksamhet, IT och arkitektur.",
         who="Workshop 2 – verksamhet, IT, arkitektur",
         fields=[
             Field("losning", "Föreslagen lösning", "textarea", required=True),
             Field("scope", "Scope – vad innehåller lösningen?", "textarea", required=True),
             Field("avgransningar", "Begränsningar och avgränsningar", "textarea"),
             Field("mvp", "MVP – minsta första leverans", "textarea", required=True),
             Field("resurser", "Resurser – interna och externa", "textarea", required=True),
             Field("tidskritiskt", "Hur tidskritiskt är det?", "textarea"),
             Field("tid", "Ungefärlig start och leveranstid"),
         ]),
    Step("business_case", "Business case", "Kostnad, nytta, ROI, risker och mätpunkter.",
         who="Kravanalytiker + ekonomi",
         fields=[
             Field("okade_intakter", "Ökade intäkter per år (tkr)", "number"),
             Field("besparing", "Besparing per år (tkr)", "number"),
             Field("kostnad_implementering", "Implementeringskostnad (tkr)", "number",
                   required=True),
             Field("kostnad_lopande", "Löpande kostnad per år (tkr)", "number"),
             Field("livslangd_ar", "Investeringens livslängd (år)", "number", required=True),
             Field("risker", "Risker – vad kan gå fel, konsekvenser och åtgärder", "textarea",
                   required=True),
             Field("matpunkter", "Mätpunkter – hur vet vi att vi lyckats?", "textarea",
                   required=True),
         ]),
    Step("prioscore", "Prioscore",
         "Poängsätt affärsvärde och komplexitet (1–10) och initiativets bidrag till varje "
         "strategiskt mål (0–100 %).",
         kind="prioscore", who="Kravanalytiker + portföljansvarig",
         fields=[Field(key, label, "number", required=True) for key, label, _ in
                 VALUE_CRITERIA + COMPLEXITY_CRITERIA]),
    Step("beslut", "Beslut & redo", "Godkännande och go / no-go i portföljforum.",
         who="Portföljforum, juridik/compliance",
         fields=[
             Field("juridik_godkand", "Godkänt av juridik/compliance", "checkbox", required=True),
             Field("rekommendation", "Rekommendation till beslut", "textarea", required=True),
             Field("beslut", "Beslut", "select", required=True,
                   choices=["", "Go", "No-go", "Omforma"]),
             Field("beslutsdatum", "Beslutsdatum", "date", required=True),
             Field("epics", "Epics i backlog (en per rad)", "textarea"),
         ]),
    Step("resultat", "Executive summary", "", kind="result"),
]

STEPS_B = [
    Step("user_story", "User story",
         "Skriv behovet som en user story och sätt acceptanskriterier tillsammans med teamet.",
         who="Produktägare + beställare + team",
         fields=[
             Field("roll", "Som …", required=True, placeholder="roll/användare"),
             Field("vill", "vill jag …", required=True, placeholder="behov/förmåga"),
             Field("sa_att", "så att …", required=True, placeholder="nytta/värde"),
             Field("bakgrund", "Behov & bakgrund", "textarea",
                   help="Nuvarande arbetssätt, workaround, hur ofta det inträffar."),
             Field("nytta_matpunkt", "Nytta & mätpunkt", "textarea",
                   help="Vad blir bättre och hur följer vi upp det?"),
             Field("paverkan", "Påverkan & beroenden", "textarea",
                   help="Berörda system, integrationer, personuppgifter, regelverk."),
             Field("ac", "Acceptanskriterier", "ac_list", required=True),
         ]),
    Step("prioritera", "Prioritera", "Värde mot insats och placering i backlog.",
         who="Produktägare / förvaltningsforum",
         fields=[
             Field("storlek", "Storlek", "select", required=True,
                   choices=["", "S (<1 v)", "M (1–2 v)", "L (2–4 v)"]),
             Field("prioritet", "Prioritet", "select", required=True,
                   choices=["", "Hög", "Medel", "Låg"]),
             Field("po_prioriterad", "Prioriterad av produktägare", "checkbox", required=True),
             Field("eskalera", "Större än väntat – eskalera till Tjänst A", "checkbox",
                   help="Flyttar ärendet till Tjänst A och återanvänder det som redan skrivits."),
         ]),
    Step("redo", "Redo & återkoppla", "Definition of Ready och besked till beställaren.",
         who="Produktägare",
         fields=[
             Field("bestallare_godkand", "Godkänd av beställaren", "checkbox", required=True),
             Field("redo_datum", "Redo för utveckling (datum)", "date", required=True),
             Field("aterkoppling", "Återkoppling till beställaren", "textarea"),
         ]),
    Step("resultat", "Färdig user story", "", kind="result"),
]

SERVICE_NAMES = {"A": "Tjänst A – Större initiativ", "B": "Tjänst B – Mindre vidareutveckling"}


def steps_for(service):
    service_steps = {"A": STEPS_A, "B": STEPS_B}.get(service, [])
    return [INTAG, TRIAGE] + service_steps


def get_step(service, key):
    return next((s for s in steps_for(service) if s.key == key), None)


def ac_rows(data):
    rows = []
    for i in range(AC_ROWS):
        row = {part: (data.get(f"ac_{i}_{part}") or "").strip()
               for part in ("givet", "nar", "sa")}
        if any(row.values()):
            rows.append(row)
    return rows


def _filled(field_, data):
    if field_.type == "ac_list":
        return any(all(r.values()) for r in ac_rows(data))
    value = data.get(field_.name)
    if field_.type == "checkbox":
        return value == "on"
    return value not in (None, "")


def missing_fields(step, data, service=None, goals=()):
    missing = [f.label for f in step.fields if f.required and not _filled(f, data)]
    if step.kind == "triage" and not service:
        missing.append("Tjänst")
    if step.kind == "prioscore":
        missing += [f"Bidrag till {g['name']}" for g in goals
                    if data.get(f"s_{g['id']}") in (None, "")]
    return missing


def step_states(service, data, current_key, goals=()):
    """Status per steg för brödsmulorna: done, current, open eller locked."""
    states = []
    blocked = False
    for step in steps_for(service):
        if step.kind == "result":
            done = not blocked
            missing = []
        else:
            missing = missing_fields(step, data, service, goals)
            done = not missing
        if blocked:
            state = "locked"
        elif step.key == current_key:
            state = "current"
        else:
            state = "done" if done else "open"
        states.append({"step": step, "state": state, "done": done and not blocked})
        if not done:
            blocked = True
    if service is None:
        states.append({"step": Step("tjanst", "Tjänstens steg", ""), "state": "locked",
                       "done": False})
    return states


def next_open_step(service, data, goals=()):
    for s in step_states(service, data, None, goals):
        if not s["done"]:
            return s["step"]
    return steps_for(service)[-1]


def definition_of_ready(service, data, score=None, roi=None):
    """Checklistan från presentationen, utvärderad mot ärendets data."""
    def has(*keys):
        return all(data.get(k) not in (None, "") for k in keys)

    if service == "A":
        return [
            ("Canvas A ifylld (problem, lösning, scope, resurser)",
             has("problem", "losning", "scope", "resurser")),
            ("Problem, effekter och mätpunkter överenskomna",
             has("problem", "effekter", "matpunkter")),
            ("Kostnad och ROI uppskattade", roi is not None),
            ("Executive summary med prioscore klar", score is not None),
            ("Godkänt av juridik/compliance", data.get("juridik_godkand") == "on"),
            ("Go-beslut i portföljforum", data.get("beslut") == "Go"),
            ("Epics och MVP-scope i backlog", has("epics", "mvp")),
        ]
    return [
        ("User story: Som … vill jag … så att …", has("roll", "vill", "sa_att")),
        ("Behov och bakgrund beskrivna", has("bakgrund")),
        ("Acceptanskriterier skrivna (Givet/När/Så)",
         any(all(r.values()) for r in ac_rows(data))),
        ("Estimerad och prioriterad", has("storlek", "prioritet")
         and data.get("po_prioriterad") == "on"),
        ("Beroenden och regelpåverkan kontrollerade", has("paverkan")),
        ("Godkänd av beställaren", data.get("bestallare_godkand") == "on"),
    ]


def escalate_to_a(data):
    """Återanvänd det som skrivits i Tjänst B när ärendet lyfts till Tjänst A."""
    mapped = dict(data)
    story = f"Som {data.get('roll', '')} vill jag {data.get('vill', '')} " \
            f"så att {data.get('sa_att', '')}".strip()
    mapped.setdefault("problem", "\n\n".join(
        p for p in (data.get("beskrivning"), data.get("bakgrund")) if p))
    mapped.setdefault("vem_problem", data.get("roll", ""))
    mapped.setdefault("effekter", "\n".join(
        p for p in (data.get("sa_att"), data.get("nytta_matpunkt")) if p))
    mapped.setdefault("losning", story)
    mapped["eskalerad_fran_b"] = "on"
    mapped["eskalera"] = ""
    return mapped
