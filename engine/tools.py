# tools.py - All Tool Definitions for the Agent

import os
import requests
import json
from datetime import datetime
from langchain_core.tools import Tool, tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from engine.config import (
    GEMINI_API_KEY, SERPER_API_KEY,
    ALPHA_VANTAGE_API_KEY, OPENWEATHERMAP_API_KEY,
    ASSISTANT_NAME
)
import wikipedia
from googlesearch import search as google_search
from yt_dlp import YoutubeDL
import pyautogui
import cv2
import threading
from pathlib import Path
import time
import urllib.parse
import webbrowser
import psutil
import platform
import re

# ==================== IMPORT DICTIONARY-BASED TASKS ====================
from engine.simple_tasks_dict import (
    add_task,
    get_current_date,
    get_current_date_time,
    get_today_tasks,
    get_tomorrow_tasks,
    get_tasks_for_date,
    get_tasks_by_date,
    get_upcoming_tasks,
    get_all_tasks,
    search_tasks,
    complete_task,
    delete_task
)

# ==================== TRY-EXCEPT IMPORTS FOR OPTIONAL LIBRARIES ====================
try:
    from screen_brightness_control import set_brightness, get_brightness
except ImportError:
    print("⚠️ screen_brightness_control not installed. Brightness control disabled on this platform.")
    set_brightness = None
    get_brightness = None

try:
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False
    print("⚠️ pycaw not available. Volume control limited.")

# ==================== TASK MANAGEMENT TOOLS (LLM-ACCESSIBLE) ====================

@tool
def fetch_tasks(time_filter: str = "today") -> str:
    """Fetch tasks from calendar/todo list.
    
    Args:
        time_filter: One of 'today', 'tomorrow', 'upcoming', or 'all'
    
    Returns: List of tasks for the specified time period
    """
    try:
        time_filter = time_filter.lower().strip()
        
        if time_filter == "today":
            return get_today_tasks()
        elif time_filter == "tomorrow":
            return get_tomorrow_tasks()
        elif time_filter in ["upcoming", "next"]:
            return get_upcoming_tasks()
        elif time_filter == "all":
            return get_all_tasks()
        else:
            return get_today_tasks()  # Default to today
    except Exception as e:
        return f"Error fetching tasks: {str(e)}"

@tool
def add_new_task(title: str, date: str = "today") -> str:
    """Add a new task to the todo list.
    
    Args:
        title: Task description/title
        date: When the task is due (default: 'today')
    
    Returns: Confirmation message
    """
    try:
        if not title or title.strip() == "":
            return "Error: Task title cannot be empty"
        return add_task(title.strip(), date)
    except Exception as e:
        return f"Error adding task: {str(e)}"

@tool
def complete_task_by_id(task_id: int) -> str:
    """Mark a task as completed.
    
    Args:
        task_id: The ID number of the task to complete
    
    Returns: Confirmation message
    """
    try:
        return complete_task(task_id)
    except Exception as e:
        return f"Error completing task: {str(e)}"

@tool
def delete_task_by_id(task_id: int) -> str:
    """Delete a task from the list.
    
    Args:
        task_id: The ID number of the task to delete
    
    Returns: Confirmation message
    """
    try:
        return delete_task(task_id)
    except Exception as e:
        return f"Error deleting task: {str(e)}"

@tool
def get_current_datetime() -> str:
    """Get the current date and time.
    
    Returns: Current date and time formatted as string
    """
    try:
        return get_current_date_time()
    except Exception as e:
        return f"Error getting date/time: {str(e)}"

# ==================== Define Tools ====================

def search_wrapper(search_query: str) -> str:
    """Wrapper to fix GoogleSerperAPIWrapper call"""
    try:
        search = GoogleSerperAPIWrapper(serpapi_api_key=SERPER_API_KEY)
        result = search.run(search_query)
        return str(result)
    except Exception as e:
        return f"Search error: {str(e)}"

