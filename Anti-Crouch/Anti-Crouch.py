import ctypes
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

def install_package(package):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs = {
            'startupinfo': startupinfo,
            'creationflags': subprocess.CREATE_NO_WINDOW
        } if sys.platform == "win32" else {}
        subprocess.check_call([sys.executable, "-m", "pip", "install", package], **kwargs)
        return True
    except Exception:
        return False

if sys.platform == "win32":
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)

try:
    import keyboard
except ImportError:
    if not install_package("keyboard"):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка", "Не удалось установить модуль keyboard. Установите вручную: pip install keyboard")
        sys.exit(1)
    import keyboard

def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if sys.platform == "win32" and not _is_admin():  
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1)
    sys.exit()

MOVEMENT = ('w', 'a', 's', 'd')
active = False
blocking = False

def evaluate_condition(event=None):
    global blocking
    if not active:
        new_blocking = False
    else:
        shift_down = keyboard.is_pressed('shift')
        moving_down = any(keyboard.is_pressed(k) for k in MOVEMENT)
        new_blocking = shift_down and not moving_down

    if new_blocking != blocking:
        if new_blocking:
            keyboard.release('ctrl')
        blocking = new_blocking

def global_hook(event):
    if blocking and event.name in ('ctrl', 'ctrl left', 'ctrl right'):
        return False
    return True

def start_keyboard_listener():
    keyboard.hook(global_hook)
    keys = ['shift'] + list(MOVEMENT)
    for key in keys:
        keyboard.on_press_key(key, evaluate_condition)
        keyboard.on_release_key(key, evaluate_condition)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shift-CTRL Blocker")
        self.resizable(False, False)
        
        self.state_lbl = tk.Label(self, text="OFF", width=8,
                                  font=("Segoe UI", 16, "bold"),
                                  bg="#d9534f", fg="white")
        self.toggle_btn = tk.Button(self, text="ON / OFF",
                                    width=12, height=2,
                                    font=("Segoe UI", 10, "bold"),
                                    command=self.toggle)

        self.state_lbl.pack(padx=20, pady=(20, 10))
        self.toggle_btn.pack(padx=20, pady=(0, 20))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def toggle(self):
        global active
        active = not active
        self.state_lbl.config(
            text="ON" if active else "OFF",
            bg="#5cb85c" if active else "#d9534f"
        )
        evaluate_condition()

    def _on_close(self):
        keyboard.unhook_all()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    start_keyboard_listener()
    App().mainloop()
