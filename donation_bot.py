import time
import pyautogui as pag
import random
from pynput.keyboard import Key, Controller
import os
from pynput import keyboard
import tkinter as tk
from tkinter import font as tkfont
import threading
import pyautogui
import winsound  # Windows only; see comment below for cross-platform alternative

pag.FAILSAFE = True
kb = Controller()

# ---------------------------------------------------------------------------
# Panel geometry: hug the top-left corner, with MARGIN pixels of slack.
# Set MARGIN = 0 for a true 0,0 corner.
# ---------------------------------------------------------------------------
PANEL_W, PANEL_H = 260, 250
MARGIN = 4

# ---------------------------------------------------------------------------
# Always-on-top control panel
# ---------------------------------------------------------------------------
class ControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bot Control")
        self.root.attributes("-topmost", True)          # always on top
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.terminate)

        title_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        status_font = tkfont.Font(family="Segoe UI", size=9)

        tk.Label(self.root, text="🤖 Bot Status", font=title_font, pady=4).pack()

        self.status_var = tk.StringVar(value="Starting...")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var,
            font=status_font, fg="blue", wraplength=240, justify="left", padx=8, pady=4
        )
        self.status_label.pack(fill="x")

        self.cycle_var = tk.StringVar(value="Cycle: 0")
        tk.Label(self.root, textvariable=self.cycle_var, font=status_font, fg="gray").pack()

        tk.Button(
            self.root, text="⛔ Terminate (or F9)", command=self.terminate,
            bg="#e74c3c", fg="white", font=title_font,
            relief="flat", padx=8, pady=6, cursor="hand2"
        ).pack(fill="x", padx=8, pady=8)

        # Sit in the very top-left corner, then lock the position so the window
        # can't be dragged or nudged by the window manager.
        self.root.geometry(f"{PANEL_W}x{PANEL_H}+{MARGIN}+{MARGIN}")
        self.root.update_idletasks()
        self.root.overrideredirect(True)                 # remove title bar -> no dragging
        self.pin_top_left()                              # snap to the exact corner
        self.root.attributes("-topmost", True)           # re-assert after override

    def pin_top_left(self):
        """Snap the window back into the top-left corner (MARGIN px of slack)."""
        self.root.geometry(f"+{MARGIN}+{MARGIN}")
        self.root.lift()
        self.root.attributes("-topmost", True)

    def set_status(self, text, color="blue"):
        self.status_var.set(text)
        self.status_label.config(fg=color)
        self.root.update_idletasks()
        self.pin_top_left()

    def set_cycle(self, n):
        self.cycle_var.set(f"Cycle: {n}")
        self.root.update_idletasks()

    def terminate(self):
        print("Terminated via UI.")
        os._exit(0)

    def tick(self):
        """Call repeatedly from main thread to keep UI alive."""
        self.root.update()


panel = ControlPanel()

# ---------------------------------------------------------------------------
# Alert sound (Windows beep — no extra libs needed)
# For macOS/Linux replace with: os.system("afplay /System/Library/Sounds/Ping.aiff")
# or: import playsound; playsound.playsound("alert.mp3")
# ---------------------------------------------------------------------------
def alert_sound():
    for _ in range(3):
        winsound.Beep(1000, 300)   # frequency=1000Hz, duration=300ms
        time.sleep(0.1)

# ---------------------------------------------------------------------------
# Keyboard listener
# ---------------------------------------------------------------------------
def on_press(key):
    try:
        if key == keyboard.Key.f9:
            print("F9 pressed, exiting.")
            os._exit(0)
    except Exception:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def press_esc(delay=0.05):
    kb.press(Key.esc)
    time.sleep(delay)
    kb.release(Key.esc)

def press_together(keys, hold_time=0.2):
    for k in keys:
        kb.press(k)
    time.sleep(hold_time)
    for k in keys:
        kb.release(k)

def tap_key(key):
    kb.press(key)
    kb.release(key)

