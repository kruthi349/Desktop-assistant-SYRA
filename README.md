🧠 SYRA – AI Powered Desktop Voice Assistant
SYRA is an intelligent, AI-powered desktop voice assistant designed to simplify human–computer interaction using natural language voice commands. It combines Large Language Models (LLMs), automation tools, and system-level integrations to perform real-time actions on a computer.

🚀 Overview
SYRA transforms a traditional desktop system into a smart assistant capable of:

Understanding natural language commands

Executing system-level operations

Performing web searches and API calls

Managing tasks and reminders

Sending messages and controlling applications

Authenticating users using face recognition

It bridges the gap between artificial intelligence and real-world desktop automation.

🎯 Problem Statement
Modern computer systems still rely heavily on manual input such as typing and clicking. This limits productivity, especially during multitasking.

Existing assistants:

Have limited system-level control

Lack customization

Do not integrate deeply with desktop environments

SYRA solves this by providing intelligent, voice-driven automation with AI decision-making.

✨ Key Features
🔊 Voice Interaction
Speech-to-text command recognition

Text-to-speech intelligent responses

Continuous command listening

🤖 AI Agent-Based Decision Making
Uses LLM (Gemini) for natural language understanding

Automatically selects appropriate tools

Generates human-like summarized responses

🛠 System Automation
Open applications

Control brightness and volume

Take screenshots

Fetch system statistics (CPU, RAM, battery)

🌐 Web & API Integration
Google search

Wikipedia search

YouTube search & playback

Weather updates

Stock market data

📱 Communication
WhatsApp messaging

SMS and calling via ADB

Email automation

📝 Task Management
Add tasks

View tasks by date

Complete or delete tasks

👁 Face Recognition Module
Face dataset generation

Face embedding creation using FaceNet

Real-time authentication using cosine similarity

Optional CNN-based classifier

🏗 System Architecture
SYRA follows a layered architecture:

Voice Input Layer

SpeechRecognition for capturing user commands

AI Agent Layer

Gemini LLM for intent detection

LangChain + LangGraph for agent workflow

Tool selection and execution

Tool Execution Layer

Python-based automation functions

System controls and API integrations

Database Layer

SQLite for contacts, commands, and user data

Response Layer

Output summarization

Voice response via pyttsx3

Computer Vision Layer (Optional)

OpenCV + FaceNet for authentication

🧩 Core Technologies
Python – Core implementation

Gemini (LLM) – Natural language understanding

LangChain – Tool integration framework

LangGraph – Agent workflow orchestration

SpeechRecognition – Voice input

pyttsx3 – Voice output

OpenCV + FaceNet + MTCNN – Face recognition

SQLite – Local database

External APIs – Weather, Google, YouTube, Stock

⚙️ How It Works
User gives a voice command.

Speech is converted to text.

The AI Agent analyzes intent using Gemini.

LangGraph selects the appropriate tool.

Tool executes the requested action.

Result is summarized.

Assistant responds via voice output.

📊 Results & Achievements
40+ integrated automation tools

Real-time system control

API-based information retrieval

Face authentication system implemented

Modular and scalable architecture

🔮 Future Scope
Mobile and IoT integration

Voice biometric authentication

Emotion detection

Offline LLM deployment

Personalized user profiles

Cloud-based synchronization