search_tool = Tool(
    name="search",
    func=search_wrapper,
    description="Search online for information. Input: search query"
)

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city. Input: city name (e.g., 'Delhi', 'London')"""
    if not OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
        return "Weather API not configured. Please set OPENWEATHERMAP_API_KEY in config."
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("cod") != 200:
            return f"Could not fetch weather for {city}. Please check the city name."
        
        description = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        
        return f"Weather in {city}: {description}, Temperature: {temp}°C, Humidity: {humidity}%, Wind: {wind_speed} m/s"
    except Exception as e:
        return f"Weather error: {str(e)}"

@tool
def calculator(operation: str, num1: float, num2: float) -> str:
    """Perform arithmetic. Operations: 'add', 'subtract', 'multiply', 'divide', 'power'
    Example: operation='add', num1=5, num2=3 → Result: 8"""
    try:
        operation = operation.lower().strip()
        if operation == "add":
            result = num1 + num2
        elif operation == "subtract":
            result = num1 - num2
        elif operation == "multiply":
            result = num1 * num2
        elif operation == "divide":
            if num2 == 0:
                return "Error: Cannot divide by zero"
            result = num1 / num2
        elif operation == "power":
            result = num1 ** num2
        else:
            return f"Unknown operation. Supported: add, subtract, multiply, divide, power"
        
        return f"{num1} {operation} {num2} = {result}"
    except Exception as e:
        return f"Calculator error: {str(e)}"

@tool
def get_stock_price(symbol: str) -> str:
    """Get stock price for a symbol. Examples: 'AAPL', 'GOOGL', 'TSLA', 'INFY'
    Input: stock symbol (uppercase)"""
    try:
        if not ALPHA_VANTAGE_API_KEY or ALPHA_VANTAGE_API_KEY == "YOUR_ALPHA_VANTAGE_API_KEY":
            return "Stock API not configured. Using demo data only."
        
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "Global Quote" in data and data["Global Quote"] and data["Global Quote"].get("05. price"):
            quote = data["Global Quote"]
            price = quote.get("05. price", "N/A")
            change = quote.get("09. change", "N/A")
            change_percent = quote.get("10. change percent", "N/A")
            return f"Stock {symbol.upper()}: ${price} (Change: {change}, {change_percent})"
        else:
            return f"Could not find stock data for {symbol}. Try another symbol."
    except Exception as e:
        return f"Stock error: {str(e)}"

@tool
def open_application(app_name: str) -> str:
    """Open application or website. Examples: 'chrome', 'whatsapp', 'spotify', 'https://google.com'"""
    try:
        from engine.features import openCommand as open_cmd
        open_cmd(app_name)
        return f"✓ Opened {app_name} successfully"
    except Exception as e:
        return f"Error: Could not open {app_name}"

@tool
def play_youtube(query: str) -> str:
    """Play video/song on YouTube. Examples: 'Imagine Dragons', 'Python tutorial'"""
    try:
        from engine.features import PlayYoutube as play_yt
        play_yt(query)
        return f"▶️ Now playing '{query}' on YouTube"
    except Exception as e:
        return f"Error: Could not play on YouTube"

@tool
def find_contact(contact_name: str) -> str:
    """Find contact in database. Input: contact name
    Returns: contact name and phone number"""
    try:
        from engine.features import findContact as find_contact_func
        mobile_no, name = find_contact_func(contact_name)
        if mobile_no != 0:
            return f"Found: {name} - Phone: {mobile_no}"
        else:
            return f"Contact '{contact_name}' not found in database"
    except Exception as e:
        return f"Error finding contact: {str(e)}"

@tool
def make_call(contact_name: str) -> str:
    """Make phone call to contact. Input: contact name"""
    try:
        from engine.features import findContact as find_contact_func
        contact_no, found_name = find_contact_func(contact_name)
        if contact_no != 0:
            from engine.features import makeCall as make_call_func
            make_call_func(found_name, contact_no)
            return f"📞 Calling {found_name}..."
        else:
            return f"Contact '{contact_name}' not found"
    except Exception as e:
        return f"Error making call: {str(e)}"

@tool
def send_sms(contact_name: str, message: str) -> str:
    """Send SMS to contact.
    Input: contact_name and message
    Example: contact_name='Mom', message='Running late'"""
    try:
        from engine.features import findContact as find_contact_func
        contact_no, found_name = find_contact_func(contact_name)
        if contact_no != 0:
            from engine.features import sendMessage as send_msg_func
            send_msg_func(message, contact_no, found_name)
            return f"✓ SMS sent to {found_name}"
        else:
            return f"Contact '{contact_name}' not found"
    except Exception as e:
        return f"Error sending SMS: {str(e)}"

@tool
def send_whatsapp(contact_name: str, message: str = "") -> str:
    """Send WhatsApp message to contact.
    Input: contact_name and message
    Example: contact_name='Alice', message='Are you free?'"""
    try:
        from engine.features import findContact as find_contact_func
        contact_no, found_name = find_contact_func(contact_name)
        if contact_no:
            from engine.features import whatsApp as whatsapp_func
            whatsapp_func(contact_no, message, "message", found_name)
            return f"✓ WhatsApp messaged {found_name}"
        else:
            return f"Contact '{contact_name}' not found"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def chat_with_ai(query: str) -> str:
    """Chat with AI assistant for general questions and conversations"""
    try:
        from engine.features import chatBot as chat_bot_func
        response = chat_bot_func(query)
        # Note: extract_text_from_response is in agent.py, but for tool, return raw
        return str(response)
    except Exception as e:
        return f"Chat error: {str(e)}"

@tool
def query_gemini(prompt: str) -> str:
    """Query Gemini AI for detailed answers"""
    try:
        from engine.features import geminai as gemini_query_func
        response = gemini_query_func(prompt)
        # Note: extract_text_from_response is in agent.py, but for tool, return raw
        return str(response)
    except Exception as e:
        return f"Gemini error: {str(e)}"
    
@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information and summaries.
    
    Call this when user wants to:
    - Get Wikipedia info
    - Learn about a topic
    - Get definitions
    
    Args:
        query: Topic to search (e.g., 'Machine Learning')
    
    Returns: Wikipedia summary (first 3 sentences)
    
    Examples:
        "search machine learning on wikipedia"
        "find information about virat kohli"
        "what is artificial intelligence"
    """
    try:
        result = wikipedia.summary(query, sentences=3, auto_suggest=False)
        return f"📖 Wikipedia: {result}"
    except wikipedia.exceptions.DisambiguationError as e:
        suggestions = ", ".join(e.options[:3])
        return f"⚠️ Multiple matches found. Try: {suggestions}"
    except wikipedia.exceptions.PageError:
        return f"❌ No Wikipedia page found for '{query}'"
    except Exception as e:
        return f"❌ Wikipedia error: {str(e)}"


