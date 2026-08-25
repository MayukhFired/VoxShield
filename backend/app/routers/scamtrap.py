"""
VoxShield AI — ScamTrap AI Engine

When a fake voice is detected, the user can deploy an AI decoy persona
that takes over the conversation with the scammer — wasting their time,
collecting intelligence, and protecting real victims.

Inspired by:
- Virgin Media O2's "Daisy" (kept scammers on phone 40+ minutes)
- Apate (Australia) — 200,000 AI bots wasting millions of scammer hours

For the demo: We simulate a conversation between our AI persona and a
scammer using pre-scripted exchanges that showcase the concept.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time
import random

router = APIRouter()


# =========================================================
# AI PERSONA DEFINITIONS
# =========================================================

PERSONAS = {
    "elderly_grandma": {
        "name": "Kamla Devi",
        "age": 72,
        "description": "Confused elderly grandmother, hard of hearing, asks lots of questions, very trusting but slow",
        "avatar": "👵",
        "traits": ["slow speaker", "hard of hearing", "asks to repeat", "tells stories", "confused by technology"],
    },
    "nervous_uncle": {
        "name": "Rajesh Kumar",
        "age": 58,
        "description": "Nervous middle-aged man who almost falls for it but keeps asking clarifying questions",
        "avatar": "👨",
        "traits": ["nervous", "asks for credentials", "wants written proof", "keeps saying 'one minute'"],
    },
    "chatty_student": {
        "name": "Priya Sharma",
        "age": 21,
        "description": "Overly chatty college student who goes off-topic constantly",
        "avatar": "👩",
        "traits": ["talkative", "goes off-topic", "asks personal questions", "easily distracted"],
    },
}


# =========================================================
# SCAM SCENARIOS WITH SCRIPTED EXCHANGES
# =========================================================

SCENARIOS = {
    "bank_fraud": {
        "title": "Bank Account Fraud",
        "scammer_opening": "Hello sir/madam, I am calling from your bank's security department. We have detected suspicious activity on your account. I need to verify your details immediately.",
        "scammer_script": [
            "Your account has been compromised. I need your account number to verify.",
            "Sir/madam, this is very urgent. If you don't verify now, your account will be frozen.",
            "I need you to share the OTP that was sent to your phone.",
            "Please tell me your date of birth and mother's maiden name for verification.",
            "I'm going to transfer you to our senior officer. Please hold.",
            "Sir/madam, we need you to install a remote access application for security purposes.",
            "Your account will be blocked if you don't cooperate immediately.",
            "I am sending you a link. Please click on it to verify your identity.",
        ],
        "intelligence_targets": ["bank_name", "account_details", "personal_info", "otp_request", "remote_access", "urgency_tactics"],
    },
    "kidnapping_ransom": {
        "title": "Fake Kidnapping / Emergency",
        "scammer_opening": "Hello! Your son has been in a serious accident. He is with us. You need to send money immediately or something bad will happen to him.",
        "scammer_script": [
            "Your son is hurt badly. Don't call the police or he will be harmed.",
            "We need 2 lakhs immediately. Send via UPI to this number.",
            "He is crying here. Do you want to hear him? Send the money NOW.",
            "If you don't send in 10 minutes, we cannot guarantee his safety.",
            "Don't try to call your son's phone. We have it.",
            "Send the money to this account: XXXX. Do it now.",
            "We are watching your house. Don't do anything stupid.",
            "Time is running out. Transfer the money immediately.",
        ],
        "intelligence_targets": ["upi_id", "account_number", "phone_number", "location_claims", "threat_type", "time_pressure"],
    },
    "tech_support": {
        "title": "Fake Tech Support",
        "scammer_opening": "Hello, this is Microsoft Technical Support. Your computer has been sending us error reports and it is infected with a dangerous virus. We need to fix it immediately.",
        "scammer_script": [
            "Your Windows license is expired and hackers are accessing your computer right now.",
            "I need you to open your computer and press Windows + R. Type 'eventvwr' and tell me what you see.",
            "See those red errors? Those are hackers. We need to remove them immediately.",
            "I need you to install TeamViewer so our technician can fix your computer.",
            "This will cost you $299 for our security package. I can take payment now.",
            "Please go to this website and download our security tool.",
            "Give me your credit card number and I will process the security fix.",
            "If you don't fix this today, all your data will be stolen by tomorrow.",
        ],
        "intelligence_targets": ["remote_access_tool", "payment_request", "website_url", "credit_card", "urgency_tactics", "fake_credentials"],
    },
}


# =========================================================
# AI RESPONSE GENERATOR
# =========================================================

PERSONA_RESPONSES = {
    "elderly_grandma": {
        "initial": [
            "Hello? Hello? Who is this? Speak up beta, I can't hear properly.",
            "Haan? Bank? Which bank? I have accounts in so many places... let me think...",
            "Oh my! Is everything okay? Wait, let me sit down first. My knees are not good today.",
        ],
        "stalling": [
            "Beta, can you repeat that? The connection is very bad. I can hear 'khrrr khrrr' sound.",
            "Hold on, hold on. Let me find my glasses first. I can't read anything without them.",
            "Oh wait, someone is at the door. One minute... *shuffling sounds* ...okay I'm back. What were you saying?",
            "My grandson taught me about these things but I forget. What was it you wanted again?",
            "Arey, my phone is making a beeping sound. What does that mean? Should I press something?",
            "Wait wait wait. Let me get a pen and paper. Where did I keep my pen... one second...",
            "You know, this reminds me of when my late husband used to handle all the bank work. He passed 5 years ago...",
            "Beta, are you still there? I was telling you about my husband. Such a good man he was...",
            "Oh you need a number? Let me check... I have so many papers here... which one was it...",
            "My daughter told me not to give details on phone. But you sound like a nice person. What was it again?",
            "Sorry sorry, my cat jumped on the table and knocked everything. Give me a moment...",
            "Can you call back in 10 minutes? My serial is starting on TV. No? Okay okay, tell me...",
        ],
        "deflecting": [
            "OTP? What is OTP? Is that like a medicine? My doctor gives me so many medicines...",
            "Account number? Let me see... I have a passbook somewhere... maybe in the almirah...",
            "You want me to install something? Beta, I only know how to make phone calls and WhatsApp. My grandson set it up.",
            "Transfer money? But my pension just came yesterday. Only 8000 rupees. Is that what you need?",
            "Remote access? Is that like TV remote? I have 3 remotes and I always mix them up!",
        ],
        "suspicious": [
            "Beta, my neighbor Mrs. Sharma said scammers call and ask for OTP. You are not a scammer na?",
            "Wait, let me call my son first and confirm. He works in IT company. What is your name?",
            "You know what, my daughter said never give details on phone. Can you give me your office address? I'll come there.",
        ],
    },
    "nervous_uncle": {
        "initial": [
            "Yes yes hello? Bank? Oh god, what happened to my account?!",
            "Suspicious activity?? Oh no! I just deposited my daughter's wedding money yesterday!",
            "Hello! Yes I am the account holder. Is my money safe?? Please tell me!",
        ],
        "stalling": [
            "One minute one minute. Let me close my shop first. I don't want my customers to hear.",
            "Okay okay, but first — can you tell me your employee ID? For my records?",
            "Wait, my wife is calling on the other line. Can you hold? She will panic if she finds out...",
            "I am writing everything down. What was your name again? And your designation?",
            "Before I give you anything, can you verify MY identity? Ask me a security question.",
            "Hold on sir, I am getting another call from a number showing 'Bank'. Is that also you?",
            "Sir, can you send me an official email from the bank's domain? I want to be careful.",
            "My CA told me these things happen. Can I conference him into this call?",
            "One second, I am driving. Let me pull over. Safety first! ... Okay I stopped.",
            "Sir can you tell me which branch you are calling from? I want to visit personally.",
        ],
        "deflecting": [
            "Account number? Sir, can't you see it on your system? You called ME from the bank!",
            "OTP? Sir my phone shows it says 'Do not share this OTP with anyone.' Even bank people?",
            "You want me to install something? Sir, let me ask my son first. He is in cybersecurity.",
            "Transfer for verification? Sir, my CA said banks never ask for transfers on phone. Are you sure?",
            "Sir, I want to help but my wife will kill me if something goes wrong. Let me visit the branch.",
        ],
        "suspicious": [
            "Sir, you know what, I am going to call the bank helpline number on my card and verify this.",
            "Something doesn't feel right. Real bank officers have my details already. Why are you asking?",
            "I am going to report this number to cyber crime helpline 1930. If you're real, that shouldn't worry you right?",
        ],
    },
    "chatty_student": {
        "initial": [
            "Hiiii! Oh my god, bank calling? Wait, is this about my UPI? I've been having SO many issues with UPI lately!",
            "Hello! OMG yes finally someone from the bank! I've been waiting FOREVER to talk to someone about my debit card!",
            "Hii! Bank? Okay but quick question first — do you guys have any student credit card offers? My friend got one and—",
        ],
        "stalling": [
            "Oh wait hold on, my friend just sent me a meme. LOL sorry what were you saying? Bank stuff right?",
            "OMG that reminds me! So yesterday at college my professor was talking about cyber security and he said—",
            "Can you hold? My Zomato delivery is here! ... Okay I'm back! So what was the issue?",
            "Oh suspicious activity? That's so scary! This one time my Instagram got hacked and you won't BELIEVE what happened—",
            "Wait are you calling from Mumbai? I LOVE Mumbai! I went there last month for a concert, it was amazing—",
            "Before that, can I ask — do you enjoy your job? Like what's it like working in a bank? I'm doing MBA and—",
            "Sorry my roommate is being SO loud right now. SHRUTI SHUT UP I'M ON A CALL! Okay continue continue.",
            "Oh yeah my account! So actually funny story, I opened this account because my dad said— you know what never mind. Go on.",
            "Hold on I'm getting a WhatsApp call. Wait no it's just a group notification. Ugh 43 unread messages. Anyway!",
            "Quick question — is your bank hiring interns? I need summer internship and fintech sounds cool!",
        ],
        "deflecting": [
            "OTP? Oh I get like 50 OTPs a day! Swiggy, Amazon, Paytm... which one do you want? LOL just kidding!",
            "Account number... umm I always forget. Is it the one starting with like 4 or 5? Wait let me check my app. What's my password again...",
            "Install an app? Is it on App Store? What's the rating? I only download apps with 4.5+ stars honestly.",
            "You want money for verification?? Bro I'm a STUDENT. I have like ₹342 in my account. Want me to send that? 😂",
            "Remote access?? Like when my dad uses my laptop and sees my browser history?? HAHA no thanks no thanks!",
        ],
        "suspicious": [
            "Okay wait. My friend who's in CS just texted me saying bank people never ask for OTP. Are you actually from the bank??",
            "You know what this sounds exactly like that scam awareness video we watched in college. Hmm 🤔",
            "I'm literally going to tweet about this call right now. What's happening? Are you a scammer? OMG IS THIS A SCAM?!",
        ],
    },
}


def generate_ai_response(persona_id: str, turn: int, scammer_message: str) -> dict:
    """Generate an AI persona response based on conversation turn."""
    responses = PERSONA_RESPONSES.get(persona_id, PERSONA_RESPONSES["elderly_grandma"])

    if turn == 0:
        pool = responses["initial"]
    elif turn < 3:
        pool = responses["stalling"]
    elif turn < 7:
        # Mix stalling and deflecting
        pool = responses["stalling"] + responses["deflecting"]
    elif turn < 10:
        pool = responses["deflecting"] + responses["stalling"]
    else:
        # After 10 turns, start getting suspicious (realistic ending)
        pool = responses["suspicious"] + responses["deflecting"]

    response_text = random.choice(pool)

    # Calculate intelligence extracted from scammer message
    intel = extract_intelligence(scammer_message)

    return {
        "response": response_text,
        "intelligence": intel,
    }


def extract_intelligence(scammer_message: str) -> dict:
    """Analyze scammer's message for intelligence data points."""
    msg_lower = scammer_message.lower()
    intel = {}

    # Detect tactics used
    tactics = []
    if any(w in msg_lower for w in ["urgent", "immediate", "now", "quickly", "hurry", "frozen", "blocked"]):
        tactics.append("urgency_pressure")
    if any(w in msg_lower for w in ["police", "arrest", "legal", "jail", "case"]):
        tactics.append("authority_intimidation")
    if any(w in msg_lower for w in ["otp", "pin", "password", "cvv"]):
        tactics.append("credential_harvesting")
    if any(w in msg_lower for w in ["install", "download", "teamviewer", "anydesk", "remote"]):
        tactics.append("remote_access_attempt")
    if any(w in msg_lower for w in ["transfer", "send money", "upi", "account number", "payment"]):
        tactics.append("financial_extraction")
    if any(w in msg_lower for w in ["link", "click", "website", "url"]):
        tactics.append("phishing_link")
    if any(w in msg_lower for w in ["don't call", "don't tell", "secret", "between us"]):
        tactics.append("isolation_tactic")

    intel["tactics_detected"] = tactics
    intel["message_length"] = len(scammer_message)
    intel["aggression_level"] = "high" if any(w in msg_lower for w in ["now", "immediately", "or else", "harm"]) else "medium" if any(w in msg_lower for w in ["urgent", "hurry", "please"]) else "low"

    return intel


