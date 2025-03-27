import cv2 # type: ignore
import mediapipe as mp # type: ignore
import pyautogui 
import numpy as np 
import speech_recognition as sr 
import threading
import time
from pynput import keyboard 

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

def get_hand_landmarks(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    return results.multi_hand_landmarks

def calculate_distance(p1, p2):
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5

def is_click_gesture(landmarks, finger1, finger2):
    return calculate_distance(landmarks[finger1], landmarks[finger2]) < 0.05

def is_hand_closed(landmarks):
    return all(calculate_distance(landmarks[i], landmarks[0]) < 0.1 for i in range(1, 5))

def is_hand_open(landmarks):
    return all(calculate_distance(landmarks[i], landmarks[0]) > 0.15 for i in range(1, 5))

def is_scroll_gesture(landmarks):
    return (landmarks[8].y < landmarks[7].y and  # Index finger up
            landmarks[12].y > landmarks[11].y)   # Middle finger down

def is_pinch_gesture(landmarks):
    return calculate_distance(landmarks[4], landmarks[8]) < 0.05

def move_cursor(landmarks):
    global prev_x, prev_y
    index_tip = landmarks[8]
    
    x = int(index_tip.x * SCREEN_WIDTH)
    y = int(index_tip.y * SCREEN_HEIGHT)
    
    # Dynamic speed based on hand movement
    speed = ((x - prev_x)**2 + (y - prev_y)**2)**0.5
    speed_factor = min(speed / 10, 5)  # Cap the speed factor at 5
    
    # Apply smoothing
    smooth_x = prev_x + (x - prev_x) / SMOOTHING * speed_factor
    smooth_y = prev_y + (y - prev_y) / SMOOTHING * speed_factor
    
    pyautogui.moveTo(smooth_x, smooth_y)
    prev_x, prev_y = smooth_x, smooth_y

def handle_scroll(landmarks):
    global prev_scroll_y
    y = landmarks[8].y
    if prev_scroll_y:
        scroll_amount = int((y - prev_scroll_y) * 1000)
        pyautogui.scroll(-scroll_amount)
    prev_scroll_y = y

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
                pyautogui.hotkey('alt', 'tab')
            elif "open browser" in command:
                pyautogui.hotkey('win', 'r')
                time.sleep(0.5)
                pyautogui.write('chrome')
                pyautogui.press('enter')
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            print("Could not request results from speech recognition service")

def on_press(key):
    global is_active, show_landmarks, scroll_mode
    if key == keyboard.Key.f1:
        is_active = not is_active
        print(f"Gesture control {'activated' if is_active else 'deactivated'}")
    elif key == keyboard.Key.f2:
        show_landmarks = not show_landmarks
        print(f"Landmark visualization {'enabled' if show_landmarks else 'disabled'}")
    elif key == keyboard.Key.f3:
        scroll_mode = not scroll_mode
        print(f"Scroll mode {'activated' if scroll_mode else 'deactivated'}")

# Start voice command thread
voice_thread = threading.Thread(target=handle_voice_commands, daemon=True)
voice_thread.start()

# Start keyboard listener
keyboard_listener = keyboard.Listener(on_press=on_press)
keyboard_listener.start()

# Main loop
cap = cv2.VideoCapture(0)
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

            # Determine if it's the left or right hand
            is_right_hand = landmarks.landmark[4].x < landmarks.landmark[20].x

            if is_right_hand:
                # Right hand controls cursor movement and clicks
                move_cursor(landmarks.landmark)

                if is_click_gesture(landmarks.landmark, 4, 8):  # Thumb and index finger
                    pyautogui.click(button='left')
                    time.sleep(0.2)  # Debounce
                elif is_click_gesture(landmarks.landmark, 4, 12):  # Thumb and middle finger
                    pyautogui.click(button='right')
                    time.sleep(0.2)  # Debounce
                elif is_hand_closed(landmarks.landmark):
                    pyautogui.hotkey('alt', 'f4')  # Close window
                    time.sleep(0.5)  # Debounce
                elif is_hand_open(landmarks.landmark):
                    pyautogui.hotkey('win', 'up')  # Maximize window
                    time.sleep(0.5)  # Debounce
                elif is_pinch_gesture(landmarks.landmark):
                    pyautogui.doubleClick()
                    time.sleep(0.3)  # Debounce
            else:
                # Left hand controls scrolling
                if is_scroll_gesture(landmarks.landmark):
                    handle_scroll(landmarks.landmark)
                elif is_hand_open(landmarks.landmark):
                    # New feature: Zoom in with open left hand
                    pyautogui.hotkey('ctrl', '+')
                    time.sleep(0.5)  # Debounce
                elif is_hand_closed(landmarks.landmark):
                    # New feature: Zoom out with closed left hand
                    pyautogui.hotkey('ctrl', '-')
                    time.sleep(0.5)  # Debounce

    # Display status information
    cv2.putText(frame, f"Gesture Control: {'Active' if is_active else 'Inactive'}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if is_active else (0, 0, 255), 2)
    cv2.putText(frame, f"Landmark Visualization: {'Enabled' if show_landmarks else 'Disabled'}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if show_landmarks else (0, 0, 255), 2)
    cv2.putText(frame, f"Scroll Mode: {'Active' if scroll_mode else 'Inactive'}", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if scroll_mode else (0, 0, 255), 2)
    cv2.putText(frame, "F1: Toggle gesture control | F2: Toggle landmarks | F3: Toggle scroll mode", (10, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow('Gesture Control', frame)
    if cv2.waitKey(5) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
keyboard_listener.stop()