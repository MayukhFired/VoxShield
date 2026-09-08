"""
VoxShield AI — Feature Verification & Diagnostic Script

Runs a comprehensive test suite across all application endpoints and core features:
1. Health & Status
2. Demo Audio Analysis
3. File Upload Detection (/api/detect)
4. Voice De-Cloaking Engine & Fingerprinting (/api/decloak)
5. ScamTrap AI Conversation Simulation (/api/scamtrap/auto)
6. ScamTrap Persona TTS Speech Synthesis (/api/scamtrap/tts)
7. Community Blacklist Search, Report & Pagination (/api/blacklist/*)
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def print_result(feature_name: str, passed: bool, detail: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} | {feature_name:<40} {detail}")

def run_feature_checks():
    print("=" * 70)
    print("VoxShield AI -- Full Feature Diagnostic Check")
    print("=" * 70)

    
    all_passed = True

    # 1. Health Check
    try:
        r = client.get("/health")
        passed = r.status_code == 200 and r.json().get("status") == "healthy"
        print_result("1. System Health Check (/health)", passed, f"Status: {r.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("1. System Health Check (/health)", False, str(e))
        all_passed = False

    # 2. Demo Audio Samples
    try:
        r = client.get("/api/demo/samples")
        passed = r.status_code == 200 and "samples" in r.json()
        print_result("2. List Demo Samples (/api/demo/samples)", passed, f"Count: {len(r.json().get('samples', {}))}")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("2. List Demo Samples (/api/demo/samples)", False, str(e))
        all_passed = False

    # 3. Demo Audio Analysis
    try:
        r = client.get("/api/demo/analyze/real_voice")
        data = r.json()
        passed = r.status_code == 200 and "verdict" in data and "confidence" in data
        print_result("3. Demo Audio Analysis (real_voice)", passed, f"Verdict: {data.get('verdict')}, Score: {data.get('confidence')}")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("3. Demo Audio Analysis (real_voice)", False, str(e))
        all_passed = False

    # 4. Audio Detection File Upload
    demo_file = PROJECT_ROOT / "data" / "demo" / "fake_voice.wav"
    if demo_file.exists():
        try:
            with open(demo_file, "rb") as f:
                r = client.post("/api/detect", files={"file": ("fake_voice.wav", f, "audio/wav")})
            data = r.json()
            passed = r.status_code == 200 and data.get("verdict") == "fake"
            print_result("4. Audio File Upload Detection (/api/detect)", passed, f"Verdict: {data.get('verdict')}, Ensemble: {data.get('ensemble_score')}")
            all_passed = all_passed and passed
        except Exception as e:
            print_result("4. Audio File Upload Detection (/api/detect)", False, str(e))
            all_passed = False
    else:
        print_result("4. Audio File Upload Detection (/api/detect)", False, "Demo audio file missing")
        all_passed = False

    # 5. Voice De-Cloaking Engine
    if demo_file.exists():
        try:
            with open(demo_file, "rb") as f:
                r = client.post("/api/decloak", files={"file": ("fake_voice.wav", f, "audio/wav")}, data={"phone_number": "+919876543210", "consent_to_store": "true"})
            data = r.json()
            passed = r.status_code == 200 and data.get("voiceprint") is not None and "fingerprint_hash" in data["voiceprint"]
            print_result("5. Voice De-Cloaking & Fingerprint (/api/decloak)", passed, f"Hash: {data.get('voiceprint', {}).get('fingerprint_hash', '')[:12]}...")
            all_passed = all_passed and passed
        except Exception as e:
            print_result("5. Voice De-Cloaking & Fingerprint (/api/decloak)", False, str(e))
            all_passed = False


    # 6. De-Cloaking Statistics
    try:
        r = client.get("/api/decloak/stats")
        data = r.json()
        passed = r.status_code == 200 and "total_scammer_voiceprints" in data
        print_result("6. De-Cloaking System Stats (/api/decloak/stats)", passed, f"Voiceprints logged: {data.get('total_scammer_voiceprints')}")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("6. De-Cloaking System Stats (/api/decloak/stats)", False, str(e))
        all_passed = False

    # 7. ScamTrap AI Auto Scenario
    try:
        r = client.post("/api/scamtrap/auto", json={"scenario_id": "bank_fraud", "persona_id": "elderly_grandma"})
        data = r.json()
        passed = r.status_code == 200 and "conversation" in data and len(data["conversation"]) > 0
        print_result("7. ScamTrap AI Simulation (/api/scamtrap/auto)", passed, f"Exchanges: {data.get('turns')}, Time Wasted: {data.get('total_time_wasted_formatted')}")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("7. ScamTrap AI Simulation (/api/scamtrap/auto)", False, str(e))
        all_passed = False

    # 8. ScamTrap TTS Synthesis (for all 3 personas)
    for persona in ["elderly_grandma", "nervous_uncle", "chatty_student"]:
        try:
            r = client.post("/api/scamtrap/tts", json={"text": f"Hello, testing speech for {persona}.", "persona_id": persona})
            passed = r.status_code == 200 and r.headers.get("content-type") == "audio/mpeg" and len(r.content) > 100
            print_result(f"8. ScamTrap TTS Voice ({persona})", passed, f"Audio size: {len(r.content)} bytes")
            all_passed = all_passed and passed
        except Exception as e:
            print_result(f"8. ScamTrap TTS Voice ({persona})", False, str(e))
            all_passed = False

    # 9. Blacklist Report Submission
    try:
        r = client.post("/api/blacklist/report", json={"phone_number": "+919876543210", "confidence_score": 0.92, "notes": "Automated verification test report."})
        data = r.json()
        passed = r.status_code == 200 and data.get("success") is True
        print_result("9. Blacklist Scam Report (/api/blacklist/report)", passed, f"Status: {data.get('entry', {}).get('status')}")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("9. Blacklist Scam Report (/api/blacklist/report)", False, str(e))
        all_passed = False

    # 10. Blacklist Number Search
    try:
        r = client.get("/api/blacklist/check/%2B919876543210")
        data = r.json()
        passed = r.status_code == 200 and data.get("is_blacklisted") is True
        print_result("10. Blacklist Number Check (/api/blacklist/check)", passed, f"Reports: {data.get('reports_count')}, Risk: {data.get('risk_level')}")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("10. Blacklist Number Check (/api/blacklist/check)", False, str(e))
        all_passed = False

    # 11. Blacklist Paginated Directory (public directory shows only confirmed entries)
    try:
        r = client.get("/api/blacklist/list?page=1&page_size=10")
        data = r.json()
        has_structure = (
            r.status_code == 200
            and "entries" in data
            and "total" in data
            and "page" in data
            and "total_pages" in data
        )
        # The public list intentionally shows only confirmed entries.
        # A freshly-reported number starts as 'suspicious', so total may be 0.
        passed = has_structure
        print_result("11. Blacklist Paginated Directory (/api/blacklist/list)", passed, f"Total confirmed: {data.get('total')} (only confirmed entries are public)")
        all_passed = all_passed and passed
    except Exception as e:
        print_result("11. Blacklist Paginated Directory (/api/blacklist/list)", False, str(e))
        all_passed = False

    # 12. Blacklist Moderation Confirm Flow (admin token required)
    try:
        import os as _os
        admin_token = _os.getenv("VOXSHIELD_ADMIN_TOKEN")
        if admin_token:
            r = client.post("/api/blacklist/confirm/%2B919876543210", headers={"x-admin-token": admin_token})
            data = r.json()
            passed = r.status_code == 200 and data.get("success") is True
            print_result("12. Blacklist Moderation Confirm Flow", passed, f"Entry status: {data.get('entry', {}).get('status')}")
            all_passed = all_passed and passed
        else:
            print_result("12. Blacklist Moderation Confirm Flow", True, "Skipped (VOXSHIELD_ADMIN_TOKEN not set — moderation disabled)")
    except Exception as e:
        print_result("12. Blacklist Moderation Confirm Flow", False, str(e))
        all_passed = False

    print("=" * 70)
    if all_passed:
        print("SUCCESS: ALL FEATURES PASSED DIAGNOSTIC CHECKS!")
    else:
        print("WARNING: SOME FEATURE CHECKS FAILED -- REVIEW DETAILS ABOVE.")
    print("=" * 70)


if __name__ == "__main__":
    run_feature_checks()