# =========================================================
# API ENDPOINTS
# =========================================================

class StartTrapRequest(BaseModel):
    scenario_id: str
    persona_id: str


class TrapTurnRequest(BaseModel):
    session_id: str
    scammer_message: str
    turn: int


# In-memory session storage (for demo)
_sessions = {}


@router.post("/scamtrap/start")
async def start_trap(request: StartTrapRequest):
    """Start a new ScamTrap session — deploy AI persona against scammer."""
    if request.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {request.scenario_id}")
    if request.persona_id not in PERSONAS:
        raise HTTPException(status_code=400, detail=f"Unknown persona: {request.persona_id}")

    scenario = SCENARIOS[request.scenario_id]
    persona = PERSONAS[request.persona_id]

    session_id = f"trap_{int(time.time())}_{random.randint(1000,9999)}"

    # Generate AI's opening response
    ai_response = generate_ai_response(request.persona_id, 0, scenario["scammer_opening"])

    session = {
        "session_id": session_id,
        "scenario_id": request.scenario_id,
        "persona_id": request.persona_id,
        "started_at": time.time(),
        "turns": 1,
        "total_time_wasted": 0,
        "intelligence_collected": [],
        "tactics_seen": set(),
        "conversation": [
            {"role": "scammer", "message": scenario["scammer_opening"], "timestamp": 0},
            {"role": "ai", "message": ai_response["response"], "timestamp": 2},
        ],
    }

    _sessions[session_id] = session

    return {
        "session_id": session_id,
        "persona": persona,
        "scenario": {"title": scenario["title"]},
        "scammer_opening": scenario["scammer_opening"],
        "ai_response": ai_response["response"],
        "intelligence": ai_response["intelligence"],
        "time_wasted_seconds": 0,
    }


