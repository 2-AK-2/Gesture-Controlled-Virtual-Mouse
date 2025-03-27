import speech_recognition as sr # type: ignore
import pyttsx3 # type: ignore
import datetime
import webbrowser

class SimplifiedAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.name = "assistant"

    def speak(self, text):
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(audio).lower()
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Sorry, I didn't catch that.")
                return ""
            except sr.RequestError:
                print("Sorry, my speech service is down.")
                return ""

    def wish(self):
        hour = datetime.datetime.now().hour
        if hour < 12:
            self.speak("Good morning!")
        elif hour < 18:
            self.speak("Good afternoon!")
        else:
            self.speak("Good evening!")
        self.speak("How can I help you?")

    def respond(self, text):
        if "hello" in text:
            self.speak("Hello! How can I assist you?")
        elif "time" in text:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
        elif "search" in text:
            search_query = text.split("search")[-1].strip()
            self.speak(f"Searching for {search_query}")
            url = f"https://www.google.com/search?q={search_query}"
            webbrowser.open(url)
        elif "bye" in text or "exit" in text:
            self.speak("Goodbye! Have a great day!")
            return False
        else:
            self.speak("I'm not sure how to help with that.")
        return True

    def run(self):
        self.wish()
        running = True
        while running:
            text = self.listen()
            if self.name in text:
                text = text.replace(self.name, "").strip()
                running = self.respond(text)

if __name__ == "__main__":
    assistant = SimplifiedAssistant()
    assistant.run()