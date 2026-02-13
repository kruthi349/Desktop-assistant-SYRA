import pyttsx3
import speech_recognition as sr
import eel
import time

def speak(text):
    """Text-to-speech function - Call ONCE per output"""
    text = str(text)
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 174)
    eel.DisplayMessage(text)
    engine.say(text)
    eel.receiverText(text)
    engine.runAndWait()

def takecommand():
    """Speech recognition function"""
    r = sr.Recognizer()
    while True:
        with sr.Microphone() as source:
            print('Listening...')
            eel.DisplayMessage('Listening...')
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source)
            try:
                audio = r.listen(source, timeout=10, phrase_time_limit=6)
            except sr.WaitTimeoutError:
                print("No speech detected. Retrying...")
                eel.DisplayMessage('No speech detected. Retrying...')
                continue
            try:
                print('Recognizing...')
                eel.DisplayMessage('Recognizing...')
                query = r.recognize_google(audio, language='en-in')
                print(f"User said: {query}")
                eel.DisplayMessage(query)
                time.sleep(1)
                return query.lower()
            except sr.UnknownValueError:
                print("Sorry, I didn't catch that.")
                eel.DisplayMessage("Sorry, I didn't catch that.")
                continue
            except sr.RequestError:
                print("Speech service unavailable.")
                eel.DisplayMessage("Speech service unavailable.")
                time.sleep(2)
                continue
            except Exception as e:
                print("Speech recognition error:", e)
                eel.DisplayMessage("Speech recognition error. Retrying...")
                continue

@eel.expose
def allCommands(message=1):
    """Main command dispatcher - CONTINUOUS LOOP FOR MULTIPLE COMMANDS"""
    try:
        from engine.agent import agent_executor

        # INFINITE LOOP: Keep listening and processing commands
        while True:
            try:
                # Get command from voice or message
                if message == 1:
                    query = takecommand()
                    print(f"Query: {query}")
                    eel.senderText(query)
                else:
                    query = message
                    eel.senderText(query)
                    message = 1 # Reset to voice mode for next iteration

                # IMPORTANT: Process command with agent
                if agent_executor and query:
                    print(f"Processing: {query}")
                    # Invoke agent with proper state
                    result = agent_executor.invoke({
                        "input": query,
                        "output": "",
                        "tool_results": {}
                    })
                    print(f"Agent Result: {result}")

                    # Check if result is valid
                    if result and isinstance(result, dict):
                        output = result.get("output", "")
                        
                        # ✓ IMPORTANT: Only speak ONCE per result
                        # Don't repeat output
                        if output and output != "Tool executed":
                            print(f"Speaking output: {output[:60]}...")
                            speak(output)
                        elif not output:
                            print("No output to speak")
                    else:
                        print("Result is not a valid dict")
                else:
                    if not agent_executor:
                        speak("Agent not initialized")
                        break

                # ✓ IMPORTANT: Return to main screen after command completes
                print("Command completed. Returning to main screen...")
                eel.DisplayMessage("Ready for next command...")
                # eel.hideListening()  # Hide listening UI
                eel.showMainScreen() # Show main screen
                
                # IMPORTANT: Reset for next command
                print("Ready for next command...")
                time.sleep(1) # Small delay before listening again

            except KeyboardInterrupt:
                print("\nExiting...")
                speak("Goodbye")
                break
            except Exception as e:
                print(f"Error in command loop: {e}")
                # ✓ IMPORTANT: Only speak error ONCE
                # speak(f"Error occurred")
                time.sleep(1)
                # Return to main screen on error
                # eel.hideListening()
                eel.showMainScreen()
                continue

    except Exception as e:
        print(f"Fatal command error: {e}")
        # speak("System error")
        eel.ShowHood()
