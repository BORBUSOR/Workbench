import os
import json
import sqlite3
from PIL import Image
from google import genai
from google.genai import types

# Anchor paths strictly to the directory where this script resides (FunFolder/ZCS Scheduler)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "learned_cache.json")
DB_FILE = os.path.join(BASE_DIR, "schedules.db")

SCHOOL_PROFILES = {
    "University of Central Florida (UCF)": {
        "description": "UCF MyUCF Portal Table Format"
    },
    "Other / Custom University": {
        "description": "Standard University Portal Format"
    }
}

def get_supported_schools():
    return list(SCHOOL_PROFILES.keys())

def init_db():
    """Initializes the local SQLite database for email-based schedule caching."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_cache (
            email TEXT,
            cache_key TEXT,
            courses_json TEXT,
            PRIMARY KEY (email, cache_key)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on module load
init_db()

def load_from_db(email, cache_key):
    if not email:
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT courses_json FROM schedule_cache WHERE email = ? AND cache_key = ?", (email, cache_key))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
    except Exception as e:
        print(f"Database load error: {e}")
    return None

def save_to_db(email, cache_key, courses):
    if not email:
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO schedule_cache (email, cache_key, courses_json)
            VALUES (?, ?, ?)
        ''', (email, cache_key, json.dumps(courses)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database save error: {e}")

def parse_schedule_text(raw_text, school_name, image_path=None, email=None):
    """Parses tabular schedules using an email-indexed SQLite database cache and model fallbacks."""
    
    cache_key = os.path.basename(image_path) if image_path else raw_text[:50]
    
    # 1. Check SQLite database first using email + cache_key
    if email:
        cached_courses = load_from_db(email, cache_key)
        if cached_courses:
            print(f"Loading schedule from database cache for email: {email}")
            return cached_courses

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from your .env file.")
            
        client = genai.Client(api_key=api_key)
        
        if not image_path or not os.path.exists(image_path):
            raise FileNotFoundError("Schedule image path was not provided to the parser.")
            
        img = Image.open(image_path)
        
        prompt = f"""
        You are an expert academic schedule parser for {school_name}.
        Analyze this schedule image carefully. Look at the 'Class' and 'Schedule' columns.
        Pay close attention to text printed below course codes (like 'WAITLIST' in red).
        Extract all courses into a strict JSON list format. Each item must be a dictionary with these exact keys:
        - "name": Course code and number including section/type (e.g., "EGN 3343-0002" or "MUT 2126-0011 LAB").
        - "days": Meeting days (e.g., "Tu", "TuTh", "MoWeFr", or "TBA").
        - "time": Time range (e.g., "9:00AM - 10:15AM", or "TBA").
        - "room": Building and room (e.g., "HS1 0119", "HEC 0125", or "TBA").
        - "status": Set to "Pending" if the class block contains "WAITLIST" or "Waiting", otherwise set to "Active".
        
        Return ONLY valid JSON. Do not include markdown code block ticks like ```json ... ```, just output the raw JSON list brackets `[...]`.
        """
        
        models_to_try = [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash"
        ]
        
        response = None
        last_exception = None
        
        for model_name in models_to_try:
            try:
                print(f"Attempting schedule parse with model: {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[img, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )
                if response and response.text:
                    break
            except Exception as model_err:
                print(f"Model {model_name} unavailable or failed: {model_err}")
                last_exception = model_err
                continue
                
        if not response or not response.text:
            raise last_exception or Exception("All model fallback attempts failed.")
        
        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        courses = json.loads(response_text)
        
        # Save successfully parsed result to SQLite database keyed by email
        if courses and email:
            save_to_db(email, cache_key, courses)
            
        return courses
        
    except Exception as e:
        print(f"Gemini Parsing Error: {e}")
        return [{"name": "Parsing Error - Check API Key / Quota", "days": "TBA", "time": "TBA", "room": "TBA", "status": "Active"}]