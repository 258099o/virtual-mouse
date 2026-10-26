import cv2
import mediapipe as mp
import pyautogui
import math
import time
import subprocess
from collections import deque

pyautogui.PAUSE = 0

def switch_desktop(direction):
    key_code = 124 if direction == "right" else 123
    subprocess.Popen([
        "osascript", "-e",
        f'tell application "System Events" to key code {key_code} using control down'
    ])

def count_extended_fingers(hand_landmarks):
    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]

    count = 0
    for tip_id, pip_id in zip(finger_tips, finger_pips):
        tip_y = hand_landmarks.landmark[tip_id].y
        pip_y = hand_landmarks.landmark[pip_id].y
        if tip_y < pip_y:
            count += 1

    return count

def is_thumb_extended(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    pinky_base = hand_landmarks.landmark[17]

    tip_distance = math.hypot(thumb_tip.x - pinky_base.x, thumb_tip.y - pinky_base.y)
    ip_distance = math.hypot(thumb_ip.x - pinky_base.x, thumb_ip.y - pinky_base.y)

    return tip_distance > ip_distance

def classify_gesture(hand_landmarks):
    count = count_extended_fingers(hand_landmarks)
    thumb_open = is_thumb_extended(hand_landmarks)

    if count == 4 and thumb_open:
        return "palm"
    if count == 4:
        return "desktop"
    if count == 3:
        return "tab"
    if count == 0:
        return "fist"
    return "other"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, model_complexity=0)
mp_drawing = mp.solutions.drawing_utils

screen_width, screen_height = pyautogui.size()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

PINCH_THRESHOLD = 0.04
is_left_pinching = False
is_right_pinching = False
is_double_pinching = False

SCROLL_ENTER_THRESHOLD = 0.045
SCROLL_EXIT_THRESHOLD = 0.07
is_scrolling = False
SCROLL_UP_ZONE = 0.35
SCROLL_DOWN_ZONE = 0.65
SCROLL_STEP = 30

SMOOTHING_FACTOR = 0.4
prev_screen_x, prev_screen_y = screen_width / 2, screen_height / 2

is_paused = False

STABLE_FRAMES = 4
recent_gestures = deque(maxlen=STABLE_FRAMES)
stable_gesture = "other"

SIDE_LEFT = 0.35
SIDE_RIGHT = 0.65
ARM_MIN = 0.4
ARM_MAX = 0.6
TAB_COOLDOWN = 0.7
DESKTOP_COOLDOWN = 1.2
swipe_armed = False
last_swipe_kind = None
last_swipe_time = 0

prev_frame_time = time.time()

