import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voiceshield.db")


def get_connection():
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            reports_count INTEGER DEFAULT 1,
            first_reported TEXT NOT NULL,
            last_reported TEXT NOT NULL,
            avg_confidence REAL DEFAULT 0.0,
            status TEXT DEFAULT 'suspicious'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            confidence_score REAL DEFAULT 0.0,
            notes TEXT,
            reported_at TEXT NOT NULL
        )
    """)
    
    # Index for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_phone_number 
        ON blacklisted_numbers(phone_number)
    """)
    
    conn.commit()
    conn.close()


async def add_report(phone_number: str, confidence_score: float, notes: Optional[str] = None):
    """Add a scam report for a phone number."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    try:
        # Add to reports table
        cursor.execute(
            "INSERT INTO reports (phone_number, confidence_score, notes, reported_at) VALUES (?, ?, ?, ?)",
            (phone_number, confidence_score, notes, now)
        )
        
        # Check if number already exists in blacklist
        cursor.execute(
            "SELECT id, reports_count, avg_confidence FROM blacklisted_numbers WHERE phone_number = ?",
            (phone_number,)
        )
        existing = cursor.fetchone()
        
        if existing:
            new_count = existing["reports_count"] + 1
            new_avg = ((existing["avg_confidence"] * existing["reports_count"]) + confidence_score) / new_count
            status = "confirmed" if new_count >= 3 else "suspicious"
            
            cursor.execute(
                """UPDATE blacklisted_numbers 
                   SET reports_count = ?, last_reported = ?, avg_confidence = ?, status = ?
                   WHERE phone_number = ?""",
                (new_count, now, new_avg, status, phone_number)
            )
        else:
            cursor.execute(
                """INSERT INTO blacklisted_numbers 
                   (phone_number, reports_count, first_reported, last_reported, avg_confidence, status)
                   VALUES (?, 1, ?, ?, ?, 'suspicious')""",
                (phone_number, now, now, confidence_score)
            )
        
        conn.commit()
        
        # Return the current state
        cursor.execute(
            "SELECT * FROM blacklisted_numbers WHERE phone_number = ?",
            (phone_number,)
        )
        entry = cursor.fetchone()
        
        return {
            "success": True,
            "message": f"Number {phone_number} reported successfully",
            "entry": dict(entry)
        }
    
    finally:
        conn.close()


async def check_blacklist(phone_number: str):
    """Check if a number is blacklisted. Optimized for <50ms response."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM blacklisted_numbers WHERE phone_number = ?",
            (phone_number,)
        )
        entry = cursor.fetchone()
        
        if entry:
            return {
                "is_blacklisted": True,
                "phone_number": entry["phone_number"],
                "reports_count": entry["reports_count"],
                "status": entry["status"],
                "avg_confidence": entry["avg_confidence"],
                "first_reported": entry["first_reported"],
                "last_reported": entry["last_reported"],
                "risk_level": "high" if entry["status"] == "confirmed" else "medium"
            }
        else:
            return {
                "is_blacklisted": False,
                "phone_number": phone_number,
                "risk_level": "unknown"
            }
    
    finally:
        conn.close()


async def get_blacklist_page(page: int = 1, page_size: int = 20, sort_by: str = "reports_count"):
    """Get a paginated list of blacklisted numbers."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * page_size
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM blacklisted_numbers")
        total = cursor.fetchone()["total"]
        
        # Get page
        cursor.execute(
            f"SELECT * FROM blacklisted_numbers ORDER BY {sort_by} DESC LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        entries = [dict(row) for row in cursor.fetchall()]
        
        return {
            "entries": entries,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    finally:
        conn.close()


async def search_blacklist(query: str):
    """Search blacklisted numbers by prefix or partial match."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM blacklisted_numbers WHERE phone_number LIKE ? ORDER BY reports_count DESC LIMIT 20",
            (f"%{query}%",)
        )
        entries = [dict(row) for row in cursor.fetchall()]
        
        return {
            "results": entries,
            "count": len(entries),
            "query": query
        }
    
    finally:
        conn.close()


# Initialize database on module import
init_db()


# =========================================================
# SCAMMER VOICEPRINT DATABASE
# =========================================================

def init_voiceprint_db():
    """Initialize the voiceprint/de-cloaking tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scammer_voiceprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint_hash TEXT NOT NULL,
            fingerprint_vector TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            times_seen INTEGER DEFAULT 1,
            linked_numbers TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decloak_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voiceprint_id INTEGER,
            phone_number TEXT,
            detection_verdict TEXT,
            detection_confidence REAL,
            voiceprint_confidence REAL,
            matched_existing INTEGER DEFAULT 0,
            similarity_score REAL DEFAULT 0.0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (voiceprint_id) REFERENCES scammer_voiceprints(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fp_hash
        ON scammer_voiceprints(fingerprint_hash)
    """)

    conn.commit()
    conn.close()