def scan_and_click(image_path, confidence=0.60, max_retries=10, delay=0.05, post_wait=0.05):
    panel.set_status(f"Looking for:\n{image_path}", color="blue")
    for _ in range(max_retries):
        panel.tick()
        try:
            location = pag.locateOnScreen(image_path, confidence=confidence)
        except pag.ImageNotFoundException:
            location = None
        if location:
            point = pag.center(location)
            pag.moveTo(point, duration=0.1)
            pag.click()
            panel.set_status(f"✅ Clicked:\n{image_path}", color="green")
            time.sleep(post_wait + random.uniform(0.2, 0.5))
            return True
        time.sleep(delay)
    panel.set_status(f"⚠️ NOT FOUND:\n{image_path}", color="red")
    alert_sound()
    return False

def generate_line_points(p1, p2, num_points=11, bias=5): #11
    x1, y1 = p1
    x2, y2 = p2
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = x1 + t * (x2 - x1) + random.randint(-bias, bias)
        y = y1 + t * (y2 - y1) + random.randint(-bias, bias)
        points.append((int(x), int(y)))
    return points

def click_position(pos, delay=0.005):
    pag.moveTo(pos[0], pos[1], duration=0.05)
    pag.click()
    time.sleep(delay + random.uniform(0.01, 0.06))

def click_center_screen(num_clicks=11, bias=20):
    sw, sh = pag.size()
    cx, cy = sw // 2, sh // 2
    for _ in range(num_clicks):
        x = cx + random.randint(-bias, bias)
        y = cy + random.randint(-bias, bias)
        pag.moveTo(x, y, duration=0.05)
        pag.click()
        time.sleep(0.01 + random.uniform(0.02, 0.08))

LANES = {
    "top":    ((417, 735),   (1364, 63)),
    "bottom": ((1531, 81),   (2372, 730)),
    "left":   ((365, 938),   (1218, 1568)),
    "right":  ((1635, 1586), (2483, 926)),
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    cycle = 0
    while True:
        cycle += 1
        panel.set_cycle(cycle)
        panel.set_status("Waiting to start cycle...", color="gray")
        panel.tick()
        time.sleep(5)


        if not scan_and_click("newgui.png"):
            continue
        if not scan_and_click("find_match.png"):
            continue
        if not scan_and_click("battle_button.png"):
            continue

        points = {name: generate_line_points(*coords) for name, coords in LANES.items()}

        panel.set_status("Running lane sequence...", color="blue")
        time.sleep(8)
        # pyautogui.scroll(-1000)
        # time.sleep(2)

        tap_key('1')
        for lane in ("top", "bottom", "left", "right"):
            for p in points[lane]:
                click_position(p)

        tap_key('2')
        for p in points["top"][3:6]:
            click_position(p)

        tap_key('q')
        for p in points["top"][3:6]:
            click_position(p)

        tap_key('w')
        for p in points["right"][4:7]:
            click_position(p)

        tap_key('e')
        for p in points["bottom"][4:7]:
            click_position(p)

        tap_key('r')
        for p in points["left"][4:7]:
            click_position(p)

        press_together(['q', 'w', 'e', 'r'], hold_time=0.3)

        tap_key('a')
        click_center_screen(num_clicks=11, bias=300)

        tap_key('z')
        click_position(points["right"][5])

        panel.set_status("Waiting post-match...", color="gray")
        time.sleep(10)

        press_esc(delay=0.05)
        scan_and_click("ok.png")
        scan_and_click("return_home.png")

        panel.set_status(f"✅ Cycle {cycle} complete!", color="green")
        print(f"Cycle {cycle} complete.")


if __name__ == "__main__":
    print("Program running... Press F9 or click Terminate to quit.")
    panel.set_status("Press OK on startup dialog.", color="gray")
    panel.tick()

    bot_thread = threading.Thread(target=main, daemon=True)
    bot_thread.start()

    # Tkinter main loop runs on main thread
    panel.root.mainloop()