@tool
def search_google(query: str) -> str:
    """Open Google and search for information.
    
    Call this when user wants to:
    - Google search something
    - Find info online
    - Browse web results
    
    Args:
        query: Search term (e.g., 'best laptops 2024')
    
    Returns: Confirmation that Google search opened
    
    Examples:
        "google search best python tutorials"
        "search google for machine learning courses"
        "google how to learn react"
    """
    try:
        from engine.features import googleSearch as google_search_func
        google_search_func(query)
        return f"🔍 Searching Google for '{query}' in your browser"
    except Exception as e:
        return f"Google search error: {str(e)}"

@tool
def search_youtube(query: str) -> str:
    """Open YouTube and search for videos.
    
    Call this when user wants to:
    - Search YouTube
    - Play music/videos
    - Watch something
    
    Args:
        query: What to search (e.g., 'Kannada songs', 'Python tutorial')
    
    Returns: Confirmation message
    
    Examples:
        "search kannada songs on youtube"
        "play arijit singh on youtube"
        "youtube python tutorial"
    """
    try:
        # URL encode the query
        encoded = urllib.parse.quote_plus(query)
        
        # Build YouTube search URL with correct parameters
        url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgIQAQ%253D%253D"
        
        # Open in new tab (new=2 is safer than new=1 for new window)
        webbrowser.open(url, new=2)
        
        # Give browser time to open and register
        
        time.sleep(0.5)
        
        return f"🎥 Searching YouTube for '{query}' in your browser"
        
    except Exception as e:
        # More detailed error for debugging
        error_msg = str(e)
        return f"YouTube search error: {error_msg}. Please check if a default browser is set."