while True:
    success, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame_h, frame_w = frame.shape[:2]

    frame_time = time.time()
    fps = 1 / (frame_time - prev_frame_time + 0.000001)
    prev_frame_time = frame_time

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            recent_gestures.append(classify_gesture(hand_landmarks))
            if len(recent_gestures) == STABLE_FRAMES and len(set(recent_gestures)) == 1:
                stable_gesture = recent_gestures[0]

            if stable_gesture == "palm":
                if is_left_pinching:
                    pyautogui.mouseUp()
                    is_left_pinching = False
                is_paused = True
            elif stable_gesture == "fist":
                is_paused = False

            cv2.putText(frame, f"Gesture: {stable_gesture}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            if not is_paused and stable_gesture != "fist":
                index_tip = hand_landmarks.landmark[8]
                thumb_tip = hand_landmarks.landmark[4]
                middle_tip = hand_landmarks.landmark[12]
                pinky_tip = hand_landmarks.landmark[20]

                if stable_gesture in ("tab", "desktop"):
                    is_scrolling = False
                    hand_x = hand_landmarks.landmark[9].x

                    left_line = int(SIDE_LEFT * frame_w)
                    right_line = int(SIDE_RIGHT * frame_w)
                    cv2.line(frame, (left_line, 0), (left_line, frame_h), (0, 255, 255), 1)
                    cv2.line(frame, (right_line, 0), (right_line, frame_h), (0, 255, 255), 1)

                    if stable_gesture != last_swipe_kind:
                        swipe_armed = False
                    last_swipe_kind = stable_gesture

                    if ARM_MIN < hand_x < ARM_MAX:
                        swipe_armed = True

                    arm_text = "READY" if swipe_armed else "move to center"
                    cv2.putText(frame, arm_text, (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                    now = time.time()
                    cooldown = TAB_COOLDOWN if stable_gesture == "tab" else DESKTOP_COOLDOWN

                    if swipe_armed and now - last_swipe_time > cooldown:
                        if hand_x > SIDE_RIGHT:
                            if stable_gesture == "tab":
                                pyautogui.hotkey('ctrl', 'tab')
                            else:
                                switch_desktop("right")
                            swipe_armed = False
                            last_swipe_time = now
                        elif hand_x < SIDE_LEFT:
                            if stable_gesture == "tab":
                                pyautogui.hotkey('ctrl', 'shift', 'tab')
                            else:
                                switch_desktop("left")
                            swipe_armed = False
                            last_swipe_time = now

                else:
                    swipe_armed = False
                    last_swipe_kind = None

                    fingers_together_distance = math.sqrt(
                        (index_tip.x - middle_tip.x) ** 2 +
                        (index_tip.y - middle_tip.y) ** 2
                    )

                    if fingers_together_distance < SCROLL_ENTER_THRESHOLD:
                        is_scrolling = True
                    elif fingers_together_distance > SCROLL_EXIT_THRESHOLD:
                        is_scrolling = False

                    if is_scrolling:
                        current_y = (index_tip.y + middle_tip.y) / 2

                        if current_y < SCROLL_UP_ZONE:
                            pyautogui.scroll(SCROLL_STEP)
                        elif current_y > SCROLL_DOWN_ZONE:
                            pyautogui.scroll(-SCROLL_STEP)

                    else:
                        raw_screen_x = index_tip.x * screen_width
                        raw_screen_y = index_tip.y * screen_height

                        smoothed_x = prev_screen_x + (raw_screen_x - prev_screen_x) * SMOOTHING_FACTOR
                        smoothed_y = prev_screen_y + (raw_screen_y - prev_screen_y) * SMOOTHING_FACTOR

                        pyautogui.moveTo(smoothed_x, smoothed_y)

                        prev_screen_x, prev_screen_y = smoothed_x, smoothed_y

                        left_distance = math.sqrt(
                            (index_tip.x - thumb_tip.x) ** 2 +
                            (index_tip.y - thumb_tip.y) ** 2
                        )

                        right_distance = math.sqrt(
                            (middle_tip.x - thumb_tip.x) ** 2 +
                            (middle_tip.y - thumb_tip.y) ** 2
                        )

                        double_distance = math.sqrt(
                            (pinky_tip.x - thumb_tip.x) ** 2 +
                            (pinky_tip.y - thumb_tip.y) ** 2
                        )

                        if left_distance < PINCH_THRESHOLD and not is_left_pinching:
                            pyautogui.mouseDown()
                            is_left_pinching = True
                        elif left_distance >= PINCH_THRESHOLD and is_left_pinching:
                            pyautogui.mouseUp()
                            is_left_pinching = False

                        if right_distance < PINCH_THRESHOLD and not is_right_pinching:
                            pyautogui.click(button='right')
                            is_right_pinching = True
                        elif right_distance >= PINCH_THRESHOLD:
                            is_right_pinching = False

                        if double_distance < PINCH_THRESHOLD and not is_double_pinching:
                            pyautogui.doubleClick()
                            is_double_pinching = True
                        elif double_distance >= PINCH_THRESHOLD:
                            is_double_pinching = False

    else:
        recent_gestures.clear()
        stable_gesture = "other"
        swipe_armed = False
        last_swipe_kind = None
        is_scrolling = False
        if is_left_pinching:
            pyautogui.mouseUp()
            is_left_pinching = False

    status_text = "PAUSED" if is_paused else "ACTIVE"
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Virtual Mouse - Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()