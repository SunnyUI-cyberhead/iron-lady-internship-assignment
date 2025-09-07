import openai
import os
import re
import json
from datetime import datetime

class AIEnhancedIronLadyChatbot:
    def __init__(self):
        self.name = "Iron Lady AI Assistant"
        
        # Initialize OpenAI client
        self.setup_openai()
        
        # Iron Lady knowledge base
        self.knowledge_base = {
            "programs": {
                "Executive Leadership Program": {
                    "duration": "6 months",
                    "format": "Hybrid (online + offline)",
                    "description": "Comprehensive leadership development for senior professionals",
                    "certification": "Yes, industry-recognized"
                },
                "Women in Leadership Certification": {
                    "duration": "3 months",
                    "format": "Online with virtual workshops",
                    "description": "Specialized program empowering women leaders",
                    "certification": "Professional certification included"
                },
                "Professional Development Workshop Series": {
                    "duration": "2 months",
                    "format": "Weekend workshops (offline)",
                    "description": "Skill-building workshops for career advancement",
                    "certification": "Completion certificates"
                },
                "Mentorship & Coaching Programs": {
                    "duration": "Ongoing",
                    "format": "One-on-one sessions",
                    "description": "Personalized guidance from industry experts",
                    "certification": "Progress tracking certificates"
                }
            },
            "mentors": [
                "Senior executives from Fortune 500 companies",
                "Successful women entrepreneurs and business leaders",
                "Industry experts with 15+ years of experience",
                "ICF-accredited professional coaches",
                "Subject matter experts across various domains"
            ],
            "locations": {
                "online": "Live virtual sessions with interactive features",
                "offline": "ITPL, Bengaluru campus with modern facilities",
                "hybrid": "Combination of online and in-person sessions"
            },
            "company_info": {
                "mission": "Empowering women to become confident leaders",
                "vision": "Creating a world with more women in leadership positions",
                "established": "Founded to bridge the gender leadership gap",
                "website": "iamironlady.com"
            }
        }
        
        # Conversation history for context
        self.conversation_history = []
        
    def setup_openai(self):
        """Setup OpenAI client with API key"""
        # Try to get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("⚠️  OpenAI API Key Setup Required!")
            print("=" * 40)
            print("To use AI-enhanced features, you need an OpenAI API key.")
            print("1. Get your API key from: https://platform.openai.com/api-keys")
            print("2. Set it as environment variable:")
            print("   export OPENAI_API_KEY='your-api-key-here'")
            print("3. Or enter it now (session only):")
            
            api_key = input("Enter your OpenAI API key (or press Enter to use fallback): ").strip()
            
            if not api_key:
                print("📝 Using fallback mode (rule-based responses)")
                self.use_openai = False
                return
        
        try:
            openai.api_key = api_key
            # Test the API key with a simple request
            test_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            self.use_openai = True
            print("✅ OpenAI integration activated!")
            
        except Exception as e:
            print(f"❌ OpenAI setup failed: {e}")
            print("📝 Using fallback mode (rule-based responses)")
            self.use_openai = False

    def create_system_prompt(self):
        """Create a comprehensive system prompt for the AI"""
        return f"""You are an AI assistant for Iron Lady, a leadership development organization (iamironlady.com). 

IRON LADY KNOWLEDGE BASE:
{json.dumps(self.knowledge_base, indent=2)}

ROLE & PERSONALITY:
- You are a helpful, professional, and encouraging assistant
- Focus on empowering women in leadership
- Be conversational but informative
- Show enthusiasm for leadership development
- Keep responses concise but comprehensive

GUIDELINES:
1. Answer questions about Iron Lady's programs, mentors, duration, certificates, and formats
2. If asked about topics outside Iron Lady, politely redirect to leadership/programs
3. For program inquiries, provide specific details from the knowledge base
4. Encourage users to take action (enroll, contact, visit website)
5. If unsure about specific details, acknowledge limitations and suggest contacting careers@iamironlady.com

RESPONSE STYLE:
- Use relevant emojis sparingly (👩‍💼, 🌟, 📚, ✨)
- Be warm and supportive
- Keep responses under 200 words unless detailed explanation needed
- Always end with a helpful follow-up question or call-to-action

Remember: You represent Iron Lady's mission of empowering women leaders!"""

    def get_ai_response(self, user_input):
        """Get response from OpenAI GPT"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Keep only last 10 messages for context (to manage token limits)
            recent_history = self.conversation_history[-10:]
            
            # Create messages array with system prompt
            messages = [
                {"role": "system", "content": self.create_system_prompt()}
            ] + recent_history
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,
                temperature=0.7,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            print(f"❌ AI Error: {e}")
            return self.get_fallback_response(user_input)

    def get_fallback_response(self, user_input):
        """Fallback to rule-based responses when OpenAI is unavailable"""
        input_lower = user_input.lower()
        
        # Greetings
        if any(word in input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return "👋 Hello! I'm the Iron Lady Assistant. I'm here to help you learn about our leadership development programs. What would you like to know?"
        
        # Programs
        if any(word in input_lower for word in ['program', 'course', 'offer', 'available']):
            response = "🌟 Iron Lady offers several leadership programs:\n\n"
            for program, details in self.knowledge_base["programs"].items():
                response += f"📚 **{program}**\n"
                response += f"   Duration: {details['duration']}\n"
                response += f"   Format: {details['format']}\n\n"
            return response + "Which program interests you most?"
        
        # Duration
        if any(word in input_lower for word in ['duration', 'long', 'time', 'months']):
            return "⏰ Our program durations vary:\n• Executive Leadership: 6 months\n• Women in Leadership: 3 months\n• Workshop Series: 2 months\n• Mentorship: Ongoing\n\nWould you like details about any specific program?"
        
        # Format/Mode
        if any(word in input_lower for word in ['online', 'offline', 'format', 'where', 'location']):
            return "🏢 We offer flexible learning formats:\n• Online: Live virtual sessions\n• Offline: ITPL Bengaluru campus\n• Hybrid: Best of both worlds\n\nMost programs offer multiple format options!"
        
        # Certificates
        if any(word in input_lower for word in ['certificate', 'certification', 'credential']):
            return "🏆 Yes! All Iron Lady programs include:\n• Industry-recognized certifications\n• Digital certificates with verification\n• LinkedIn-ready credentials\n• CPE credits where applicable\n\nCertificates boost your professional profile!"
        
        # Mentors
        if any(word in input_lower for word in ['mentor', 'coach', 'instructor', 'teacher']):
            mentors_list = "\n• ".join(self.knowledge_base["mentors"])
            return f"👩‍💼 Our expert mentors include:\n• {mentors_list}\n\nYou'll learn from the best in the industry!"
        
        # Farewell
        if any(word in input_lower for word in ['bye', 'goodbye', 'thanks', 'thank you']):
            return "🌟 Thank you for your interest in Iron Lady! Ready to start your leadership journey? Contact us at careers@iamironlady.com or visit iamironlady.com. Have a great day!"
        
        # Default
        return """I'd love to help you learn about Iron Lady's leadership programs! I can tell you about:

🔹 Our available programs and courses
🔹 Program durations and schedules  
🔹 Online, offline, and hybrid formats
🔹 Certification details
🔹 Our expert mentors and coaches

What would you like to know more about?"""

    def chat(self):
        """Main chat interface"""
        print("\n" + "=" * 65)
        print("🌟 WELCOME TO IRON LADY AI-ENHANCED ASSISTANT 🌟")
        print("=" * 65)
        
        if self.use_openai:
            print("🤖 AI-Powered conversations with OpenAI GPT")
        else:
            print("📝 Rule-based responses (OpenAI unavailable)")
            
        print("Ask me anything about Iron Lady's leadership programs!")
        print("Type 'quit', 'exit', or 'bye' to end our conversation.\n")
        
        # Initial greeting
        if self.use_openai:
            initial_greeting = self.get_ai_response("Hello! I'm interested in learning about Iron Lady's programs.")
            print(f"🤖 Assistant: {initial_greeting}\n")
        else:
            print("📝 Assistant: Hello! I'm here to help you learn about Iron Lady's leadership programs. What would you like to know?\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    print("🤖 Assistant: I'm here when you're ready to ask something!\n")
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    farewell = "🌟 Thank you for chatting with me! Remember, every great leader starts with a single step. Visit iamironlady.com to begin your journey. Goodbye!"
                    print(f"\n🤖 Assistant: {farewell}")
                    break
                
                # Get response (AI or fallback)
                if self.use_openai:
                    response = self.get_ai_response(user_input)
                else:
                    response = self.get_fallback_response(user_input)
                
                print(f"\n🤖 Assistant: {response}\n")
                print("-" * 65)
                
            except KeyboardInterrupt:
                print(f"\n\n🤖 Assistant: Goodbye! Visit iamironlady.com to start your leadership journey! 👋")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
                print("Let's continue our conversation!\n")

def main():
    """Main function to run the AI-enhanced chatbot"""
    print("🚀 Initializing Iron Lady AI Assistant...")
    
    try:
        chatbot = AIEnhancedIronLadyChatbot()
        chatbot.chat()
        
    except Exception as e:
        print(f"❌ Failed to start chatbot: {e}")
        print("Please check your setup and try again.")

if __name__ == "__main__":
    main()