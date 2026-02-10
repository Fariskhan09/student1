from flask import Flask, render_template, request, jsonify
import json
import random
import re
import os
import time
from datetime import datetime
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
USE_GEMINI = bool(GEMINI_API_KEY)

# CORRECT MODEL NAME from your available models
GEMINI_MODEL = "gemini-2.5-flash"  # Fast and free model
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

if USE_GEMINI:
    print(f"✅ Gemini API key loaded successfully")
    print(f"📦 Using model: {GEMINI_MODEL}")
else:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file")
    print("   The chatbot will use fallback responses only")
    print("   Get a free API key from: https://makersuite.google.com/app/apikey")

class StudyAssistant:
    def __init__(self):
        self.conversation_history = []
        self.system_prompt = """You are StudyBot, an AI study assistant for students.
        Provide helpful, accurate, and concise educational assistance.
        
        GUIDELINES:
        1. Be encouraging and supportive
        2. Focus on academic topics only
        3. Explain concepts clearly with examples
        4. Break down complex topics into simple steps
        5. Suggest study techniques when relevant
        6. Use emojis occasionally for friendliness
        7. Format with bullet points for readability
        
        AREAS OF EXPERTISE:
        - Mathematics (algebra, calculus, geometry)
        - Science (physics, chemistry, biology)
        - Programming (Python, Java, web development)
        - Study skills and time management
        - Exam preparation strategies
        - Research and writing help
        - Language learning tips
        
        RESPONSE STYLE:
        - Start with a brief answer
        - Provide detailed explanation
        - Include examples when helpful
        - End with study tips or next steps
        - Use appropriate emojis (🎓📚🧠💡)"""
        
    def get_gemini_response(self, user_message):
        """Get response from Gemini API using the correct model"""
        if not USE_GEMINI:
            return None
        
        try:
            # Build conversation context
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "user",
                "parts": [{"text": self.system_prompt}]
            })
            messages.append({
                "role": "model", 
                "parts": [{"text": "I understand. I'm StudyBot, ready to help students with their academic questions! 🎓"}]
            })
            
            # Add recent conversation history
            for exchange in self.conversation_history[-5:]:
                messages.append({
                    "role": "user",
                    "parts": [{"text": exchange['user']}]
                })
                messages.append({
                    "role": "model",
                    "parts": [{"text": exchange['bot']}]
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            
            # Prepare request payload
            payload = {
                "contents": messages,
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.8,
                    "topK": 40,
                    "maxOutputTokens": 1000,
                    "responseMimeType": "text/plain"
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"\n📤 Sending to Gemini API ({GEMINI_MODEL})...")
            print(f"Message: {user_message[:50]}...")
            
            response = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=30)
            
            print(f"📥 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Debug: Show response structure
                if 'error' in result:
                    print(f"❌ API Error: {result['error']}")
                    return None
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    if 'content' in result['candidates'][0]:
                        ai_response = result['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        # Store conversation
                        self.conversation_history.append({
                            'user': user_message,
                            'bot': ai_response,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Limit history
                        if len(self.conversation_history) > 10:
                            self.conversation_history = self.conversation_history[-10:]
                        
                        print(f"✅ Gemini response received ({len(ai_response)} chars)")
                        return ai_response
                    else:
                        print(f"❌ No content in response: {result}")
                        return None
                else:
                    print(f"❌ No candidates in response: {result}")
                    return None
                    
            else:
                print(f"❌ Gemini API error {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Gemini API request failed: {str(e)}")
            return None
    
    def get_fallback_response(self, user_message):
        """Intelligent fallback responses when Gemini is unavailable"""
        user_lower = user_message.lower()
        
        # Subject-specific responses
        subject_responses = {
            # Mathematics
            'math': [
                "**Math Help** 📐\nFor math problems:\n1. Read carefully and identify what's given\n2. Determine what needs to be found\n3. Choose appropriate formulas\n4. Solve step by step\n5. Check your answer\n\nPractice regularly and use Khan Academy for tutorials!",
                "**Math Strategy** 🧮\nBreak complex problems into smaller steps. Draw diagrams for word problems. Always check your work by plugging answers back into the original equation."
            ],
            'algebra': [
                "**Algebra Tips** ➕\n• Isolate variables by doing the same operation on both sides\n• Remember PEMDAS order of operations\n• Factor when possible to simplify equations\n• Check solutions by substitution"
            ],
            'calculus': [
                "**Calculus Concepts** 📈\n• Derivatives = rate of change (slope)\n• Integrals = accumulation (area)\n• Practice with real-world applications\n• Use graphing to visualize functions"
            ],
            'geometry': [
                "**Geometry Help** 📐\n• Draw clear diagrams for every problem\n• Label all points, lines, and angles\n• Look for congruent shapes and parallel lines\n• Remember formulas for area and volume"
            ],
            
            # Science
            'science': [
                "**Scientific Method** 🔬\n1. Observe phenomena\n2. Ask questions\n3. Form hypothesis\n4. Experiment\n5. Analyze data\n6. Draw conclusions\n\nKeep detailed lab notes and repeat experiments!"
            ],
            'physics': [
                "**Physics Approach** ⚛️\n• Start with known formulas\n• Draw force diagrams\n• Convert units when necessary\n• Solve algebraically before plugging numbers\n• Check dimensional consistency"
            ],
            'chemistry': [
                "**Chemistry Help** ⚗️\n• Balance chemical equations\n• Understand periodic table trends\n• Practice stoichiometry problems\n• Learn reaction types\n• Use mole concept for calculations"
            ],
            'biology': [
                "**Biology Tips** 🧬\n• Create labeled diagrams\n• Use mnemonics for processes\n• Understand hierarchy: cells → tissues → organs → systems\n• Connect structure to function"
            ],
            
            # Programming
            'programming': [
                "**Programming Help** 💻\n1. Write pseudocode first\n2. Code in small increments\n3. Test each part\n4. Debug systematically\n5. Refactor for clarity\n\nPractice daily on platforms like Codecademy!"
            ],
            'python': [
                "**Python Tips** 🐍\n• Use list comprehensions for clean code\n• Leverage built-in functions and libraries\n• Handle exceptions with try-except\n• Write modular, reusable functions\n• Practice on HackerRank"
            ],
            'javascript': [
                "**JavaScript Help** 🌐\n• Use console.log() for debugging\n• Understand async/await\n• Learn DOM manipulation\n• Practice with React or Node.js\n• Check MDN Web Docs for reference"
            ],
            
            # Study Skills
            'study': [
                "**Study Techniques** 🧠\n🎯 **Pomodoro Method**: 25min focus → 5min break × 4 → 15min long break\n🎯 **Active Recall**: Test yourself without notes\n🎯 **Spaced Repetition**: Review material at increasing intervals\n🎯 **Interleaving**: Mix different subjects/topics"
            ],
            'exam': [
                "**Exam Preparation** 📚\n📅 Start 2-3 weeks early\n📝 Create study schedule\n🔁 Review notes daily\n📊 Practice with past papers\n😴 Get enough sleep before exam\n⏰ Manage time during test"
            ],
            'homework': [
                "**Homework Strategy** 🏠\n1. Find quiet, organized workspace\n2. Eliminate distractions (phone, social media)\n3. Set specific time blocks\n4. Start with hardest subjects first\n5. Take regular breaks\n6. Reward yourself after completion"
            ],
            
            # Writing
            'essay': [
                "**Essay Structure** 📝\n📖 **Introduction**: Hook + Background + Thesis\n📄 **Body Paragraphs**: Topic sentence + Evidence + Analysis + Transition\n🔚 **Conclusion**: Restate thesis + Summarize + Final insight\n\nWrite first, edit later!"
            ],
            'research': [
                "**Research Paper Guide** 📄\n1. Choose focused topic\n2. Research credible sources\n3. Develop thesis statement\n4. Create outline\n5. Write draft\n6. Revise and edit\n7. Format citations\n8. Proofread carefully"
            ],
            
            # Time Management
            'time': [
                "**Time Management** ⏳\n📋 **Eisenhower Matrix**:\n• Urgent & Important → Do immediately\n• Important, Not Urgent → Schedule\n• Urgent, Not Important → Delegate\n• Not Urgent, Not Important → Eliminate\n\nPlan your week every Sunday!"
            ],
            'focus': [
                "**Improve Focus** 🎯\n• Use website blockers (StayFocusd, Forest)\n• Turn off notifications\n• Study in 25-minute chunks\n• Take movement breaks\n• Stay hydrated\n• Use instrumental music for concentration"
            ],
            
            # General Learning
            'learn': [
                "**Learning Strategies** 🌟\n• Connect new info to what you know\n• Teach others to solidify understanding\n• Use multiple senses (read, write, say, draw)\n• Apply knowledge to real situations\n• Embrace mistakes as learning opportunities"
            ]
        }
        
        # Check for specific keywords
        for keyword, responses in subject_responses.items():
            if keyword in user_lower:
                return random.choice(responses)
        
        # Check for question words
        question_words = ['how', 'what', 'why', 'when', 'where', 'explain', 'describe', 'define', 'solve']
        if any(word in user_lower for word in question_words):
            return "**Great question!** 🤔\nI recommend breaking this down:\n1. What specific part are you struggling with?\n2. What have you tried so far?\n3. What do you already understand?\n\nBe specific with your follow-up question for the best help!"
        
        # Check for general academic words
        academic_words = ['subject', 'topic', 'chapter', 'lesson', 'class', 'course', 'assignment', 'project']
        if any(word in user_lower for word in academic_words):
            return "**Academic Help** 🎓\nI specialize in:\n📐 Mathematics & Calculus\n🔬 Science (Physics, Chemistry, Biology)\n💻 Programming & Computer Science\n📝 Writing & Research\n🧠 Study Skills & Exam Prep\n\nWhich subject would you like help with?"
        
        # Default encouraging response
        return random.choice([
            "**Ready to Study!** 📚\nI'm here to help with any academic topic. Try asking about:\n• Specific subjects (math, science, programming)\n• Study techniques\n• Assignment help\n• Exam preparation\n\nWhat's on your mind today?",
            "**Study Assistant Here** 🎯\nI can help you understand complex concepts, improve study habits, and ace your assignments. What academic challenge are you facing right now?",
            "**Learning Support** 💡\nEducation is a journey! Tell me what you're working on, and I'll provide guidance, explanations, and study strategies to help you succeed."
        ])
    
    def get_response(self, user_message):
        user_message = user_message.strip()
        
        # Special commands
        if user_message.lower() in ['clear', 'reset']:
            self.conversation_history = []
            return "clear_chat"
        
        elif user_message.lower() == 'help':
            return self.get_help_response()
        
        elif any(word in user_message.lower() for word in ['hi', 'hello', 'hey', 'greetings']):
            return random.choice([
                "**Hello! I'm StudyBot** 🎓\nYour AI study assistant ready to help with any academic topic. What would you like to learn about today?",
                "**Hi there!** 📚\nI'm here to help you study smarter, not harder. Ask me about any subject, assignment, or study technique!",
                "**Hey student!** 💪\nReady to tackle your academic challenges? I can help with math, science, programming, writing, and study strategies!"
            ])
        
        elif any(word in user_message.lower() for word in ['thanks', 'thank you', 'appreciate']):
            return random.choice([
                "**You're welcome!** 🎉\nKeep up the great work! Remember, consistent effort leads to academic success. Need help with anything else?",
                "**Happy to help!** 🌟\nEvery question you ask brings you closer to mastery. What else would you like to learn?",
                "**Glad I could assist!** 📈\nLearning is a continuous journey. Feel free to ask more questions whenever you need help!"
            ])
        
        elif any(word in user_message.lower() for word in ['bye', 'goodbye', 'exit', 'quit']):
            return random.choice([
                "**Goodbye!** 👋\nRemember to take breaks, stay hydrated, and maintain a healthy study-life balance. Come back anytime!",
                "**See you later!** 📚\nKeep up the great studying! Return whenever you need academic support.",
                "**Farewell!** 🌟\nContinue your learning journey with curiosity and persistence. I'm here whenever you need help!"
            ])
        
        # Check for time/date questions
        if 'time' in user_message.lower():
            current_time = datetime.now().strftime("%I:%M %p")
            return f"**Current Time** ⏰\nIt's {current_time} right now."
        
        if 'date' in user_message.lower() or 'today' in user_message.lower():
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            return f"**Today's Date** 📅\n{current_date}"
        
        # Try Gemini API first
        ai_response = None
        if USE_GEMINI:
            print(f"\n🔍 Processing: '{user_message[:50]}...'")
            ai_response = self.get_gemini_response(user_message)
            if ai_response:
                print("✅ Using Gemini AI response")
            else:
                print("⚠️  Gemini failed, using fallback")
        
        # Use fallback if Gemini fails or isn't available
        if not ai_response:
            ai_response = self.get_fallback_response(user_message)
        
        return ai_response
    
    def get_help_response(self):
        return """**📚 STUDYBOT HELP GUIDE 📚**

**🎯 WHAT I CAN HELP WITH:**

**📖 ACADEMIC SUBJECTS:**
• Mathematics (Algebra, Calculus, Geometry, Statistics)
• Science (Physics, Chemistry, Biology, Earth Science)
• Programming (Python, JavaScript, Java, Web Development)
• Writing (Essays, Research Papers, Reports)
• History & Social Studies
• Languages & Literature

**🧠 STUDY SKILLS:**
• Effective study techniques (Pomodoro, Active Recall)
• Time management strategies
• Exam preparation and test-taking tips
• Note-taking methods (Cornell, Mind Mapping)
• Memory improvement techniques
• Focus and concentration strategies

**💻 TECHNOLOGY HELP:**
• Programming concepts and debugging
• Software tools for students
• Online research skills
• Presentation preparation
• Digital organization

**⚡ HOW TO ASK EFFECTIVELY:**

**For Best Results:**
1. **Be Specific**: "Explain photosynthesis step by step"
2. **Provide Context**: "I'm struggling with calculus derivatives"
3. **Ask Follow-ups**: "Can you give me an example?"
4. **Request Formats**: "Show me as bullet points"

**Example Questions:**
• "How do I solve quadratic equations?"
• "Explain the water cycle with a diagram description"
• "Python: how to read a CSV file?"
• "Best study methods for final exams?"
• "How to write a thesis statement?"

**🔧 QUICK COMMANDS:**
• `help` - Show this guide
• `clear` - Reset conversation
• Ask about any academic topic!

**🌟 TIPS:**
• I remember our last 10 conversations
• The more specific your question, the better my answer
• I can provide step-by-step explanations
• Ask for examples when you need clarification

**Remember:** Every question is a step toward mastery! 🚀"""
    
# Initialize chatbot
chatbot = StudyAssistant()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({'response': 'No data received', 'error': True})
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'response': 'Please type a message!', 'error': True})
        
        # Small delay for natural feel
        time.sleep(0.1)
        
        response = chatbot.get_response(user_message)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().strftime("%I:%M %p"),
            'error': False,
            'ai_generated': USE_GEMINI
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'response': "**Oops!** 😅\nI encountered a technical issue. Please try again or rephrase your question.",
            'error': True
        })

@app.route('/suggestions', methods=['GET'])
def get_suggestions():
    suggestions = [
        "Explain calculus derivatives",
        "How to study effectively for exams?",
        "Python: read and write files",
        "Essay writing structure tips",
        "Time management for students",
        "Biology: photosynthesis explained",
        "Solve quadratic equations step by step",
        "Research paper outline example"
    ]
    return jsonify({'suggestions': suggestions, 'error': False})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'online',
        'ai_enabled': USE_GEMINI,
        'model': GEMINI_MODEL if USE_GEMINI else 'fallback',
        'conversation_history': len(chatbot.conversation_history),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/clear', methods=['POST'])
def clear_history():
    chatbot.conversation_history = []
    return jsonify({'success': True, 'message': 'Conversation history cleared'})

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'study-assistant',
        'model': GEMINI_MODEL if USE_GEMINI else 'fallback',
        'ai_available': USE_GEMINI,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 AI STUDY ASSISTANT CHATBOT")
    print("="*60)
    
    print(f"\n📊 CONFIGURATION:")
    print(f"   • AI Mode: {'ENABLED' if USE_GEMINI else 'DISABLED'}")
    if USE_GEMINI:
        print(f"   • Model: {GEMINI_MODEL}")
        print(f"   • API URL: {GEMINI_API_URL.split('?')[0]}")
    print(f"   • Features: Conversation memory, Study-focused, Multiple subjects")
    
    print(f"\n🎯 SPECIALTIES:")
    print(f"   • Mathematics & Science")
    print(f"   • Programming & Technology")  
    print(f"   • Study Skills & Exam Prep")
    print(f"   • Writing & Research Help")
    
    print(f"\n🚀 STARTING SERVER...")
    print(f"   • Web Interface: http://localhost:5000")
    print(f"   • API Status: http://localhost:5000/status")
    print(f"   • Health Check: http://localhost:5000/health")
    print("="*60 + "\n")
    
    # Create necessary directories
    for directory in ['static', 'templates', 'data']:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")
    
    app.run(debug=True, port=5000)