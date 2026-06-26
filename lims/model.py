"""
SQLite persistence layer for Laboratory LIMS.
Manages samples, tests, instruments, and reagents.
"""
import json
import sqlite3
from datetime import date
from typing import Optional

from data.mock_data import MOCK_SAMPLES, MOCK_TESTS, MOCK_INSTRUMENTS, MOCK_REAGENTS

_DDL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS samples (
    sample_id       TEXT PRIMARY KEY,
    barcode         TEXT,
    sample_type     TEXT,
    description     TEXT,
    client          TEXT,
    project         TEXT,
    received_date   TEXT,
    received_by     TEXT,
    storage_location TEXT,
    status          TEXT,
    priority        TEXT,
    volume          TEXT,
    matrix          TEXT,
    added_at        TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS tests (
    test_id         TEXT PRIMARY KEY,
    sample_id       TEXT NOT NULL,
    test_name       TEXT NOT NULL,
    method          TEXT,
    requested_by    TEXT,
    requested_date  TEXT,
    assigned_to     TEXT,
    status          TEXT,
    result          TEXT,
    result_units    TEXT,
    result_date     TEXT,
    pass_fail       TEXT,
    specification   TEXT,
    notes           TEXT,
    added_at        TEXT DEFAULT (date('now')),
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
);

CREATE TABLE IF NOT EXISTS instruments (
    instrument_id       TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    model               TEXT,
    serial_number       TEXT,
    location            TEXT,
    department          TEXT,
    status              TEXT,
    last_calibration    TEXT,
    next_calibration    TEXT,
    calibrated_by       TEXT,
    calibration_method  TEXT,
    added_at            TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS reagents (
    reagent_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    catalog_number  TEXT,
    lot_number      TEXT,
    manufacturer    TEXT,
    received_date   TEXT,
    expiry_date     TEXT,
    quantity        REAL,
    unit            TEXT,
    storage_location TEXT,
    status          TEXT,
    category        TEXT,
    added_at        TEXT DEFAULT (date('now'))
);
"""

_SAMPLE_STATUSES = {"Received", "In Progress", "Pending Review", "Approved", "Released", "Rejected"}
_TEST_STATUSES = {"Requested", "In Progress", "Completed", "Reviewed", "Approved", "Failed"}
_INSTRUMENT_STATUSES = {"Active", "Due for Calibration", "Out of Service", "Retired"}
_REAGENT_STATUSES = {"In Stock", "Low Stock", "Expired", "Quarantined", "Depleted"}


class Model:
    def __init__(self, db_path: str = ":memory:"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def is_seeded(self) -> bool:
        row = self._conn.execute("SELECT COUNT(*) FROM samples").fetchone()
        return row[0] > 0

    def seed(self) -> None:
        for s in MOCK_SAMPLES:
            self.upsert_sample(s)
        for t in MOCK_TESTS:
            self.upsert_test(t)
        for i in MOCK_INSTRUMENTS:
            self.upsert_instrument(i)
        for r in MOCK_REAGENTS:
            self.upsert_reagent(r)
        self._conn.commit()

    # ── Samples ───────────────────────────────────────────────────────────────

    def upsert_sample(self, s: dict) -> None:
        self._conn.execute(
            """INSERT INTO samples
               (sample_id, barcode, sample_type, description, client, project,
                received_date, received_by, storage_location, status, priority, volume, matrix)
               VALUES (:sample_id, :barcode, :sample_type, :description, :client, :project,
                       :received_date, :received_by, :storage_location, :status, :priority,
                       :volume, :matrix)
               ON CONFLICT(sample_id) DO UPDATE SET
                 status=excluded.status, storage_location=excluded.storage_location""",
            s,
        )

    def list_samples(
        self,
        sample_type: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        client: Optional[str] = None,
    ) -> list[dict]:
        sql = "SELECT * FROM samples WHERE 1=1"
        params: list = []
        if sample_type:
            sql += " AND sample_type=?"; params.append(sample_type)
        if status:
            sql += " AND status=?"; params.append(status)
        if priority:
            sql += " AND priority=?"; params.append(priority)
        if client:
            sql += " AND client=?"; params.append(client)
        sql += " ORDER BY received_date DESC"
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def get_sample(self, sample_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM samples WHERE sample_id=?", (sample_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_sample_tests(self, sample_id: str) -> list[dict]:
        return [
            dict(r)
            for r in self._conn.execute(
                "SELECT * FROM tests WHERE sample_id=? ORDER BY requested_date DESC",
                (sample_id,),
            ).fetchall()
        ]

    def update_sample_status(self, sample_id: str, status: str) -> bool:
        if status not in _SAMPLE_STATUSES:
            return False
        self._conn.execute(
            "UPDATE samples SET status=? WHERE sample_id=?", (status, sample_id)
        )
        self._conn.commit()
        return True

    # ── Tests ─────────────────────────────────────────────────────────────────

    def upsert_test(self, t: dict) -> None:
        self._conn.execute(
            """INSERT INTO tests
               (test_id, sample_id, test_name, method, requested_by, requested_date,
                assigned_to, status, result, result_units, result_date, pass_fail,
                specification, notes)
               VALUES (:test_id, :sample_id, :test_name, :method, :requested_by,
                       :requested_date, :assigned_to, :status, :result, :result_units,
                       :result_date, :pass_fail, :specification, :notes)
               ON CONFLICT(test_id) DO UPDATE SET
                 status=excluded.status, result=excluded.result,
                 result_date=excluded.result_date, pass_fail=excluded.pass_fail,
                 notes=excluded.notes""",
            t,
        )

    def list_tests(
        self,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        pass_fail: Optional[str] = None,
    ) -> list[dict]:
        sql = "SELECT t.*, s.sample_type, s.barcode FROM tests t LEFT JOIN samples s ON t.sample_id=s.sample_id WHERE 1=1"
        params: list = []
        if status:
            sql += " AND t.status=?"; params.append(status)
        if assigned_to:
            sql += " AND t.assigned_to=?"; params.append(assigned_to)
        if pass_fail:
            sql += " AND t.pass_fail=?"; params.append(pass_fail)
        sql += " ORDER BY t.requested_date DESC"
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def get_test(self, test_id: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM tests WHERE test_id=?", (test_id,)).fetchone()
        return dict(row) if row else None

    # ── Instruments ───────────────────────────────────────────────────────────

    def upsert_instrument(self, i: dict) -> None:
        self._conn.execute(
            """INSERT INTO instruments
               (instrument_id, name, model, serial_number, location, department,
                status, last_calibration, next_calibration, calibrated_by, calibration_method)
               VALUES (:instrument_id, :name, :model, :serial_number, :location, :department,
                       :status, :last_calibration, :next_calibration, :calibrated_by,
                       :calibration_method)
               ON CONFLICT(instrument_id) DO UPDATE SET
                 status=excluded.status, last_calibration=excluded.last_calibration,
                 next_calibration=excluded.next_calibration""",
            i,
        )

    def list_instruments(
        self,
        status: Optional[str] = None,
        department: Optional[str] = None,
    ) -> list[dict]:
        sql = "SELECT * FROM instruments WHERE 1=1"
        params: list = []
        if status:
            sql += " AND status=?"; params.append(status)
        if department:
            sql += " AND department=?"; params.append(department)
        sql += " ORDER BY next_calibration ASC"
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def get_instrument(self, instrument_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM instruments WHERE instrument_id=?", (instrument_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Reagents ──────────────────────────────────────────────────────────────

    def upsert_reagent(self, r: dict) -> None:
        self._conn.execute(
            """INSERT INTO reagents
               (reagent_id, name, catalog_number, lot_number, manufacturer, received_date,
                expiry_date, quantity, unit, storage_location, status, category)
               VALUES (:reagent_id, :name, :catalog_number, :lot_number, :manufacturer,
                       :received_date, :expiry_date, :quantity, :unit, :storage_location,
                       :status, :category)
               ON CONFLICT(reagent_id) DO UPDATE SET
                 status=excluded.status, quantity=excluded.quantity""",
            r,
        )

    def list_reagents(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        sql = "SELECT * FROM reagents WHERE 1=1"
        params: list = []
        if status:
            sql += " AND status=?"; params.append(status)
        if category:
            sql += " AND category=?"; params.append(category)
        sql += " ORDER BY expiry_date ASC"
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def get_reagent(self, reagent_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM reagents WHERE reagent_id=?", (reagent_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Dashboard stats ───────────────────────────────────────────────────────

    def dashboard_stats(self) -> dict:
        today = date.today().isoformat()

        s = self._conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
        s_open = self._conn.execute(
            "SELECT COUNT(*) FROM samples WHERE status NOT IN ('Released','Rejected')"
        ).fetchone()[0]
        s_critical = self._conn.execute(
            "SELECT COUNT(*) FROM samples WHERE priority='Critical'"
        ).fetchone()[0]

        t_total = self._conn.execute("SELECT COUNT(*) FROM tests").fetchone()[0]
        t_pending = self._conn.execute(
            "SELECT COUNT(*) FROM tests WHERE status IN ('Requested','In Progress')"
        ).fetchone()[0]
        t_pass = self._conn.execute(
            "SELECT COUNT(*) FROM tests WHERE pass_fail='Pass'"
        ).fetchone()[0]
        t_fail = self._conn.execute(
            "SELECT COUNT(*) FROM tests WHERE pass_fail='Fail'"
        ).fetchone()[0]

        i_total = self._conn.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
        i_due = self._conn.execute(
            "SELECT COUNT(*) FROM instruments WHERE status='Due for Calibration'"
        ).fetchone()[0]
        i_oos = self._conn.execute(
            "SELECT COUNT(*) FROM instruments WHERE status='Out of Service'"
        ).fetchone()[0]

        r_total = self._conn.execute("SELECT COUNT(*) FROM reagents").fetchone()[0]
        r_expiring = self._conn.execute(
            "SELECT COUNT(*) FROM reagents WHERE expiry_date<=? AND status NOT IN ('Expired','Depleted')",
            (today,),
        ).fetchone()[0]
        r_low = self._conn.execute(
            "SELECT COUNT(*) FROM reagents WHERE status='Low Stock'"
        ).fetchone()[0]
        r_expired = self._conn.execute(
            "SELECT COUNT(*) FROM reagents WHERE status='Expired'"
        ).fetchone()[0]

        by_sample_type = {
            r["sample_type"]: r["cnt"]
            for r in self._conn.execute(
                "SELECT sample_type, COUNT(*) as cnt FROM samples GROUP BY sample_type"
            ).fetchall()
        }
        by_sample_status = {
            r["status"]: r["cnt"]
            for r in self._conn.execute(
                "SELECT status, COUNT(*) as cnt FROM samples GROUP BY status"
            ).fetchall()
        }

        return {
            "total_samples": s,
            "open_samples": s_open,
            "critical_samples": s_critical,
            "total_tests": t_total,
            "pending_tests": t_pending,
            "passed_tests": t_pass,
            "failed_tests": t_fail,
            "total_instruments": i_total,
            "instruments_due_calibration": i_due,
            "instruments_out_of_service": i_oos,
            "total_reagents": r_total,
            "reagents_expiring_soon": r_expiring,
            "reagents_low_stock": r_low,
            "reagents_expired": r_expired,
            "by_sample_type": by_sample_type,
            "by_sample_status": by_sample_status,
        }