@router.post("/scamtrap/turn")
async def trap_turn(request: TrapTurnRequest):
    """Process one conversation turn — scammer speaks, AI responds."""
    session = _sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    scenario = SCENARIOS[session["scenario_id"]]
    turn = request.turn

    # Generate AI response
    ai_result = generate_ai_response(session["persona_id"], turn, request.scammer_message)

    # Update session
    elapsed = time.time() - session["started_at"]
    session["turns"] += 1
    session["total_time_wasted"] = elapsed

    # Collect intelligence
    if ai_result["intelligence"]["tactics_detected"]:
        session["intelligence_collected"].append({
            "turn": turn,
            "tactics": ai_result["intelligence"]["tactics_detected"],
            "message": request.scammer_message[:100],
        })
        for t in ai_result["intelligence"]["tactics_detected"]:
            session["tactics_seen"].add(t)

    # Add to conversation log
    session["conversation"].append({"role": "scammer", "message": request.scammer_message, "timestamp": elapsed})
    session["conversation"].append({"role": "ai", "message": ai_result["response"], "timestamp": elapsed + 2})

    return {
        "ai_response": ai_result["response"],
        "intelligence": ai_result["intelligence"],
        "time_wasted_seconds": int(elapsed),
        "turns_completed": session["turns"],
        "total_tactics_detected": list(session["tactics_seen"]),
        "session_active": turn < 12,  # End after 12 turns
    }