@tool
def get_system_stats() -> str:
    """Get comprehensive system resource statistics.
    
    Returns: CPU, RAM, Battery, Disk, Temperature stats
    
    Examples:
        "What's my system status?"
        "Show CPU usage"
        "Check my RAM"
    """
    try:
        stats = {
            "⚡ CPU Usage": f"{psutil.cpu_percent(interval=1)}%",
            "💾 RAM Usage": f"{psutil.virtual_memory().percent}%",
            "📦 RAM Available": f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
            "💿 Disk Usage": f"{psutil.disk_usage('/').percent}%",
        }
        
        # Battery info
        battery = psutil.sensors_battery()
        if battery:
            stats["🔋 Battery"] = f"{battery.percent}% - {'🔌 Plugged' if battery.power_plugged else '⚡ Discharging'}"
        
        # Temperature (if available)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                first_temp = list(temps.values())[0]
                stats["🌡️ CPU Temp"] = f"{first_temp.current}°C"
        except:
            pass
        
        # Format output
        output = "📊 System Status:\n"
        for key, value in stats.items():
            output += f"{key}: {value}\n"
        
        return output.strip()
    
    except Exception as e:
        return f"Error getting system stats: {str(e)}"


@tool
def get_cpu_usage() -> str:
    """Get detailed CPU usage information."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        return f"CPU Usage: {cpu_percent}% (Cores: {cpu_count})"
    except Exception as e:
        return f"CPU error: {str(e)}"


@tool
def get_ram_usage() -> str:
    """Get detailed RAM usage information."""
    try:
        mem = psutil.virtual_memory()
        return f"RAM Usage: {mem.percent}% ({mem.used / (1024**3):.2f}GB / {mem.total / (1024**3):.2f}GB)"
    except Exception as e:
        return f"RAM error: {str(e)}"


@tool
def get_battery_status() -> str:
    """Get battery status and health.
    
    Returns: Battery percentage, charging status, and estimated time remaining
    
    Examples:
        "What's my battery status?"
        "Check battery level"
        "Am I plugged in?"
    """
    try:
        import psutil
        
        # Get battery information
        battery = psutil.sensors_battery()
        
        # CRITICAL: Check if battery exists (None on desktop systems)
        if battery is None:
            return "⚠️ No battery found (Desktop system or battery not detected)"
        
        # Extract values with safety checks
        percent = battery.percent if hasattr(battery, 'percent') else 0
        is_plugged = battery.power_plugged if hasattr(battery, 'power_plugged') else False
        
        # Determine charging status
        status = "🔌 Plugged In (Charging)" if is_plugged else "⚡ Discharging"
        
        # Build remaining time string
        remaining_text = ""
        
        if hasattr(battery, 'secsleft') and battery.secsleft is not None:
            # Handle special values
            if battery.secsleft == psutil.POWER_TIME_UNLIMITED:
                # Plugged in, battery not discharging
                remaining_text = " (Plugged in - no discharge estimate)"
            elif battery.secsleft < 0:
                # Invalid/unavailable data
                remaining_text = ""
            elif battery.secsleft > 0:
                # Calculate hours and minutes
                total_seconds = int(battery.secsleft)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                
                if hours > 0:
                    remaining_text = f" (~{hours}h {minutes}m remaining)"
                else:
                    remaining_text = f" (~{minutes}m remaining)"
        
        # Build final output
        output = f"🔋 Battery: {percent}% - {status}{remaining_text}"
        
        # Add warning for low battery when discharging
        if percent < 20 and not is_plugged:
            output += " ⚠️ LOW BATTERY - PLUG IN SOON!"
        elif percent < 10:
            output += " 🚨 CRITICAL - PLUG IN IMMEDIATELY!"
        
        return output
        
    except AttributeError as ae:
        return f"⚠️ Battery attribute error: {str(ae)}. Battery info not fully available on this system."
    except Exception as e:
        return f"❌ Battery status error: {str(e)}"


@tool
def control_brightness(action: str, value: int = 0) -> str:
    """Control display brightness.
    
    Args:
        action: 'increase', 'decrease', 'set', 'get'
        value: Brightness level 0-100 (if action='set')
    
    Returns: Confirmation message
    
    Examples:
        "Increase brightness"
        "Set brightness to 80%"
        "Decrease brightness"
    """
    try:
        if get_brightness is None:
            return "Brightness control not available on this platform."
        
        current = get_brightness(display=0)
        
        if action == "increase":
            new_brightness = min(current + 10, 100)
            set_brightness(new_brightness, display=0)
            return f"✅ Brightness increased: {current}% → {new_brightness}%"
        
        elif action == "decrease":
            new_brightness = max(current - 10, 0)
            set_brightness(new_brightness, display=0)
            return f"✅ Brightness decreased: {current}% → {new_brightness}%"
        
        elif action == "set":
            value = max(0, min(value, 100))
            set_brightness(value, display=0)
            return f"✅ Brightness set to {value}%"
        
        elif action == "get":
            return f"Current brightness: {current}%"
        
        else:
            return "Invalid action. Use: 'increase', 'decrease', 'set', or 'get'"
    
    except Exception as e:
        return f"Brightness control error: {str(e)}"

@tool
def play_spotify(query: str) -> str:
    """
    Play/search music on Spotify (opens browser).
    
    Args:
        query: Song, artist, or album name.
        
    Examples:
        "Play Shape of You on Spotify"
        "Spotify search Taylor Swift"
    """
    try:
        from engine.features import spotifySearch as spotify_search_func
        spotify_search_func(query)
        return f"🎵 Playing '{query}' on Spotify"
    except Exception as e:
        return f"Spotify error: {str(e)}"

@tool
def control_volume(action: str, value: int = 0) -> str:
    """
    Control system volume using keyboard shortcuts.
    Works on all Windows systems without Pycaw.
    """
    import pyautogui
    import time

    action = action.lower().strip()

    if action == "increase":
        for _ in range(5):  # Increase 5 steps
            pyautogui.press("volumeup")
            time.sleep(0.05)
        return "🔊 Volume increased"
    
    elif action == "decrease":
        for _ in range(5):
            pyautogui.press("volumedown")
            time.sleep(0.05)
        return "🔉 Volume decreased"

    elif action == "mute":
        pyautogui.press("volumemute")
        return "🔇 System muted"

    elif action == "unmute":
        pyautogui.press("volumemute")  # toggle mute
        return "🔊 System unmuted"

    elif action == "set":
        # Normalize: set → mute → raise volume
        pyautogui.press("volumemute")
        time.sleep(0.1)

        steps = round(value / 2)  # rough mapping
        for _ in range(steps):
            pyautogui.press("volumeup")
            time.sleep(0.05)

        return f"🔊 Volume set to ~{value}% (approx.)"

    return "Unknown command"

@tool
def take_screenshot(save_location: str = "") -> str:
    """
    Windows-10 stable screenshot tool using mss (NOT pyautogui).
    Saves screenshots inside ./screenshots unless a custom folder is given.
    """

    try:
        import mss
        import mss.tools

        # Default folder → ./screenshots
        if not save_location:
            save_location = Path.cwd() / "screenshots"
        else:
            save_location = Path(save_location)

        save_location.mkdir(parents=True, exist_ok=True)

        # File name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = save_location / f"screenshot_{timestamp}.png"

        # Capture full screen using mss (most stable on Windows)
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filename))

        return f"📸 Screenshot saved: {filename}"

    except Exception as e:
        return f"❌ Screenshot error: {str(e)}"


@tool
def send_email(to: str, message_summary: str) -> str:
    """
    Open Gmail in browser with a pre-filled email (recipient, subject, body).
    The LLM automatically generates the subject and body.
    """

    try:
        from engine.features import openGmailCompose as gmail_func
        from engine.config import GEMINI_API_KEY
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Local LLM client (this is allowed inside tools)
        local_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=GEMINI_API_KEY,
            temperature=0.6
        )

        # Ask LLM to prepare the email
        email_prompt = f"""
