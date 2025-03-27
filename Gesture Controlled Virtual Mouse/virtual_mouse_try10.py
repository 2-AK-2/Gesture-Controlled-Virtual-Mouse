import cv2 
import mediapipe as mp 
import pyautogui  
import numpy as np  
import speech_recognition as sr 
import threading
import time
from pynput import keyboard  
import math
from collections import deque
import pickle
import os

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)

# Initialize speech recognition
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# Smoothing factor for cursor movement
SMOOTHING = 5
prev_x, prev_y = 0, 0

# Global variables
is_active = True
show_landmarks = True
scroll_mode = False
prev_scroll_y = 0
last_tap_time = 0
last_scroll_y = None
scroll_speed = 2
last_click_time = 0
DOUBLE_CLICK_TIME = 0.3
SWIPE_THRESHOLD = 0.3
DRAG_THRESHOLD = 1.0  # Time in seconds to hold for drag
ZOOM_SENSITIVITY = 2.0
BRIGHTNESS_SENSITIVITY = 5
VOLUME_SENSITIVITY = 2

# Gesture history for custom gesture recognition
gesture_history = deque(maxlen=50)

# Custom gesture definitions (example)
custom_gestures = {
    'M': lambda: os.system('start wmplayer'),  # Launch Windows Media Player
    'C': lambda: os.system('start chrome'),   # Launch Chrome
}

# Mode switching
MODES = ['MOUSE', 'SCROLL', 'GESTURE']
current_mode = 'MOUSE'

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

def is_scroll_gesture(landmarks):
    return landmarks[8].y < landmarks[7].y and landmarks[12].y > landmarks[11].y

def is_pinch_gesture(landmarks):
    return calculate_distance(landmarks[4], landmarks[8]) < 0.05

def move_cursor(landmarks):
    global prev_x, prev_y
    index_tip = landmarks[8]

    x = int(index_tip.x * SCREEN_WIDTH)
    y = int(index_tip.y * SCREEN_HEIGHT)

    speed = ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
    speed_factor = min(speed / 10, 5)

    smooth_x = prev_x + (x - prev_x) / SMOOTHING * speed_factor
    smooth_y = prev_y + (y - prev_y) / SMOOTHING * speed_factor

    pyautogui.moveTo(smooth_x, smooth_y)
    prev_x, prev_y = smooth_x, smooth_y

def handle_scroll(landmarks):
    global last_scroll_y
    current_y = landmarks[8].y

    if last_scroll_y is not None:
        delta_y = current_y - last_scroll_y
        scroll_amount = int(delta_y * SCREEN_HEIGHT * scroll_speed)

        if abs(scroll_amount) > 5:
            pyautogui.scroll(-scroll_amount)

    last_scroll_y = current_y

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
            change = int(delta_y * BRIGHTNESS_SENSITIVITY)
            # Use appropriate API calls to change brightness
            # This is a placeholder and needs to be implemented based on the OS
            print(f"Changing brightness by {change}")
    prev_y = current_y

def handle_volume(landmarks):
    center_x = (landmarks[4].x + landmarks[8].x) / 2
    center_y = (landmarks[4].y + landmarks[8].y) / 2
    angle = math.atan2(center_y - 0.5, center_x - 0.5)
    volume_change = int(angle * VOLUME_SENSITIVITY)
    # Use appropriate API calls to change volume
    # This is a placeholder and needs to be implemented based on the OS
    print(f"Changing volume by {volume_change}")

def recognize_custom_gesture(landmarks):
    # Simplified custom gesture recognition
    # In a real implementation, this would use more sophisticated pattern matching
    gesture_history.append((landmarks[8].x, landmarks[8].y))
    if len(gesture_history) == 50:
        # Check if the gesture matches any predefined patterns
        for gesture, action in custom_gestures.items():
            if gesture == 'M':  # Example: Check if gesture forms an 'M'
                action()

def handle_voice_commands():
    while True:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
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
                # Implement sleep functionality
                print("Putting computer to sleep")
            elif "wake" in command:
                # Implement wake functionality
                print("Waking up computer")
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            print("Could not request results from speech recognition service")

def on_press(key):
    global is_active, show_landmarks, scroll_mode, current_mode
    if key == keyboard.Key.f1:
        is_active = not is_active
        print(f"Gesture control {'activated' if is_active else 'deactivated'}")
    elif key == keyboard.Key.f2:
        show_landmarks = not show_landmarks
        print(f"Landmark visualization {'enabled' if show_landmarks else 'disabled'}")
    elif key == keyboard.Key.f3:
        current_mode = MODES[(MODES.index(current_mode) + 1) % len(MODES)]
        print(f"Switched to {current_mode} mode")

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

    if hand_landmarks and is_active:
        for i, landmarks in enumerate(hand_landmarks):
            if show_landmarks:
                mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

            is_right_hand = landmarks.landmark[4].x < landmarks.landmark[20].x

            if current_mode == 'MOUSE':
                if is_right_hand:
                    move_cursor(landmarks.landmark)

                    if is_click_gesture(landmarks.landmark, 4, 8):
                        current_time = time.time()
                        if current_time - last_click_time < DOUBLE_CLICK_TIME:
                            pyautogui.doubleClick()
                            last_click_time = 0
                        else:
                            pyautogui.click()
                            last_click_time = current_time
                        time.sleep(0.2)
                    elif is_click_gesture(landmarks.landmark, 4, 12):
                        pyautogui.click(button="right")
                        time.sleep(0.2)
                    elif is_hand_closed(landmarks.landmark):
                        pyautogui.hotkey("alt", "f4")
                        time.sleep(0.5)
                    elif is_hand_open(landmarks.landmark):
                        pyautogui.hotkey("win", "up")
                        time.sleep(0.5)
                else:
                    if is_scroll_gesture(landmarks.landmark):
                        handle_scroll(landmarks.landmark)
                    elif is_hand_open(landmarks.landmark):
                        handle_zoom(landmarks.landmark)
                    elif is_hand_closed(landmarks.landmark):
                        handle_brightness(landmarks.landmark)

            elif current_mode == 'SCROLL':
                handle_scroll(landmarks.landmark)

            elif current_mode == 'GESTURE':
                recognize_custom_gesture(landmarks.landmark)

            # Multi-finger gestures
            if len(hand_landmarks) >= 2:
                # Implement multi-finger gestures here
                pass

    # Display status information
    cv2.putText(
        frame,
        f"Mode: {current_mode}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )
    cv2.putText(
        frame,
        f"Gesture Control: {'Active' if is_active else 'Inactive'}",
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0) if is_active else (0, 0, 255),
        2,
    )
    cv2.putText(
        frame,
        f"Landmark Visualization: {'Enabled' if show_landmarks else 'Disabled'}",
        (10, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0) if show_landmarks else (0, 0, 255),
        2,
    )
    cv2.putText(
        frame,
        "F1: Toggle control | F2: Toggle landmarks | F3: Switch mode",
        (10, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )

    cv2.imshow("Advanced Gesture Control", frame)
    if cv2.waitKey(5) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
keyboard_listener.stop()