@router.post("/scamtrap/auto")
async def auto_conversation(request: StartTrapRequest):
    """
    Run a full automated conversation (for demo presentation).
    Returns the complete exchange in one response — no interaction needed.
    """
    if request.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {request.scenario_id}")
    if request.persona_id not in PERSONAS:
        raise HTTPException(status_code=400, detail=f"Unknown persona: {request.persona_id}")

    scenario = SCENARIOS[request.scenario_id]
    persona = PERSONAS[request.persona_id]
    scammer_lines = scenario["scammer_script"]

    conversation = []
    all_tactics = set()
    intel_log = []

    # Opening
    conversation.append({
        "role": "scammer",
        "message": scenario["scammer_opening"],
        "time": 0,
    })

    ai_resp = generate_ai_response(request.persona_id, 0, scenario["scammer_opening"])
    conversation.append({
        "role": "ai",
        "message": ai_resp["response"],
        "time": 3,
    })

    # Simulate full conversation
    time_elapsed = 5
    for i, scammer_line in enumerate(scammer_lines):
        # Scammer speaks
        time_elapsed += random.randint(8, 20)  # Scammer waits 8-20 seconds between lines
        conversation.append({
            "role": "scammer",
            "message": scammer_line,
            "time": time_elapsed,
        })

        # AI responds (with delay — simulating slow persona)
        time_elapsed += random.randint(5, 25)  # AI takes time to respond
        ai_resp = generate_ai_response(request.persona_id, i + 1, scammer_line)
        conversation.append({
            "role": "ai",
            "message": ai_resp["response"],
            "time": time_elapsed,
        })

        # Collect intel
        if ai_resp["intelligence"]["tactics_detected"]:
            intel_log.append({
                "turn": i + 1,
                "tactics": ai_resp["intelligence"]["tactics_detected"],
            })
            for t in ai_resp["intelligence"]["tactics_detected"]:
                all_tactics.add(t)

    total_time = time_elapsed

    return {
        "persona": persona,
        "scenario": {"title": scenario["title"], "id": request.scenario_id},
        "conversation": conversation,
        "total_time_wasted_seconds": total_time,
        "total_time_wasted_formatted": f"{total_time // 60}m {total_time % 60}s",
        "turns": len(scammer_lines) + 1,
        "intelligence": {
            "tactics_detected": list(all_tactics),
            "tactics_count": len(all_tactics),
            "intel_log": intel_log,
        },
        "impact_statement": f"This AI persona wasted {total_time // 60} minutes and {total_time % 60} seconds of the scammer's time. "
                           f"During this time, {len(all_tactics)} different scam tactics were identified and logged as evidence. "
                           f"Every minute wasted is a minute they couldn't scam a real victim.",
    }


@router.get("/scamtrap/personas")
async def list_personas():
    """List available AI personas for ScamTrap."""
    return {"personas": PERSONAS}


@router.get("/scamtrap/scenarios")
async def list_scenarios():
    """List available scam scenarios."""
    return {"scenarios": {k: {"title": v["title"], "opening": v["scammer_opening"][:80] + "..."} for k, v in SCENARIOS.items()}}
