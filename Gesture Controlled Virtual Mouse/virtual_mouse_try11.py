import cv2  # type: ignore
import mediapipe as mp  # type: ignore
import pyautogui  # type: ignore
import numpy as np  # type: ignore
import speech_recognition as sr  # type: ignore
import threading
import time
from pynput import keyboard  # type: ignore
import math
from collections import deque
import tkinter as tk
from tkinter import ttk
import json
import os

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# Global variables
config = {
    "is_active": True,
    "show_landmarks": True,
    "smoothing": 5,
    "scroll_speed": 2,
    "double_click_time": 0.3,
    "swipe_threshold": 0.3,
    "drag_threshold": 1.0,
    "zoom_sensitivity": 2.0,
    "brightness_sensitivity": 5,
    "volume_sensitivity": 2,
    "current_mode": "MOUSE"
}

prev_x, prev_y = 0, 0
last_tap_time = 0
last_scroll_y = None
last_click_time = 0
gesture_history = deque(maxlen=50)

# Custom gesture definitions
custom_gestures = {
    'M': lambda: os.system('start wmplayer'),
    'C': lambda: os.system('start chrome'),
}

MODES = ['MOUSE', 'SCROLL', 'GESTURE']

# Initialize speech recognition
recognizer = sr.Recognizer()
microphone = sr.Microphone()

def save_config():
    with open('gesture_config.json', 'w') as f:
        json.dump(config, f)

def load_config():
    global config
    try:
        with open('gesture_config.json', 'r') as f:
            config.update(json.load(f))
    except FileNotFoundError:
        save_config()

