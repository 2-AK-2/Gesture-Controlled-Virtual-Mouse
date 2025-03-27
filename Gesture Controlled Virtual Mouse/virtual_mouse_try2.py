import pyttsx3 
import speech_recognition as sr 
from datetime import date
import time
import webbrowser
import datetime
from pynput.keyboard import Key, Controller 
import pyautogui 
import sys
import os
from os import listdir, startfile
from os.path import isfile, join
import smtplib
import wikipediaapi
import cv2 
import eel 
from queue import Queue
from threading import Thread

# -------------------Object Initialization------------------------
today = date.today()
r = sr.Recognizer()
keyboard = Controller()
engine = pyttsx3.init('sapi5')
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
pyautogui.FAILSAFE = False

# -----------------Variables-----------------------
file_exp_status = False
files = []
path = ''
is_awake = True  # Bot status

# ------------------Gesture Control Classes-----------------------
class Marker:
    # Marker class methods will go here (not fully implemented for brevity)
    pass

class ROI:
    # ROI class methods for tracking ROI of hand
    pass

class Glove:
    # Glove class that detects the glove gesture
    gesture = None
    
    def find_fingers(self, FinalMask):
        # Code for finger detection goes here
        pass
    
    def find_gesture(self, frame):
        # Code to interpret the gesture from the finger detection
        pass

class Tracker:
    tracker_started = False
    tracker_bbox = None
    now_time = time.time()
    start_time = time.time()

    def CSRT_tracker(self, frame):
        ok = True  # Simulation, will depend on tracking logic
        if self.tracker_bbox:
            p1 = (int(self.tracker_bbox[0]), int(self.tracker_bbox[1]))
            p2 = (int(self.tracker_bbox[0] + self.tracker_bbox[2]), int(self.tracker_bbox[1] + self.tracker_bbox[3]))
            cv2.rectangle(frame, p1, p2, (80, 255, 255), 2, 1)

class Mouse:
    def __init__(self):
        self.tx_old = 0
        self.ty_old = 0
        self.trial = True
        self.flag = 0

    def move_mouse(self, frame, position, gesture):
        (sx, sy) = pyautogui.size()
        (camx, camy) = (frame.shape[:2][0], frame.shape[:2][1])
        (mx_old, my_old) = pyautogui.position()

        Damping = 2  # Adjustable hyperparameter
        tx, ty = position
        if self.trial:
            self.trial, self.tx_old, self.ty_old = False, tx, ty

        delta_tx = tx - self.tx_old
        delta_ty = ty - self.ty_old
        self.tx_old, self.ty_old = tx, ty

        if gesture == 3:
            self.flag = 0
            mx = mx_old + (delta_tx * sx) // (camx * Damping)
            my = my_old + (delta_ty * sy) // (camy * Damping)
            pyautogui.moveTo(mx, my, duration=0.1)
        elif gesture == 0:
            if self.flag == 0:
                pyautogui.doubleClick()
                self.flag = 1

class GestureController:
    gc_mode = 0
    aru_marker = Marker()
    hand_roi = ROI()
    glove = Glove()
    csrt_track = Tracker()
    mouse = Mouse()

    def __init__(self):
        GestureController.cap = cv2.VideoCapture(0)
        GestureController.gc_mode = 1

    def start(self):
        while GestureController.gc_mode:
            ret, frame = GestureController.cap.read()
            frame = cv2.flip(frame, 1)

            self.csrt_track.CSRT_tracker(frame)
            # Detection logic, gesture recognition, mouse movement logic

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        GestureController.cap.release()
        cv2.destroyAllWindows()

# -------------------Chatbot with Gesture Control-----------------
class ChatBot:
    started = False
    userinputQueue = Queue()

    def isUserInput():
        return not ChatBot.userinputQueue.empty()

    def popUserInput():
        return ChatBot.userinputQueue.get()

    def close_callback(route, websockets):
        exit()

    @eel.expose
    def getUserInput(msg):
        ChatBot.userinputQueue.put(msg)

    def close():
        ChatBot.started = False

    def addUserMsg(msg):
        eel.addUserMsg(msg)

    def addAppMsg(msg):
        eel.addAppMsg(msg)

    def start():
        path = os.path.dirname(os.path.abspath(__file__))
        eel.init(path + r'\web', allowed_extensions=['.js', '.html'])
        try:
            eel.start('index.html', mode='chrome',
                      host='localhost', port=27005, block=False,
                      size=(350, 480), position=(10, 100),
                      disable_cache=True, close_callback=ChatBot.close_callback)
            ChatBot.started = True
            while ChatBot.started:
                eel.sleep(10.0)
        except:
            pass

# ----------------Voice Assistant Functions-----------------------
def reply(audio):
    ChatBot.addAppMsg(audio)
    engine.say(audio)
    engine.runAndWait()

def wish():
    hour = int(datetime.datetime.now().hour)
    if hour < 12:
        reply("Good Morning!")
    elif hour < 18:
        reply("Good Afternoon!")
    else:
        reply("Good Evening!")
    reply("I am Proton, how may I help you?")

def record_audio():
    with sr.Microphone() as source:
        r.pause_threshold = 0.8
        voice_data = ''
        audio = r.listen(source, phrase_time_limit=5)
        try:
            voice_data = r.recognize_google(audio)
        except sr.RequestError:
            reply('Sorry, my service is down. Please check your internet connection.')
        except sr.UnknownValueError:
            pass
        return voice_data.lower()

def respond(voice_data):
    global file_exp_status, files, path, is_awake
    voice_data = voice_data.replace('proton', '')
    ChatBot.addUserMsg(voice_data)

    if 'hello' in voice_data:
        wish()

    elif 'search' in voice_data:
        reply('Searching for ' + voice_data.split('search')[1])
        url = 'https://google.com/search?q=' + voice_data.split('search')[1]
        try:
            webbrowser.get().open(url)
            reply('Here is what I found.')
        except:
            reply('Please check your internet connection.')

    elif 'launch gesture recognition' in voice_data:
        if GestureController.gc_mode:
            reply('Gesture recognition is already active.')
        else:
            gc = GestureController()
            t = Thread(target=gc.start)
            t.start()
            reply('Gesture recognition launched successfully.')

    elif 'stop gesture recognition' in voice_data:
        if GestureController.gc_mode:
            GestureController.gc_mode = 0
            reply('Gesture recognition stopped.')
        else:
            reply('Gesture recognition is already inactive.')

# ----------------------Driver Code-------------------------------
t1 = Thread(target=ChatBot.start)
t1.start()

while not ChatBot.started:
    time.sleep(0.5)

wish()

while True:
    voice_data = record_audio()
    if 'proton' in voice_data:
        try:
            respond(voice_data)
        except SystemExit:
            reply("Exiting.")
            break
        except Exception as e:
            print(f"Error: {e}")
            break
