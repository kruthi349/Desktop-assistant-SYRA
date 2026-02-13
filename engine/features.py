import os
import re
import sqlite3
import time
import json
from playsound import playsound
import eel
import pyaudio
import pyautogui
import pywhatkit as kit
import pvporcupine
import requests
from pipes import quote
import markdown2
from bs4 import BeautifulSoup
from engine.command import speak, takecommand
from engine.config import ASSISTANT_NAME, OPENWEATHERMAP_API_KEY
from engine.helper import extract_yt_term, markdown_to_text, remove_words
from hugchat import hugchat
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import struct
from rapidfuzz import process, fuzz

con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

@eel.expose
def playAssistantSound():
    """Play assistant sound"""
    music_dir = r"www\assets\audio\start_sound.mp3"
    playsound(music_dir)


def openCommand(query):
    """Open applications or websites"""
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "").lower().strip()
    
    if query:
        try:
            cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (query,))
            results = cursor.fetchall()
            
            if results:
                speak(f"Opening {query}")
                os.startfile(results[0][0])
            else:
                cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (query,))
                results = cursor.fetchall()
                
                if results:
                    speak(f"Opening {query}")
                    import webbrowser
                    webbrowser.open(results[0][0])
                else:
                    speak(f"Opening {query}")
                    try:
                        os.system(f'start {query}')
                    except:
                        speak("not found")
        except:
            speak("something went wrong")


def PlayYoutube(query):
    """Play video on YouTube"""
    search_term = extract_yt_term(query)
    speak(f"Playing {search_term} on YouTube")
    kit.playonyt(search_term)


def hotword():
    """Hotword detection using Porcupine"""
    porcupine = None
    paud = None
    audio_stream = None
    
    try:
        porcupine = pvporcupine.create(keywords=["syra"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)
            
            if keyword_index >= 0:
                print("hotword detected")
                import pyautogui as autogui
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
    except:
        if porcupine:
            porcupine.delete()
        if audio_stream:
            audio_stream.close()
        if paud:
            paud.terminate()


def findContact(query):
    """Find contact from database using fuzzy matching"""

    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'whatsapp', 'video']
    query = remove_words(query, words_to_remove).strip().lower()
    
    print("\n\n\nLOG from Function findContact (variable query):", query)

    # 1. Fetch all names from DB
    cursor.execute("SELECT name FROM contacts")
    all_names = [row[0] for row in cursor.fetchall()]
    # print("LOG from Function findContact (variable all_names):", all_names)
    
    if not all_names:
        speak("No contacts stored in your database.")
        return None, None

    # 2. Find best name match
    matched_name, score, _ = process.extractOne(query, all_names, scorer=fuzz.partial_ratio)
    print("LOG from Function findContact (variable matched_name, score):", matched_name, score)

    # 3. Ensure similarity is strong enough
    if score < 60:   # adjust if needed
        speak("I couldn't find a close match for that contact.")
        return None, None

    # 4. Now get the number of the matched contact
    cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name)=?", (matched_name.lower(),))
    result = cursor.fetchone()

    if not result:
        speak("Contact found by name but number is missing.")
        return None, None

    mobile_number = str(result[0])

    if not mobile_number.startswith("+91"):
        mobile_number = "+91" + mobile_number

    return mobile_number, matched_name


def whatsApp(mobile_no, message, flag, name):
    """Send WhatsApp message, call, or video call using WhatsApp Web"""
    import webbrowser
    import time
    from pipes import quote

    # Define message type
    if flag == 'message':
        jarvis_message = f"Message sent successfully to {name}"
    elif flag == 'call':
        message = ''
        jarvis_message = f"Calling {name} on WhatsApp"
    else:
        message = ''
        jarvis_message = f"Starting video call with {name} on WhatsApp"

    # Encode message for URL
    encoded_message = quote(message)

    # Build WhatsApp Web URL
    whatsapp_url = f"https://web.whatsapp.com/send?phone={mobile_no}&text={encoded_message}"

    # Open in default browser
    speak(f"Opening WhatsApp chat with {name}")
    webbrowser.open(whatsapp_url)
    time.sleep(5)  # wait a few seconds for WhatsApp Web to open

    speak(jarvis_message)


def chatBot(query):
    """Chat with HugChat"""
    user_input = query.lower()
    chatbot = hugchat.ChatBot(cookie_path=r"engine\cookies.json")
    id = chatbot.new_conversation()
    chatbot.change_conversation(id)
    response = chatbot.chat(user_input)
    print(response)
    return response


def makeCall(name, mobileNo):
    """Make phone call via ADB"""
    mobileNo = mobileNo.replace(" ", "")
    speak(f"Calling {name}")
    command = f'adb shell am start -a android.intent.action.CALL -d tel:{mobileNo}'
    os.system(command)


def sendMessage(message, mobileNo, name):
    """Send message via ADB"""
    from engine.helper import replace_spaces_with_percent_s, goback, keyEvent, tapEvents, adbInput
    
    message = replace_spaces_with_percent_s(message)
    mobileNo = replace_spaces_with_percent_s(mobileNo)
    
    speak("sending message")
    goback(4)
    time.sleep(1)
    keyEvent(3)
    tapEvents(136, 2220)
    tapEvents(819, 2192)
    adbInput(mobileNo)
    tapEvents(601, 574)
    tapEvents(390, 2270)
    adbInput(message)
    tapEvents(957, 1397)
    
    speak(f"message send successfully to {name}")


