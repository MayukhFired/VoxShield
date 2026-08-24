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
