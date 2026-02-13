import os
import re
import time
import markdown2
from bs4 import BeautifulSoup


def extract_yt_term(command):
    """Extract YouTube search term from command"""
    pattern = r'play\s+(.*?)\s+on\s+youtube'
    match = re.search(pattern, command, re.IGNORECASE)
    return match.group(1) if match else None


def remove_words(input_string, words_to_remove):
    """Remove unwanted words from string"""
    words = input_string.split()
    filtered_words = [word for word in words if word.lower() not in words_to_remove]
    return ' '.join(filtered_words)


def keyEvent(key_code):
    """Simulate key event via ADB"""
    command = f'adb shell input keyevent {key_code}'
    os.system(command)
    time.sleep(1)


def tapEvents(x, y):
    """Simulate tap event via ADB"""
    command = f'adb shell input tap {x} {y}'
    os.system(command)
    time.sleep(1)


def adbInput(message):
    """Insert text via ADB"""
    command = f'adb shell input text "{message}"'
    os.system(command)
    time.sleep(1)


def goback(key_code):
    """Go back multiple times"""
    for i in range(6):
        keyEvent(key_code)


def replace_spaces_with_percent_s(input_string):
    """Replace spaces with %s for message"""
    return input_string.replace(' ', '%s')


def markdown_to_text(md):
    """Convert markdown to plain text"""
    html = markdown2.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text().strip()