Write a professional email.

Recipient: {to}
Purpose summary: "{message_summary}"

Return in this format:
Subject: <your subject>
Body:
<your email body>
"""

        response = local_llm.invoke(email_prompt)
        email_text = response.content if hasattr(response, "content") else str(response)

        # Extract subject & body
        lines = email_text.split("\n")
        subject = ""
        body_lines = []

        for line in lines:
            if line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
            else:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()

        # Now open Gmail
        gmail_func(to, subject, body)

        return f"📧 Opening Gmail to email {to}"

    except Exception as e:
        return f"Email error: {str(e)}"

@tool
def create_folder(folder_name: str) -> str:
    """
    Create a folder inside the current working directory.
    If folder exists → returns a message without error.
    
    Args:
        folder_name: Name of the folder to create.
    """
    try:
        folder_path = Path.cwd() / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        return f"📁 Folder created at: {folder_path}"
    except Exception as e:
        return f"❌ Error creating folder: {str(e)}"

@tool
def delete_folder(folder_name: str) -> str:
    """
    Delete a folder inside the current working directory.
    Only deletes if folder is empty (safety).
    
    Args:
        folder_name: Name of the folder to delete.
    """
    try:
        folder_path = Path.cwd() / folder_name
        
        if not folder_path.exists():
            return "⚠️ Folder does not exist."
        
        if any(folder_path.iterdir()):
            return "❌ Folder is not empty. Cannot delete for safety."
        
        folder_path.rmdir()
        return f"🗑️ Folder '{folder_name}' deleted successfully."
    except Exception as e:
        return f"❌ Error deleting folder: {str(e)}"

@tool
def create_file(instruction: str) -> str:
    """
    Universal file generator.
    - Creates ANY file type: code, text, markdown, JSON, notes.
    - Saves into ./codebase
    - If user provides a filename → use it
    - If no extension is provided → use .txt
    - LLM must return EXTENSION + CONTENT (but the agent should NOT pass content)

    Args:
        instruction: Description of what file to create.
    """
    try:
        from engine.config import GEMINI_API_KEY
        from langchain_google_genai import ChatGoogleGenerativeAI

        codebase_dir = Path.cwd() / "codebase"
        codebase_dir.mkdir(exist_ok=True)

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=GEMINI_API_KEY,
            temperature=0.5
        )

        # Detect filename if user gave one (e.g. hello.txt)
        filename_match = re.search(r"\b([\w\-]+\.\w+)\b", instruction)
        user_filename = filename_match.group(1) if filename_match else None

        # LLM prompt
        prompt = f"""
