import sqlite3
from pathlib import Path


DATABASE_FILE = Path(__file__).parent / "smartloan.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT UNIQUE NOT NULL,
            loan_id INTEGER,
            applicant_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            annual_income REAL,
            loan_amount REAL,
            status TEXT DEFAULT 'Document Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT UNIQUE NOT NULL,
            application_id TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            saved_filename TEXT NOT NULL,
            document_type TEXT DEFAULT 'Unknown',
            extracted_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id)
                REFERENCES applications(application_id)
        )
    """)

    connection.commit()
    connection.close()


def insert_application(application):
    connection = get_connection()

    connection.execute("""
        INSERT INTO applications (
            application_id,
            loan_id,
            applicant_name,
            email,
            phone,
            annual_income,
            loan_amount,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        application["application_id"],
        application.get("loan_id"),
        application["applicant_name"],
        application["email"],
        application["phone"],
        application["annual_income"],
        application["loan_amount"],
        application["status"]
    ))

    connection.commit()
    connection.close()


def get_all_applications():
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM applications
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def application_exists(application_id):
    connection = get_connection()

    row = connection.execute("""
        SELECT application_id
        FROM applications
        WHERE application_id = ?
    """, (application_id,)).fetchone()

    connection.close()

    return row is not None


def insert_document(document):
    connection = get_connection()

    connection.execute("""
        INSERT INTO documents (
            document_id,
            application_id,
            original_filename,
            saved_filename,
            document_type,
            extracted_text
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        document["document_id"],
        document["application_id"],
        document["original_filename"],
        document["saved_filename"],
        document["document_type"],
        document["extracted_text"]
    ))

    connection.commit()
    connection.close()


def get_documents_by_application(application_id):
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM documents
        WHERE application_id = ?
        ORDER BY id DESC
    """, (application_id,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def update_application_status(application_id, status):
    connection = get_connection()

    connection.execute("""
        UPDATE applications
        SET status = ?
        WHERE application_id = ?
    """, (status, application_id))

    connection.commit()
    connection.close()