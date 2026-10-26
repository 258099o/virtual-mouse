# Hand Gesture Virtual Mouse

Control your computer's mouse with just your hand, using your webcam. No special hardware needed.

The program watches your hand through the camera, finds your fingers using computer vision, and turns hand gestures into real mouse actions: moving the cursor, clicking, scrolling, and switching browser tabs or desktops.

<!-- Add a demo GIF here later: ![Demo](assets/demo.gif) -->

## How it works

```
Camera -> OpenCV -> video frames -> MediaPipe -> 21 hand landmarks
-> our gesture logic -> PyAutoGUI -> operating system -> mouse / keyboard actions
```

- **OpenCV** reads frames from the webcam and draws the on-screen feedback.
- **MediaPipe Hands** finds 21 landmark points (fingertips, knuckles, wrist) on your hand.
- **Our gesture logic** measures distances between fingertips and counts extended fingers to decide which gesture you are making.
- **PyAutoGUI** sends the resulting mouse and keyboard actions to the operating system.

## Gestures

| Action | Gesture |
|---|---|
| Move cursor | Point with your index finger. The cursor follows your fingertip |
| Left click | Pinch thumb + index finger |
| Right click | Pinch thumb + middle finger |
| Double click | Pinch thumb + pinky finger |
| Scroll up / down | Hold index and middle fingertips together. Keep them in the **top third** of the camera view to scroll up, or the **bottom third** to scroll down. Open your fingers to stop |
| Next / previous tab | Hold up **3 fingers** (index, middle, ring) with thumb and pinky folded. Move your hand to the **right** side for the next tab, or the **left** side for the previous tab. Return to the center before swiping again |
| Next / previous desktop (macOS) | Hold up **4 fingers with the thumb tucked in**. Move your hand to the right or left side, same as tab switching |
| Pause tracking | Open palm with all fingers and thumb spread |
| Resume tracking | Make a fist |

The video window shows the current mode (`ACTIVE` / `PAUSED`), the detected gesture, and the FPS. Yellow lines mark the left and right swipe zones.

## Requirements

- Python 3.9 or newer
- A webcam
- macOS (tested). See [Platform support](#platform-support)

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/258099o/virtual-mouse.git
cd virtual-mouse

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

```bash
python3 src/virtual_mouse/main.py
```

- Press **q** in the video window to quit.
- **Emergency stop:** quickly move your real mouse to the top-left corner of the screen. PyAutoGUI's failsafe will stop the program.

## macOS permissions

macOS blocks apps from controlling your computer until you allow them. The app that runs Python (Terminal or VS Code) needs:

1. **Camera**: allow when prompted, or in System Settings > Privacy & Security > Camera.
2. **Accessibility**: System Settings > Privacy & Security > Accessibility, switch on Terminal or VS Code. Without this the cursor will not move.
3. **Desktop switching** also needs **Mission Control shortcuts** turned on: System Settings > Keyboard > Keyboard Shortcuts > Mission Control > "Move left a space" and "Move right a space". You also need at least two desktops.

After changing permissions, quit and reopen Terminal or VS Code.

## Platform support

| Platform | Status |
|---|---|
| macOS | Tested |
| Windows / Linux | Not tested yet. Cursor, click, scroll and tab switching use PyAutoGUI and may work. Desktop switching uses macOS-only code and needs a per-OS version |

## Troubleshooting

- **`module 'mediapipe' has no attribute 'solutions'`**: newer MediaPipe versions removed this API. Install the pinned version with `pip install -r requirements.txt`.
- **`Failed to build pyobjc-core` when installing PyAutoGUI**: run `pip install --upgrade pip` and `xcode-select --install`, then install again.
- **Cursor does not move**: grant Accessibility permission (see above).
- **Camera does not open**: grant Camera permission, and close other apps that are using the camera.
- **Desktop swipe does nothing**: check the Mission Control shortcuts and permissions above.
- **Laggy or jittery**: use good, even lighting and keep your hand clearly in view. Check the FPS shown in the video window.

## Known limitations

- Click-and-drag is not reliable yet.
- Only one hand is tracked.
- Gestures can misfire in poor lighting or with a cluttered background.
- Thumb detection is the least stable part, because the thumb is hard for the camera to read.

## Project structure

```
virtual-mouse/
├── README.md
├── requirements.txt
├── .gitignore
└── src/
    └── virtual_mouse/
        ├── __init__.py
        └── main.py
```

## Contributors

- [@258099o](https://github.com/258099o)
- [Antra (@antra-byte)](https://github.com/antra-byte)

Built with [MediaPipe](https://developers.google.com/mediapipe), [OpenCV](https://opencv.org/) and [PyAutoGUI](https://pyautogui.readthedocs.io/).