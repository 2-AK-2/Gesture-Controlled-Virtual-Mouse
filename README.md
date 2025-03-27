# 🎯 Gesture-Controlled Virtual Mouse with Voice Commands 🖱️🗣️

## 🚀 Overview
This project implements a **gesture-controlled virtual mouse** using **MediaPipe Hands** and **OpenCV**. It allows users to control the mouse cursor, perform clicks, scroll, and execute various commands using hand gestures. Additionally, it supports **voice commands** for actions like opening applications and adjusting volume. 🎤💻

## ✨ Features
- 🖐️ **Hand Tracking:** Uses **MediaPipe Hands** to detect and track hand landmarks.
- 🖱️ **Cursor Movement:** Move the mouse cursor using the **index finger's** position.
- 🖰 **Clicking Mechanisms:**
  - 👆 **Single Click:** Thumb and index finger close together.
  - ✌️ **Double Click:** Two consecutive clicks within a short time.
  - 🤞 **Right Click:** Thumb and middle finger close together.
- 🔄 **Scrolling:**
  - ☝️ Index finger up & ✌️ middle finger down for **vertical scrolling**.
- 🖥️ **Window Controls:**
  - ✊ **Close window:** Close hand gesture.
  - 🖐️ **Maximize window:** Open hand gesture.
- 🎙️ **Voice Commands:**
  - 📜 "Scroll up/down"
  - 🔊 "Volume up/down"
  - 🔇 "Mute"
  - 🔄 "Switch window"
  - 🌐 "Open browser"
- ⌨️ **Keyboard Shortcuts:**
  - `F1` 🎛️: Toggle **gesture control**.
  - `F2` 🎨: Toggle **hand landmark visualization**.
  - `F3` 🖱️: Toggle **scroll mode**.
  - `Esc` ❌: Exit the program.

## 📦 Prerequisites
Make sure you have the following installed:
- 🐍 **Python 3.x**
- 📷 **OpenCV (`cv2`)**
- ✋ **MediaPipe (`mediapipe`)**
- 🖱️ **PyAutoGUI (`pyautogui`)**
- 🔢 **NumPy (`numpy`)**
- 🎤 **SpeechRecognition (`speech_recognition`)**
- ⌨️ **Pynput (`pynput`)**

Install dependencies using:
```sh
pip install opencv-python mediapipe pyautogui numpy SpeechRecognition pynput
```

## ▶️ Usage
1. **Run the script:**
2. **Position your hand** in front of the webcam. 📸
3. **Use gestures** to control the cursor and clicks. 🖱️
4. **Use voice commands** for additional controls. 🎤
5. **Press `F1`** to activate/deactivate **gesture control**. 🕹️
6. **Press `Esc`** to exit. ❌

## 🛠️ Troubleshooting
- 📷 **Ensure the camera** is properly connected and not used by another application.
- 💡 **Adjust lighting conditions** for better hand tracking.
- 🎯 **If gestures are not recognized correctly,** try adjusting the camera position.

## 🔮 Future Improvements
- 👐 **Multi-hand support** for advanced interactions.
- 🤖 **More refined gesture recognition** with adaptive thresholds.
- 🏡 **Integration with smart home automation.**

