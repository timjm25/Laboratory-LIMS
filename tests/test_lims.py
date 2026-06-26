"""
Comprehensive tests for Laboratory LIMS.
Covers: mock data corpus, model layer, Flask routes, REST API.
"""
import pytest

from data.mock_data import MOCK_SAMPLES, MOCK_TESTS, MOCK_INSTRUMENTS, MOCK_REAGENTS
from lims.model import Model


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def model():
    m = Model(":memory:")
    m.seed()
    return m


@pytest.fixture
def client():
    from lims.app import create_app
    app = create_app(":memory:")
    return app.test_client()


# ── Mock data corpus ──────────────────────────────────────────────────────────

class TestMockData:
    def test_minimum_samples(self):
        assert len(MOCK_SAMPLES) >= 8

    def test_minimum_tests(self):
        assert len(MOCK_TESTS) >= 8

    def test_minimum_instruments(self):
        assert len(MOCK_INSTRUMENTS) >= 6

    def test_minimum_reagents(self):
        assert len(MOCK_REAGENTS) >= 8

    def test_sample_ids_unique(self):
        ids = [s["sample_id"] for s in MOCK_SAMPLES]
        assert len(ids) == len(set(ids))

    def test_test_ids_unique(self):
        ids = [t["test_id"] for t in MOCK_TESTS]
        assert len(ids) == len(set(ids))

    def test_instrument_ids_unique(self):
        ids = [i["instrument_id"] for i in MOCK_INSTRUMENTS]
        assert len(ids) == len(set(ids))

    def test_reagent_ids_unique(self):
        ids = [r["reagent_id"] for r in MOCK_REAGENTS]
        assert len(ids) == len(set(ids))

    def test_sample_required_fields(self):
        required = {"sample_id", "barcode", "sample_type", "description", "status", "priority"}
        for s in MOCK_SAMPLES:
            missing = required - set(s.keys())
            assert not missing, f"{s.get('sample_id')} missing: {missing}"

    def test_test_required_fields(self):
        required = {"test_id", "sample_id", "test_name", "method", "status"}
        for t in MOCK_TESTS:
            missing = required - set(t.keys())
            assert not missing, f"{t.get('test_id')} missing: {missing}"

    def test_instrument_required_fields(self):
        required = {"instrument_id", "name", "status", "next_calibration"}
        for i in MOCK_INSTRUMENTS:
            missing = required - set(i.keys())
            assert not missing, f"{i.get('instrument_id')} missing: {missing}"

    def test_reagent_required_fields(self):
        required = {"reagent_id", "name", "lot_number", "expiry_date", "status"}
        for r in MOCK_REAGENTS:
            missing = required - set(r.keys())
            assert not missing, f"{r.get('reagent_id')} missing: {missing}"

    def test_sample_statuses_valid(self):
        valid = {"Received", "In Progress", "Pending Review", "Approved", "Released", "Rejected"}
        for s in MOCK_SAMPLES:
            assert s["status"] in valid, f"{s['sample_id']} bad status: {s['status']}"

    def test_test_statuses_valid(self):
        valid = {"Requested", "In Progress", "Completed", "Reviewed", "Approved", "Failed"}
        for t in MOCK_TESTS:
            assert t["status"] in valid, f"{t['test_id']} bad status: {t['status']}"

    def test_instrument_statuses_valid(self):
        valid = {"Active", "Due for Calibration", "Out of Service", "Retired"}
        for i in MOCK_INSTRUMENTS:
            assert i["status"] in valid, f"{i['instrument_id']} bad status: {i['status']}"

    def test_reagent_statuses_valid(self):
        valid = {"In Stock", "Low Stock", "Expired", "Quarantined", "Depleted"}
        for r in MOCK_REAGENTS:
            assert r["status"] in valid, f"{r['reagent_id']} bad status: {r['status']}"

    def test_sample_types_cover_multiple(self):
        types = {s["sample_type"] for s in MOCK_SAMPLES}
        assert len(types) >= 4

    def test_test_sample_ids_reference_valid_samples(self):
        sample_ids = {s["sample_id"] for s in MOCK_SAMPLES}
        for t in MOCK_TESTS:
            assert t["sample_id"] in sample_ids, f"{t['test_id']} references unknown sample {t['sample_id']}"