def get_hand_landmarks(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    return results.multi_hand_landmarks

def calculate_distance(p1, p2):
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5

def is_click_gesture(landmarks, finger1, finger2):
    return calculate_distance(landmarks[finger1], landmarks[finger2]) < 0.05

def is_hand_closed(landmarks):
    return all(calculate_distance(landmarks[i], landmarks[0]) < 0.1 for i in range(1, 5))

def is_hand_open(landmarks):
    return all(calculate_distance(landmarks[i], landmarks[0]) > 0.15 for i in range(1, 5))

def move_cursor(landmarks):
    global prev_x, prev_y
    index_tip = landmarks[8]

    x = int(index_tip.x * SCREEN_WIDTH)
    y = int(index_tip.y * SCREEN_HEIGHT)

    speed = ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
    speed_factor = min(speed / 10, 5)

    smooth_x = prev_x + (x - prev_x) / config['smoothing'] * speed_factor
    smooth_y = prev_y + (y - prev_y) / config['smoothing'] * speed_factor

    pyautogui.moveTo(smooth_x, smooth_y)
    prev_x, prev_y = smooth_x, smooth_y

def handle_scroll(landmarks):
    global last_scroll_y
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    
    if last_scroll_y is None:
        last_scroll_y = thumb_tip.y
    
    # Calculate the distance between thumb and index finger
    distance = calculate_distance(thumb_tip, index_tip)
    
    # Use the vertical movement of the hand for scrolling
    delta_y = thumb_tip.y - last_scroll_y
    
    # Adjust scroll speed based on the pinch distance
    scroll_multiplier = 1 - min(distance * 2, 0.9)  # Closer pinch = faster scroll
    
    scroll_amount = int(delta_y * SCREEN_HEIGHT * config['scroll_speed'] * scroll_multiplier)
    
    if abs(scroll_amount) > 5:
        pyautogui.scroll(-scroll_amount)
    
    last_scroll_y = thumb_tip.y

def handle_zoom(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    distance = calculate_distance(thumb_tip, index_tip)
    
    if distance > 0.1:
        pyautogui.hotkey('ctrl', '+')
    elif distance < 0.05:
        pyautogui.hotkey('ctrl', '-')

def handle_brightness(landmarks):
    global prev_y
    current_y = landmarks[8].y
    if prev_y:
        delta_y = current_y - prev_y
        if abs(delta_y) > 0.01:
            change = int(delta_y * config['brightness_sensitivity'])
            # Use appropriate API calls to change brightness
            print(f"Changing brightness by {change}")
    prev_y = current_y

def handle_volume(landmarks):
    center_x = (landmarks[4].x + landmarks[8].x) / 2
    center_y = (landmarks[4].y + landmarks[8].y) / 2
    angle = math.atan2(center_y - 0.5, center_x - 0.5)
    volume_change = int(angle * config['volume_sensitivity'])
    # Use appropriate API calls to change volume
    print(f"Changing volume by {volume_change}")

def recognize_custom_gesture(landmarks):
    gesture_history.append((landmarks[8].x, landmarks[8].y))
    if len(gesture_history) == 50:
        for gesture, action in custom_gestures.items():
            if gesture == 'M':  # Example: Check if gesture forms an 'M'
                action()

def handle_voice_commands():
    while True:
        print("Listening for commands...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")
            if "scroll up" in command:
                pyautogui.scroll(200)
            elif "scroll down" in command:
                pyautogui.scroll(-200)
            elif "volume up" in command:
                pyautogui.press("volumeup")
            elif "volume down" in command:
                pyautogui.press("volumedown")
            elif "mute" in command:
                pyautogui.press("volumemute")
            elif "switch window" in command:
                pyautogui.hotkey("alt", "tab")
            elif "open browser" in command:
                pyautogui.hotkey("win", "r")
                time.sleep(0.5)
                pyautogui.write("chrome")
                pyautogui.press("enter")
            elif "sleep" in command:
                print("Putting computer to sleep")
                # Implement sleep functionality
            elif "wake" in command:
                print("Waking up computer")
                # Implement wake functionality
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from speech recognition service; {e}")

def on_press(key):
    global config
    if key == keyboard.Key.f1:
        config['is_active'] = not config['is_active']
        print(f"Gesture control {'activated' if config['is_active'] else 'deactivated'}")
    elif key == keyboard.Key.f2:
        config['show_landmarks'] = not config['show_landmarks']
        print(f"Landmark visualization {'enabled' if config['show_landmarks'] else 'disabled'}")
    elif key == keyboard.Key.f3:
        config['current_mode'] = MODES[(MODES.index(config['current_mode']) + 1) % len(MODES)]
        print(f"Switched to {config['current_mode']} mode")
    save_config()

def create_settings_ui():
    def update_config():
        for key, var in config_vars.items():
            config[key] = var.get()
        save_config()
        settings_window.destroy()

    settings_window = tk.Tk()
    settings_window.title("Gesture Control Settings")

    config_vars = {}
    for key, value in config.items():
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            ttk.Checkbutton(settings_window, text=key, variable=var).pack()
        elif isinstance(value, (int, float)):
            var = tk.DoubleVar(value=value)
            ttk.Label(settings_window, text=key).pack()
            ttk.Scale(settings_window, from_=0, to=10, variable=var, orient=tk.HORIZONTAL).pack()
        elif isinstance(value, str):
            var = tk.StringVar(value=value)
            ttk.Label(settings_window, text=key).pack()
            ttk.Combobox(settings_window, textvariable=var, values=MODES).pack()
        config_vars[key] = var

    ttk.Button(settings_window, text="Save", command=update_config).pack()
    settings_window.mainloop()

# Load configuration
load_config()

# Start voice command thread
voice_thread = threading.Thread(target=handle_voice_commands, daemon=True)
voice_thread.start()

# Start keyboard listener
keyboard_listener = keyboard.Listener(on_press=on_press)
keyboard_listener.start()

# Main loop
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    hand_landmarks = get_hand_landmarks(frame)

    if hand_landmarks and config['is_active']:
        for landmarks in hand_landmarks:
            if config['show_landmarks']:
                mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

            if config['current_mode'] == 'MOUSE':
                move_cursor(landmarks.landmark)
                if is_click_gesture(landmarks.landmark, 4, 8):
                    current_time = time.time()
                    if current_time - last_click_time < config['double_click_time']:
                        pyautogui.doubleClick()
                        last_click_time = 0
                    else:
                        pyautogui.click()
                        last_click_time = current_time
                    time.sleep(0.2)
                elif is_click_gesture(landmarks.landmark, 4, 12):
                    pyautogui.click(button="right")
                    time.sleep(0.2)
            elif config['current_mode'] == 'SCROLL':
                handle_scroll(landmarks.landmark)
            elif config['current_mode'] == 'GESTURE':
                recognize_custom_gesture(landmarks.landmark)

            if is_hand_open(landmarks.landmark):
                handle_zoom(landmarks.landmark)
            elif is_hand_closed(landmarks.landmark):
                handle_brightness(landmarks.landmark)

    # Display status information
    cv2.putText(
        frame,
        f"Mode: {config['current_mode']} | Active: {'Yes' if config['is_active'] else 'No'}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0) if config['is_active'] else (0, 0, 255),
        2,
    )
    cv2.putText(
        frame,
        f"Landmarks: {'On' if config['show_landmarks'] else 'Off'} | F1: Toggle | F2: Landmarks | F3: Mode",
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.imshow("Gesture Control", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break
    elif key == ord('s'):
        create_settings_ui()

cap.release()
cv2.destroyAllWindows()
keyboard_listener.stop()