async def store_voiceprint(fingerprint_hash: str, fingerprint_vector: list, confidence: float, phone_number: Optional[str] = None) -> dict:
    """Store a new scammer voiceprint or update if similar one exists."""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    try:
        # Check if this exact hash already exists
        cursor.execute(
            "SELECT * FROM scammer_voiceprints WHERE fingerprint_hash = ?",
            (fingerprint_hash,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing record
            times = existing["times_seen"] + 1
            linked = json.loads(existing["linked_numbers"])
            if phone_number and phone_number not in linked:
                linked.append(phone_number)

            cursor.execute("""
                UPDATE scammer_voiceprints
                SET last_seen = ?, times_seen = ?, linked_numbers = ?,
                    confidence = MAX(confidence, ?)
                WHERE id = ?
            """, (now, times, json.dumps(linked), confidence, existing["id"]))

            conn.commit()
            voiceprint_id = existing["id"]
            is_new = False
        else:
            # Insert new voiceprint
            linked = json.dumps([phone_number] if phone_number else [])
            cursor.execute("""
                INSERT INTO scammer_voiceprints
                (fingerprint_hash, fingerprint_vector, confidence, first_seen, last_seen, times_seen, linked_numbers, status)
                VALUES (?, ?, ?, ?, ?, 1, ?, 'active')
            """, (fingerprint_hash, json.dumps(fingerprint_vector), confidence, now, now, linked))

            conn.commit()
            voiceprint_id = cursor.lastrowid
            is_new = True

        return {
            "voiceprint_id": voiceprint_id,
            "is_new": is_new,
            "times_seen": 1 if is_new else existing["times_seen"] + 1,
        }

    finally:
        conn.close()


async def find_similar_voiceprints(fingerprint_vector: list, threshold: float = 0.65) -> list:
    """
    Find voiceprints in the database that are similar to the given vector.
    Uses cosine similarity comparison against all stored voiceprints.
    """
    import json
    import numpy as np

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM scammer_voiceprints")
        all_prints = cursor.fetchall()

        if not all_prints:
            return []

        query_vec = np.array(fingerprint_vector)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []
        query_vec = query_vec / query_norm

        matches = []
        for row in all_prints:
            stored_vec = np.array(json.loads(row["fingerprint_vector"]))
            stored_norm = np.linalg.norm(stored_vec)
            if stored_norm == 0:
                continue
            stored_vec = stored_vec / stored_norm

            # Cosine similarity
            min_len = min(len(query_vec), len(stored_vec))
            similarity = float(np.dot(query_vec[:min_len], stored_vec[:min_len]))
            # Scale to 0-1
            similarity = (similarity + 1) / 2

            if similarity >= threshold:
                matches.append({
                    "voiceprint_id": row["id"],
                    "similarity": round(similarity, 4),
                    "times_seen": row["times_seen"],
                    "first_seen": row["first_seen"],
                    "last_seen": row["last_seen"],
                    "linked_numbers": json.loads(row["linked_numbers"]),
                    "status": row["status"],
                    "fingerprint_hash": row["fingerprint_hash"],
                })

        # Sort by similarity descending
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:10]  # Top 10 matches

    finally:
        conn.close()


async def record_decloak_case(voiceprint_id: int, phone_number: Optional[str], detection_verdict: str,
                               detection_confidence: float, voiceprint_confidence: float,
                               matched_existing: bool, similarity_score: float) -> int:
    """Record a de-cloaking case for audit trail."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    try:
        cursor.execute("""
            INSERT INTO decloak_cases
            (voiceprint_id, phone_number, detection_verdict, detection_confidence,
             voiceprint_confidence, matched_existing, similarity_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (voiceprint_id, phone_number, detection_verdict, detection_confidence,
              voiceprint_confidence, 1 if matched_existing else 0, similarity_score, now))

        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


async def get_scammer_profile(voiceprint_id: int) -> Optional[dict]:
    """Get full scammer profile by voiceprint ID."""
    import json
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM scammer_voiceprints WHERE id = ?", (voiceprint_id,))
        row = cursor.fetchone()
        if not row:
            return None

        # Get all cases for this voiceprint
        cursor.execute(
            "SELECT * FROM decloak_cases WHERE voiceprint_id = ? ORDER BY timestamp DESC",
            (voiceprint_id,)
        )
        cases = [dict(c) for c in cursor.fetchall()]

        return {
            "voiceprint_id": row["id"],
            "fingerprint_hash": row["fingerprint_hash"],
            "confidence": row["confidence"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "times_seen": row["times_seen"],
            "linked_numbers": json.loads(row["linked_numbers"]),
            "status": row["status"],
            "cases": cases,
            "total_victims_targeted": len(cases),
        }
    finally:
        conn.close()


async def get_decloak_stats() -> dict:
    """Get overall de-cloaking statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) as total FROM scammer_voiceprints")
        total_prints = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM decloak_cases")
        total_cases = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM decloak_cases WHERE matched_existing = 1")
        total_matches = cursor.fetchone()["total"]

        cursor.execute("SELECT MAX(times_seen) as max_seen FROM scammer_voiceprints")
        row = cursor.fetchone()
        most_seen = row["max_seen"] if row["max_seen"] else 0

        return {
            "total_scammer_voiceprints": total_prints,
            "total_decloak_cases": total_cases,
            "cross_case_matches": total_matches,
            "most_prolific_scammer_cases": most_seen,
        }
    finally:
        conn.close()


# Initialize voiceprint tables
init_voiceprint_db()
