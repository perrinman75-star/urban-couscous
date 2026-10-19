from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)

from . import db
from .flows import (AC_ROWS, INTAG, SERVICE_NAMES, ac_rows, definition_of_ready,
                    escalate_to_a, get_step, missing_fields, next_open_step,
                    step_states, steps_for)
from .scoring import (COMPLEXITY_CRITERIA, TRIAGE_QUESTIONS, VALUE_CRITERIA,
                      business_case, prioscore, triage_service)

bp = Blueprint("kravfangst", __name__)


@bp.app_template_filter("num")
def num(value, suffix=""):
    """Svenskt talformat: 1,24 · 62 % · 5 000 tkr. Tomt värde blir –."""
    if value is None or value == "":
        return "–"
    value = round(float(value), 2)
    text = f"{value:,.2f}".rstrip("0").rstrip(".").replace(",", " ").replace(".", ",")
    return text + suffix


@bp.app_context_processor
def globals_():
    return {"SERVICE_NAMES": SERVICE_NAMES, "AC_ROWS": AC_ROWS}


def _load(case_id):
    case = db.get_case(case_id)
    if case is None:
        abort(404)
    return case


def _read_form(step, data, goals):
    """Läs stegets fält från formuläret in i ärendets data."""
    form = request.form
    for f in step.fields:
        if f.type == "checkbox":
            data[f.name] = "on" if form.get(f.name) else ""
        elif f.type == "ac_list":
            for i in range(AC_ROWS):
                for part in ("givet", "nar", "sa"):
                    key = f"ac_{i}_{part}"
                    data[key] = form.get(key, "").strip()
        else:
            data[f.name] = form.get(f.name, "").strip()
    if step.kind == "prioscore":
        for goal in goals:
            data[f"s_{goal['id']}"] = form.get(f"s_{goal['id']}", "").strip()
    return data


def _service_after_triage(data):
    override = data.get("triage_overstyr")
    return override if override in ("A", "B") else triage_service(data)


@bp.route("/")
def index():
    goals = db.list_goals()
    cases = []
    for case in db.list_cases():
        data, service = case["data"], case["tjanst"]
        score = prioscore(data, goals) if service == "A" else None
        states = step_states(service, data, None, goals)
        done = sum(1 for s in states if s["done"])
        cases.append({**case, "score": score, "progress": (done, len(states)),
                      "next": next_open_step(service, data, goals)})
    portfolio = sorted((c for c in cases if c["score"] and c["score"].score is not None),
                       key=lambda c: c["score"].score, reverse=True)
    return render_template("index.html", cases=cases, portfolio=portfolio)


@bp.route("/nytt", methods=["GET", "POST"])
def new_case():
    data = {}
    errors = []
    if request.method == "POST":
        data = _read_form(INTAG, {}, [])
        errors = missing_fields(INTAG, data)
        if not errors:
            case_id = db.create_case(data)
            return redirect(url_for(".step", case_id=case_id, key="triage"))
    crumbs = step_states(None, data, "intag")
    return render_template("step.html", case=None, step=INTAG, data=data, errors=errors,
                           crumbs=crumbs, service=None)


@bp.route("/arende/<int:case_id>")
def case_start(case_id):
    case = _load(case_id)
    nxt = next_open_step(case["tjanst"], case["data"], db.list_goals())
    return redirect(url_for(".step", case_id=case_id, key=nxt.key))


@bp.route("/arende/<int:case_id>/<key>", methods=["GET", "POST"])
def step(case_id, key):
    case = _load(case_id)
    goals = db.list_goals()
    service, data = case["tjanst"], case["data"]
    current = get_step(service, key)
    if current is None:
        abort(404)

    crumbs = step_states(service, data, key, goals)
    if next(c for c in crumbs if c["step"].key == key)["state"] == "locked":
        flash("Gör klart tidigare steg först.")
        return redirect(url_for(".case_start", case_id=case_id))

    errors = []
    if request.method == "POST":
        data = _read_form(current, data, goals)
        if current.kind == "triage":
            service = _service_after_triage(data)
        if current.key == "prioritera" and data.get("eskalera") == "on":
            data = escalate_to_a(data)
            db.save_case(case_id, data, "A")
            flash("Ärendet är eskalerat till Tjänst A. Det som redan skrivits är återanvänt.")
            return redirect(url_for(".step", case_id=case_id, key="problem"))
        db.save_case(case_id, data, service)
        if request.form.get("action") == "save":
            flash("Utkastet är sparat.")
            return redirect(url_for(".step", case_id=case_id, key=key))
        errors = missing_fields(current, data, service, goals)
        if not errors:
            steps = steps_for(service)
            idx = [s.key for s in steps].index(key)
            return redirect(url_for(".step", case_id=case_id, key=steps[idx + 1].key))
        crumbs = step_states(service, data, key, goals)

    case = {**case, "tjanst": service, "data": data}
    ctx = dict(case=case, step=current, data=data, errors=errors, crumbs=crumbs,
               service=service, goals=goals)
    if current.kind == "triage":
        ctx["recommended"] = triage_service(data)
        ctx["questions"] = TRIAGE_QUESTIONS
    if current.kind == "prioscore":
        ctx.update(score=prioscore(data, goals), value_criteria=VALUE_CRITERIA,
                   complexity_criteria=COMPLEXITY_CRITERIA)
    if current.kind == "result":
        return _result(ctx, goals)
    return render_template("step.html", **ctx)


def _result(ctx, goals):
    data, service = ctx["data"], ctx["service"]
    if service == "A":
        score = prioscore(data, goals)
        bc = business_case(data)
        ctx.update(score=score, bc=bc, dor=definition_of_ready("A", data, score.score, bc.roi),
                   contributions=[(g_, data.get(f"s_{g_['id']}")) for g_ in goals],
                   epics=[e for e in (data.get("epics") or "").splitlines() if e.strip()])
        return render_template("executive_summary.html", **ctx)
    ctx.update(dor=definition_of_ready("B", data), acs=ac_rows(data))
    return render_template("user_story.html", **ctx)


@bp.route("/arende/<int:case_id>/radera", methods=["POST"])
def delete(case_id):
    _load(case_id)
    db.delete_case(case_id)
    flash("Ärendet är raderat.")
    return redirect(url_for(".index"))


@bp.route("/mal", methods=["GET", "POST"])
def goals():
    errors = []
    goals_ = db.list_goals()
    if request.method == "POST":
        ids = request.form.getlist("id")
        names = request.form.getlist("name")
        weights = request.form.getlist("weight")
        goals_ = []
        for id_, name, weight in zip(ids, names, weights):
            if not name.strip():
                continue
            try:
                w = float(weight)
            except ValueError:
                errors.append(f"Vikten för {name} måste vara ett tal.")
                w = 0
            goals_.append({"id": int(id_) if id_ else None, "name": name.strip(), "weight": w})
        total = sum(g_["weight"] for g_ in goals_)
        if goals_ and abs(total - 100) > 0.01:
            errors.append(f"Vikterna måste summera till 100 % (nu {total:g} %).")
        if not goals_:
            errors.append("Ange minst ett strategiskt mål.")
        if not errors:
            db.save_goals(goals_)
            flash("De strategiska målen är sparade.")
            return redirect(url_for(".goals"))
    return render_template("goals.html", goals=goals_, errors=errors)
