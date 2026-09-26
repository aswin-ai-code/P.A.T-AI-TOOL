import speech_recognition as sr
import pyttsx3


class PATVoice:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        

    def speak(self, text):
        print(f"P.A.T: {text}")

        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    
    def listen(self):
        with sr.Microphone() as source:
            print("🎤 Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio)
            print(f"You: {text}")
            return text

        except sr.UnknownValueError:
            print("❌ I couldn't understand.")
            return ""

        except sr.RequestError as error:
            print(f"❌ Speech service error: {error}")
            return ""


if __name__ == "__main__":
    pat = PATVoice()

    pat.speak("Hello! I am P.A.T. Voice system is ready.")

    text = pat.listen()

    if text:
        pat.speak(f"You said {text}")