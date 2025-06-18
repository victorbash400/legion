# legion_adk/config.py

import os

# Google Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCZu4Dn1H2vOVSEzdxeddDXGLZNpn3--R4")

# Sonar API Key for web research
SONAR_API_KEY = os.getenv("SONAR_API_KEY", "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")

# ADK Configuration (basic for now)
ADK_CONFIG = {
    "model_name": "gemini-pro", # Using gemini-pro as a default
    "temperature": 0.7,
}

# Firestore configuration (for future use)
FIRESTORE_COLLECTION_NAME = "adk_agent_states"