# ── Model layer ───────────────────────────────────────────────────────────────

class TestModel:
    def test_seed_loads_samples(self, model):
        assert len(model.list_samples()) == len(MOCK_SAMPLES)

    def test_seed_loads_tests(self, model):
        assert len(model.list_tests()) == len(MOCK_TESTS)

    def test_seed_loads_instruments(self, model):
        assert len(model.list_instruments()) == len(MOCK_INSTRUMENTS)

    def test_seed_loads_reagents(self, model):
        assert len(model.list_reagents()) == len(MOCK_REAGENTS)

    def test_is_seeded_true(self, model):
        assert model.is_seeded() is True

    def test_fresh_model_not_seeded(self):
        assert Model(":memory:").is_seeded() is False

    def test_get_sample_exists(self, model):
        s = model.get_sample("S-2024-0001")
        assert s is not None
        assert s["sample_type"] == "Drug Substance"

    def test_get_sample_missing(self, model):
        assert model.get_sample("S-9999-9999") is None

    def test_get_instrument_exists(self, model):
        i = model.get_instrument("INS-001")
        assert i is not None
        assert "HPLC" in i["name"]

    def test_get_reagent_exists(self, model):
        r = model.get_reagent("RGT-001")
        assert r is not None
        assert "Acetonitrile" in r["name"]

    def test_filter_samples_by_type(self, model):
        env = model.list_samples(sample_type="Environmental")
        assert all(s["sample_type"] == "Environmental" for s in env)
        assert len(env) > 0

    def test_filter_samples_by_status(self, model):
        released = model.list_samples(status="Released")
        assert all(s["status"] == "Released" for s in released)

    def test_filter_samples_by_priority(self, model):
        critical = model.list_samples(priority="Critical")
        assert all(s["priority"] == "Critical" for s in critical)

    def test_filter_tests_by_status(self, model):
        requested = model.list_tests(status="Requested")
        assert all(t["status"] == "Requested" for t in requested)

    def test_filter_instruments_by_status(self, model):
        due = model.list_instruments(status="Due for Calibration")
        assert all(i["status"] == "Due for Calibration" for i in due)

    def test_filter_reagents_by_status(self, model):
        expired = model.list_reagents(status="Expired")
        assert all(r["status"] == "Expired" for r in expired)

    def test_get_sample_tests(self, model):
        tests = model.get_sample_tests("S-2024-0001")
        assert len(tests) > 0
        assert all(t["sample_id"] == "S-2024-0001" for t in tests)

    def test_update_sample_status(self, model):
        assert model.update_sample_status("S-2024-0005", "In Progress") is True
        s = model.get_sample("S-2024-0005")
        assert s["status"] == "In Progress"

    def test_update_sample_status_invalid(self, model):
        assert model.update_sample_status("S-2024-0005", "Bogus Status") is False

    def test_dashboard_stats_structure(self, model):
        stats = model.dashboard_stats()
        for key in (
            "total_samples", "open_samples", "critical_samples",
            "total_tests", "pending_tests", "passed_tests", "failed_tests",
            "total_instruments", "instruments_due_calibration", "instruments_out_of_service",
            "total_reagents", "reagents_expired", "reagents_low_stock",
            "by_sample_type", "by_sample_status",
        ):
            assert key in stats, f"Missing stats key: {key}"

    def test_dashboard_stats_totals(self, model):
        stats = model.dashboard_stats()
        assert stats["total_samples"] == len(MOCK_SAMPLES)
        assert stats["total_tests"] == len(MOCK_TESTS)
        assert stats["total_instruments"] == len(MOCK_INSTRUMENTS)
        assert stats["total_reagents"] == len(MOCK_REAGENTS)

    def test_instruments_ordered_by_next_calibration(self, model):
        instruments = model.list_instruments()
        dates = [i["next_calibration"] for i in instruments]
        assert dates == sorted(dates)

    def test_reagents_ordered_by_expiry(self, model):
        reagents = model.list_reagents()
        dates = [r["expiry_date"] for r in reagents]
        assert dates == sorted(dates)


# ── Flask routes ──────────────────────────────────────────────────────────────