You must generate a file.

User instruction:
\"\"\"{instruction}\"\"\"

Respond ONLY in this format:
EXTENSION: .ext
CONTENT:
<file content here>

Rules:
- EXTENSION must start with a dot (e.g., .py, .txt, .md, .json)
- Do NOT wrap content inside code blocks
- Do NOT add commentary
"""

        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)

        # ============================
        #     CLEAN PARSING LOGIC
        # ============================
        # Remove markdown code fences if present
        text = text.replace("```", "").strip()

        extension = None
        content = ""

        lines = text.splitlines()
        reading_content = False

        for line in lines:
            # EXTENSION detection
            if line.strip().lower().startswith("extension"):
                ext_value = line.split(":", 1)[1].strip()
                extension = ext_value if ext_value.startswith(".") else f".{ext_value}"
                continue

            # CONTENT detection
            if line.strip().lower().startswith("content"):
                reading_content = True
                continue

            if reading_content:
                content += line + "\n"

        if not extension:
            extension = ".txt"

        content = content.strip()

        # ============================
        # Create filename
        # ============================

        if user_filename:
            if not user_filename.endswith(extension):
                base = user_filename.rsplit(".", 1)[0]
                filename = f"{base}{extension}"
            else:
                filename = user_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_file_{timestamp}{extension}"

        filepath = codebase_dir / filename

        # ============================
        # Save file
        # ============================
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return f"✅ File created successfully: {filepath}"

    except Exception as e:
        print(e)
        return f"❌ Error creating file: {str(e)}"

# ==================== Export All Tools ====================
all_tools = [
    # ===== TASK MANAGEMENT =====
    fetch_tasks,
    add_new_task,
    complete_task_by_id,
    delete_task_by_id,
    get_current_datetime,
    
    # ===== COMMUNICATION =====
    send_whatsapp,
    send_sms,
    make_call,
    find_contact,
    send_email,
    
    # ===== WEB & SEARCH =====
    search_wikipedia,      # ← Wikipedia search
    search_google,         # ← Google search
    search_youtube,        # ← YouTube search
    
    # ===== BROWSER/APPS =====
    open_application,
    play_spotify,
    
    # ===== INFORMATION =====
    get_weather,
    get_stock_price,
    calculator,
    chat_with_ai,
    query_gemini,
    search_tool,           # General search tool
    
    # ===== SYSTEM CONTROL =====
    control_volume,
    control_brightness,
    take_screenshot,
    
    # ===== SYSTEM INFO =====
    get_battery_status,
    get_ram_usage,
    get_cpu_usage,
    get_system_stats,
    
    # ===== FILE & CODE MANAGEMENT =====
    create_folder,
    delete_folder,
    create_file,
]