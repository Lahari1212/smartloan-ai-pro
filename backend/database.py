import json
import sqlite3
from pathlib import Path


DATABASE_FILE = Path(__file__).parent / "smartloan.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def _add_column_if_not_exists(cursor, table: str, column_def: str):
    col_name = column_def.split()[0]
    cursor.execute(f"PRAGMA table_info({table})")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if col_name not in existing_cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------
    # Users table (authentication)
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'applicant',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------
    # Audit logs table
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            user_id TEXT,
            user_email TEXT,
            event TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------
    # Notifications table
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            application_id TEXT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------
    # Applications table
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT UNIQUE NOT NULL,
            user_id TEXT,
            loan_id INTEGER,
            applicant_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            annual_income REAL,
            loan_amount REAL,
            loan_term INTEGER DEFAULT 10,
            cibil_score INTEGER DEFAULT 750,
            education TEXT DEFAULT 'Graduate',
            self_employed TEXT DEFAULT 'No',
            residential_assets_value REAL DEFAULT 0,
            commercial_assets_value REAL DEFAULT 0,
            luxury_assets_value REAL DEFAULT 0,
            bank_asset_value REAL DEFAULT 0,
            status TEXT DEFAULT 'Document Pending',
            review_notes TEXT,
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            ai_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------
    # Documents table
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT UNIQUE NOT NULL,
            application_id TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            saved_filename TEXT NOT NULL,
            document_type TEXT DEFAULT 'Unknown',
            extracted_text TEXT,
            extracted_json TEXT,
            confidence_score REAL DEFAULT 0.0,
            classification_confidence REAL DEFAULT 0.0,
            file_size INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        )
    """)

    # --------------------------------------------------
    # Schema migrations for existing DBs (safe ALTER TABLE)
    # --------------------------------------------------
    cols_to_add_app = [
        "user_id TEXT",
        "loan_term INTEGER DEFAULT 10",
        "cibil_score INTEGER DEFAULT 750",
        "education TEXT DEFAULT 'Graduate'",
        "self_employed TEXT DEFAULT 'No'",
        "residential_assets_value REAL DEFAULT 0",
        "commercial_assets_value REAL DEFAULT 0",
        "luxury_assets_value REAL DEFAULT 0",
        "bank_asset_value REAL DEFAULT 0",
        "review_notes TEXT",
        "reviewed_by TEXT",
        "reviewed_at TIMESTAMP",
        "ai_summary TEXT",
    ]
    for col in cols_to_add_app:
        _add_column_if_not_exists(cursor, "applications", col)

    cols_to_add_docs = [
        "extracted_json TEXT",
        "confidence_score REAL DEFAULT 0.0",
        "classification_confidence REAL DEFAULT 0.0",
        "file_size INTEGER DEFAULT 0",
    ]
    for col in cols_to_add_docs:
        _add_column_if_not_exists(cursor, "documents", col)

    connection.commit()
    connection.close()


# ==============================================================
# User (Auth) Functions
# ==============================================================

def insert_user(user: dict):
    """Insert a new user into the users table."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, full_name, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user["user_id"],
        user["full_name"],
        user["email"],
        user["password_hash"],
        user.get("role", "applicant"),
    ))
    connection.commit()
    connection.close()


def get_user_by_email(email: str):
    """Fetch a user record by email address."""
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    connection.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str):
    """Fetch a user record by user_id."""
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    connection.close()
    return dict(row) if row else None


def email_exists(email: str) -> bool:
    """Return True if the email is already registered."""
    return get_user_by_email(email) is not None


def upsert_officer(user_id: str, full_name: str, email: str, password_hash: str):
    """
    Create the officer account if it doesn't exist,
    or update the password hash if it does (so env-var changes take effect).
    """
    connection = get_connection()
    cursor = connection.cursor()
    existing = connection.execute(
        "SELECT id FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()

    if existing:
        cursor.execute("""
            UPDATE users SET password_hash = ?, full_name = ?, role = 'officer'
            WHERE email = ?
        """, (password_hash, full_name, email.lower().strip()))
    else:
        cursor.execute("""
            INSERT INTO users (user_id, full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?, 'officer')
        """, (user_id, full_name, email.lower().strip(), password_hash))

    connection.commit()
    connection.close()


# ==============================================================
# Application Functions (all existing preserved + user_id added)
# ==============================================================

def insert_application(application):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO applications (
            application_id,
            user_id,
            loan_id,
            applicant_name,
            email,
            phone,
            annual_income,
            loan_amount,
            loan_term,
            cibil_score,
            education,
            self_employed,
            residential_assets_value,
            commercial_assets_value,
            luxury_assets_value,
            bank_asset_value,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        application["application_id"],
        application.get("user_id"),
        application.get("loan_id"),
        application["applicant_name"],
        application.get("email"),
        application.get("phone"),
        application.get("annual_income"),
        application.get("loan_amount"),
        application.get("loan_term", 10),
        application.get("cibil_score", 750),
        application.get("education", "Graduate"),
        application.get("self_employed", "No"),
        application.get("residential_assets_value", 0),
        application.get("commercial_assets_value", 0),
        application.get("luxury_assets_value", 0),
        application.get("bank_asset_value", 0),
        application.get("status", "Document Pending"),
    ))

    connection.commit()
    connection.close()


