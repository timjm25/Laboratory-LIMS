"""
Flask application factory for Laboratory LIMS.
Port 5109.
"""
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

from lims.model import Model
from lims.seed import seed as _seed


def create_app(db_path: str = ":memory:") -> Flask:
    app = Flask(__name__, template_folder="templates")
    app._lims_model = None

    def _model() -> Model:
        if app._lims_model is None:
            m = Model(db_path)
            _seed(m)
            app._lims_model = m
        return app._lims_model

    # ── Health ────────────────────────────────────────────────────────────────

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok", "service": "Laboratory LIMS"})

    # ── Dashboard ─────────────────────────────────────────────────────────────

    @app.get("/")
    def dashboard():
        m = _model()
        stats = m.dashboard_stats()
        recent_samples = m.list_samples()[:5]
        pending_tests = m.list_tests(status="Requested") + m.list_tests(status="In Progress")
        pending_tests = pending_tests[:8]
        instruments_attention = [
            i for i in m.list_instruments()
            if i["status"] in ("Due for Calibration", "Out of Service")
        ]
        reagents_attention = [
            r for r in m.list_reagents()
            if r["status"] in ("Expired", "Low Stock", "Quarantined")
        ]
        return render_template(
            "dashboard.html",
            stats=stats,
            recent_samples=recent_samples,
            pending_tests=pending_tests,
            instruments_attention=instruments_attention,
            reagents_attention=reagents_attention,
        )

    # ── Samples ───────────────────────────────────────────────────────────────

    @app.get("/samples")
    def samples_list():
        m = _model()
        sample_type = request.args.get("sample_type", "")
        status = request.args.get("status", "")
        priority = request.args.get("priority", "")
        client = request.args.get("client", "")
        samples = m.list_samples(
            sample_type=sample_type or None,
            status=status or None,
            priority=priority or None,
            client=client or None,
        )
        return render_template(
            "samples.html",
            samples=samples,
            filters={"sample_type": sample_type, "status": status, "priority": priority, "client": client},
        )

    @app.get("/sample/<sample_id>")
    def sample_detail(sample_id):
        m = _model()
        sample = m.get_sample(sample_id)
        if not sample:
            abort(404)
        tests = m.get_sample_tests(sample_id)
        return render_template("sample_detail.html", sample=sample, tests=tests)

    @app.post("/sample/<sample_id>/status")
    def update_sample_status(sample_id):
        m = _model()
        new_status = request.form.get("status", "")
        m.update_sample_status(sample_id, new_status)
        return redirect(url_for("sample_detail", sample_id=sample_id))

    # ── Tests ─────────────────────────────────────────────────────────────────

    @app.get("/tests")
    def tests_list():
        m = _model()
        status = request.args.get("status", "")
        assigned_to = request.args.get("assigned_to", "")
        pass_fail = request.args.get("pass_fail", "")
        tests = m.list_tests(
            status=status or None,
            assigned_to=assigned_to or None,
            pass_fail=pass_fail or None,
        )
        return render_template(
            "tests.html",
            tests=tests,
            filters={"status": status, "assigned_to": assigned_to, "pass_fail": pass_fail},
        )

    # ── Instruments ───────────────────────────────────────────────────────────

    @app.get("/instruments")
    def instruments_list():
        m = _model()
        status = request.args.get("status", "")
        department = request.args.get("department", "")
        instruments = m.list_instruments(
            status=status or None,
            department=department or None,
        )
        return render_template(
            "instruments.html",
            instruments=instruments,
            filters={"status": status, "department": department},
        )

    # ── Reagents ──────────────────────────────────────────────────────────────

    @app.get("/reagents")
    def reagents_list():
        m = _model()
        status = request.args.get("status", "")
        category = request.args.get("category", "")
        reagents = m.list_reagents(
            status=status or None,
            category=category or None,
        )
        return render_template(
            "reagents.html",
            reagents=reagents,
            filters={"status": status, "category": category},
        )

    # ── REST API ──────────────────────────────────────────────────────────────

    @app.get("/api/v1/samples")
    def api_samples():
        m = _model()
        return jsonify(m.list_samples(
            sample_type=request.args.get("sample_type"),
            status=request.args.get("status"),
            priority=request.args.get("priority"),
            client=request.args.get("client"),
        ))

    @app.get("/api/v1/sample/<sample_id>")
    def api_sample(sample_id):
        m = _model()
        s = m.get_sample(sample_id)
        if not s:
            return jsonify({"error": "not found"}), 404
        return jsonify({"sample": s, "tests": m.get_sample_tests(sample_id)})

    @app.get("/api/v1/tests")
    def api_tests():
        m = _model()
        return jsonify(m.list_tests(
            status=request.args.get("status"),
            assigned_to=request.args.get("assigned_to"),
            pass_fail=request.args.get("pass_fail"),
        ))

    @app.get("/api/v1/instruments")
    def api_instruments():
        m = _model()
        return jsonify(m.list_instruments(
            status=request.args.get("status"),
            department=request.args.get("department"),
        ))

    @app.get("/api/v1/reagents")
    def api_reagents():
        m = _model()
        return jsonify(m.list_reagents(
            status=request.args.get("status"),
            category=request.args.get("category"),
        ))

    @app.get("/api/v1/stats")
    def api_stats():
        return jsonify(_model().dashboard_stats())

    return app
