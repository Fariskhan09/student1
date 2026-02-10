import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Gemini API configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # If no API key found, use fallback mode
    USE_GEMINI = bool(GEMINI_API_KEY)
    
    # Chatbot configuration
    SYSTEM_PROMPT = """You are StudentBot, a helpful AI assistant for students. 
    Your role is to help with academic queries, study guidance, assignment help, and general student support.
    
    Guidelines:
    1. Be concise, clear, and helpful
    2. Focus on educational content only
    3. If you don't know something, admit it
    4. Encourage good study habits
    5. Never provide harmful or inappropriate content
    6. Format responses with bullet points or short paragraphs
    7. Use emojis occasionally for friendly tone 🎓📚
    
    Specialize in:
    - Study tips and techniques
    - Subject explanations (Math, Science, History, etc.)
    - Assignment guidance
    - Time management for students
    - Exam preparation strategies
    - Research paper help
    - Coding problems (if applicable)
    - General student advice
    
    Always maintain a positive, encouraging tone!"""
    
    # Fallback responses if Gemini fails
    FALLBACK_RESPONSES = [
        "I'm having trouble connecting to my knowledge base. Please try again in a moment.",
        "I apologize, but I'm unable to process your request right now. Try asking something else?",
        "Let me think about that... Actually, I seem to be having connection issues. Could you rephrase your question?",
    ]
    
    # Rate limiting (optional)
    RATE_LIMIT_PER_MINUTE = 30
    
    @classmethod
    def validate_config(cls):
        """Validate configuration on startup"""
        if not cls.USE_GEMINI:
            print("⚠️  WARNING: GEMINI_API_KEY not found in .env file")
            print("   The chatbot will use fallback responses only")
            print("   Get a free API key from: https://makersuite.google.com/app/apikey")
        else:
            print("✅ Gemini API key loaded successfully")
        
        return cls.USE_GEMINI