def get_all_applications():
    """Return all applications (officer view)."""
    connection = get_connection()
    rows = connection.execute("""
        SELECT *
        FROM applications
        ORDER BY id DESC
    """).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_applications_by_user(user_id: str):
    """Return applications belonging to a specific applicant."""
    connection = get_connection()
    rows = connection.execute("""
        SELECT *
        FROM applications
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_application_by_id(application_id: str):
    connection = get_connection()
    row = connection.execute("""
        SELECT *
        FROM applications
        WHERE application_id = ?
    """, (application_id,)).fetchone()
    connection.close()
    if row:
        return dict(row)
    return None


def application_exists(application_id):
    return get_application_by_id(application_id) is not None


# ==============================================================
# Document Functions (all existing preserved)
# ==============================================================

def insert_document(document):
    connection = get_connection()
    cursor = connection.cursor()

    extracted_json_str = document.get("extracted_json")
    if isinstance(extracted_json_str, (dict, list)):
        extracted_json_str = json.dumps(extracted_json_str)

    cursor.execute("""
        INSERT INTO documents (
            document_id,
            application_id,
            original_filename,
            saved_filename,
            document_type,
            extracted_text,
            extracted_json,
            confidence_score,
            classification_confidence,
            file_size
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        document["document_id"],
        document["application_id"],
        document["original_filename"],
        document["saved_filename"],
        document.get("document_type", "Unknown"),
        document.get("extracted_text", ""),
        extracted_json_str,
        document.get("confidence_score", 0.0),
        document.get("classification_confidence", 0.0),
        document.get("file_size", 0),
    ))

    connection.commit()
    connection.close()


def get_documents_by_application(application_id):
    connection = get_connection()
    rows = connection.execute("""
        SELECT *
        FROM documents
        WHERE application_id = ?
        ORDER BY id ASC
    """, (application_id,)).fetchall()
    connection.close()

    results = []
    for row in rows:
        d = dict(row)
        if d.get("extracted_json"):
            try:
                d["extracted_json"] = json.loads(d["extracted_json"])
            except Exception:
                pass
        results.append(d)
    return results


def get_document_by_id(document_id: str):
    connection = get_connection()
    row = connection.execute("""
        SELECT *
        FROM documents
        WHERE document_id = ?
    """, (document_id,)).fetchone()
    connection.close()
    if not row:
        return None
    d = dict(row)
    if d.get("extracted_json"):
        try:
            d["extracted_json"] = json.loads(d["extracted_json"])
        except Exception:
            pass
    return d


def update_document_extraction(document_id, document_type, extracted_text, extracted_json, confidence_score, classification_confidence):
    connection = get_connection()
    if isinstance(extracted_json, (dict, list)):
        extracted_json = json.dumps(extracted_json)

    connection.execute("""
        UPDATE documents
        SET document_type = ?,
            extracted_text = ?,
            extracted_json = ?,
            confidence_score = ?,
            classification_confidence = ?
        WHERE document_id = ?
    """, (
        document_type,
        extracted_text,
        extracted_json,
        confidence_score,
        classification_confidence,
        document_id
    ))
    connection.commit()
    connection.close()


def update_application_status(application_id, status):
    connection = get_connection()
    connection.execute("""
        UPDATE applications
        SET status = ?
        WHERE application_id = ?
    """, (status, application_id))
    connection.commit()
    connection.close()


def update_application_summary(application_id, ai_summary: str, status: str = None):
    connection = get_connection()
    if status:
        connection.execute("""
            UPDATE applications
            SET ai_summary = ?, status = ?
            WHERE application_id = ?
        """, (ai_summary, status, application_id))
    else:
        connection.execute("""
            UPDATE applications
            SET ai_summary = ?
            WHERE application_id = ?
        """, (ai_summary, application_id))
    connection.commit()
    connection.close()


def record_officer_review(application_id, decision: str, notes: str, officer_id: str = "Loan Officer"):
    connection = get_connection()
    connection.execute("""
        UPDATE applications
        SET status = ?,
            review_notes = ?,
            reviewed_by = ?,
            reviewed_at = CURRENT_TIMESTAMP
        WHERE application_id = ?
    """, (decision, notes, officer_id, application_id))
    connection.commit()
    connection.close()


# ==============================================================
# Audit Log Functions
# ==============================================================

def log_audit_event(application_id: str, event: str, details: str = None,
                    user_id: str = None, user_email: str = None):
    """Record an audit event for an application."""
    connection = get_connection()
    connection.execute("""
        INSERT INTO audit_logs (application_id, user_id, user_email, event, details)
        VALUES (?, ?, ?, ?, ?)
    """, (application_id, user_id, user_email, event, details))
    connection.commit()
    connection.close()


def get_audit_log(application_id: str):
    """Return all audit events for an application, newest first."""
    connection = get_connection()
    rows = connection.execute("""
        SELECT * FROM audit_logs
        WHERE application_id = ?
        ORDER BY id ASC
    """, (application_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


# ==============================================================
# Notification Functions
# ==============================================================

def create_notification(user_id: str, title: str, message: str, application_id: str = None):
    """Create an in-app notification for a user."""
    connection = get_connection()
    connection.execute("""
        INSERT INTO notifications (user_id, application_id, title, message)
        VALUES (?, ?, ?, ?)
    """, (user_id, application_id, title, message))
    connection.commit()
    connection.close()


def get_notifications_by_user(user_id: str, limit: int = 20):
    """Fetch notifications for a specific user, newest first."""
    connection = get_connection()
    rows = connection.execute("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def mark_notification_as_read(notification_id: int, user_id: str):
    """Mark a notification as read."""
    connection = get_connection()
    connection.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE id = ? AND user_id = ?
    """, (notification_id, user_id))
    connection.commit()
    connection.close()