class TestFlaskRoutes:
    def test_healthz(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_dashboard_loads(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"LIMS" in resp.data

    def test_samples_list_loads(self, client):
        client.get("/")
        resp = client.get("/samples")
        assert resp.status_code == 200

    def test_samples_filter_by_type(self, client):
        client.get("/")
        resp = client.get("/samples?sample_type=Environmental")
        assert resp.status_code == 200
        assert b"Environmental" in resp.data

    def test_samples_filter_by_status(self, client):
        client.get("/")
        resp = client.get("/samples?status=Released")
        assert resp.status_code == 200

    def test_sample_detail_loads(self, client):
        client.get("/")
        resp = client.get("/sample/S-2024-0001")
        assert resp.status_code == 200
        assert b"Drug Substance" in resp.data

    def test_sample_detail_404(self, client):
        client.get("/")
        resp = client.get("/sample/S-9999-9999")
        assert resp.status_code == 404

    def test_update_sample_status_redirects(self, client):
        client.get("/")
        resp = client.post("/sample/S-2024-0005/status", data={"status": "In Progress"})
        assert resp.status_code == 302

    def test_tests_list_loads(self, client):
        client.get("/")
        resp = client.get("/tests")
        assert resp.status_code == 200

    def test_tests_filter_by_status(self, client):
        client.get("/")
        resp = client.get("/tests?status=Approved")
        assert resp.status_code == 200

    def test_instruments_list_loads(self, client):
        client.get("/")
        resp = client.get("/instruments")
        assert resp.status_code == 200

    def test_instruments_filter_by_status(self, client):
        client.get("/")
        resp = client.get("/instruments?status=Active")
        assert resp.status_code == 200

    def test_reagents_list_loads(self, client):
        client.get("/")
        resp = client.get("/reagents")
        assert resp.status_code == 200

    def test_reagents_filter_by_status(self, client):
        client.get("/")
        resp = client.get("/reagents?status=Expired")
        assert resp.status_code == 200

    def test_reagents_filter_by_category(self, client):
        client.get("/")
        resp = client.get("/reagents?category=Solvent")
        assert resp.status_code == 200


# ── REST API ──────────────────────────────────────────────────────────────────

class TestRestAPI:
    def test_api_samples(self, client):
        client.get("/")
        resp = client.get("/api/v1/samples")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == len(MOCK_SAMPLES)

    def test_api_samples_filter_type(self, client):
        client.get("/")
        resp = client.get("/api/v1/samples?sample_type=Water")
        data = resp.get_json()
        assert all(s["sample_type"] == "Water" for s in data)

    def test_api_samples_filter_status(self, client):
        client.get("/")
        resp = client.get("/api/v1/samples?status=Released")
        data = resp.get_json()
        assert all(s["status"] == "Released" for s in data)

    def test_api_sample_detail(self, client):
        client.get("/")
        resp = client.get("/api/v1/sample/S-2024-0001")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sample" in data
        assert "tests" in data

    def test_api_sample_not_found(self, client):
        client.get("/")
        resp = client.get("/api/v1/sample/S-9999-9999")
        assert resp.status_code == 404

    def test_api_tests(self, client):
        client.get("/")
        resp = client.get("/api/v1/tests")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == len(MOCK_TESTS)

    def test_api_tests_filter_status(self, client):
        client.get("/")
        resp = client.get("/api/v1/tests?status=Approved")
        data = resp.get_json()
        assert all(t["status"] == "Approved" for t in data)

    def test_api_instruments(self, client):
        client.get("/")
        resp = client.get("/api/v1/instruments")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == len(MOCK_INSTRUMENTS)

    def test_api_instruments_filter_status(self, client):
        client.get("/")
        resp = client.get("/api/v1/instruments?status=Active")
        data = resp.get_json()
        assert all(i["status"] == "Active" for i in data)

    def test_api_reagents(self, client):
        client.get("/")
        resp = client.get("/api/v1/reagents")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == len(MOCK_REAGENTS)

    def test_api_reagents_filter_category(self, client):
        client.get("/")
        resp = client.get("/api/v1/reagents?category=Solvent")
        data = resp.get_json()
        assert all(r["category"] == "Solvent" for r in data)

    def test_api_stats(self, client):
        client.get("/")
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_samples" in data
        assert "total_instruments" in data
        assert "by_sample_type" in data