def get_weather(city: str) -> str:
    """Get current weather for a city"""
    if not OPENWEATHERMAP_API_KEY:
        return "Error: OpenWeatherMap API key not found"
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get("cod") != 200:
            return f"Error: Could not fetch weather for {city}"
        
        description = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        
        result = f"Weather in {city}: {description}, Temperature: {temp}°C, Humidity: {humidity}%"

        return result
    except Exception as e:
        return f"Error fetching weather: {str(e)}"


def geminai(query):
    """Query Gemini AI"""
    try:
        query = (
            query.replace(ASSISTANT_NAME, "")
            .replace("search", "")
            .strip()
        )

        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            max_output_tokens=512,
        )

        SYSTEM_COMMAND = (
            "You are Syra, a helpful and friendly personal assistant. "
            "Keep responses short unless asked, and avoid emojis."
        )

        messages = [
            SystemMessage(content=SYSTEM_COMMAND),
            HumanMessage(content=query)
        ]

        response = model.invoke(messages)
        text = response.content

        # Clean markdown
        clean = text.replace("*", "")

        return clean
    except Exception as e:
        print(f"Error: {e}")
        return str(e)

def googleSearch(query):
    import webbrowser
    import urllib.parse

    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)

def youtubeSearch(query):
    import webbrowser
    import urllib.parse

    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgIQAQ%253D%253D"
    webbrowser.open(url)

def spotifySearch(query):
    import webbrowser
    import urllib.parse

    encoded = urllib.parse.quote_plus(query)
    url = f"https://open.spotify.com/search/{encoded}"
    webbrowser.open(url)
    
def openGmailCompose(to, subject, body):
    import webbrowser
    import urllib.parse

    to_enc = urllib.parse.quote(to)
    subject_enc = urllib.parse.quote(subject)
    body_enc = urllib.parse.quote(body)

    url = (
        "https://mail.google.com/mail/?view=cm&fs=1"
        f"&to={to_enc}"
        f"&su={subject_enc}"
        f"&body={body_enc}"
    )

    webbrowser.open(url)

# Settings and Database Functions
@eel.expose
def assistantName():
    """Get assistant name"""
    return ASSISTANT_NAME


@eel.expose
def personalInfo():
    """Get personal info"""
    try:
        cursor.execute("SELECT * FROM info")
        results = cursor.fetchall()
        jsonArr = json.dumps(results[0])
        eel.getData(jsonArr)
        return 1
    except:
        print("no data")


@eel.expose
def updatePersonalInfo(name, designation, mobileno, email, city):
    """Update personal info"""
    cursor.execute("SELECT COUNT(*) FROM info")
    count = cursor.fetchone()[0]
    
    if count > 0:
        cursor.execute(
            'UPDATE info SET name=?, designation=?, mobileno=?, email=?, city=?',
            (name, designation, mobileno, email, city)
        )
    else:
        cursor.execute(
            'INSERT INTO info (name, designation, mobileno, email, city) VALUES (?, ?, ?, ?, ?)',
            (name, designation, mobileno, email, city)
        )
    
    con.commit()
    personalInfo()
    return 1


@eel.expose
def displaySysCommand():
    """Display system commands"""
    cursor.execute("SELECT * FROM sys_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displaySysCommand(jsonArr)
    return 1


@eel.expose
def deleteSysCommand(id):
    """Delete system command"""
    cursor.execute("DELETE FROM sys_command WHERE id = ?", (id,))
    con.commit()


@eel.expose
def addSysCommand(key, value):
    """Add system command"""
    cursor.execute('INSERT INTO sys_command VALUES (?, ?, ?)', (None, key, value))
    con.commit()


@eel.expose
def displayWebCommand():
    """Display web commands"""
    cursor.execute("SELECT * FROM web_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayWebCommand(jsonArr)
    return 1


@eel.expose
def addWebCommand(key, value):
    """Add web command"""
    cursor.execute('INSERT INTO web_command VALUES (?, ?, ?)', (None, key, value))
    con.commit()


@eel.expose
def deleteWebCommand(id):
    """Delete web command"""
    cursor.execute("DELETE FROM web_command WHERE Id = ?", (id,))
    con.commit()


@eel.expose
def displayPhoneBookCommand():
    """Display phone book"""
    cursor.execute("SELECT * FROM contacts")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayPhoneBookCommand(jsonArr)
    return 1


@eel.expose
def deletePhoneBookCommand(id):
    """Delete contact"""
    cursor.execute("DELETE FROM contacts WHERE Id = ?", (id,))
    con.commit()


@eel.expose
def InsertContacts(Name, MobileNo, Email, City):
    """Insert contact"""
    cursor.execute('INSERT INTO contacts VALUES (?, ?, ?, ?, ?)', (None, Name, MobileNo, Email, City))
    con.commit()
