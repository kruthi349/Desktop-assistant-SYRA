import os
import eel
import subprocess
from engine.features import playAssistantSound
from engine.command import speak
from engine.auth import recoganize  # Importing face authentication

def start():
    """Initialize and start Jarvis"""
    eel.init("www")
    playAssistantSound()
    
    @eel.expose
    def init():
        """Initialize face authentication"""
        try:
            subprocess.call([r'device.bat'])
        except:
            pass
        
        eel.hideLoader()
        speak("Ready for Face Authentication")
        
        # Using face authentication - unchanged as requested
        face_detected = recoganize.AuthenticateFace()
        flag = face_detected[0]
        
        if flag == 1:
            eel.hideFaceAuth()
            speak("Face Authentication Successful")
            eel.hideFaceAuthSuccess()
            speak(f"Hello, Welcome {face_detected[1]}, How can I help you")
            eel.hideStart()
            playAssistantSound()
        else:
            speak("Face Authentication Failed")
    
    os.system('start msedge.exe --app="http://localhost:8000/index.html"')
    eel.start('index.html', mode=None, host='localhost', block=True)


if __name__ == "__main__":
    start()
