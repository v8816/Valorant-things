import ctypes, os, sys
import subprocess
import tkinter as tk
def install_package(package):
    """Устанавливает указанный пакет через pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Успешно установлен модуль: {package}")
        return True
    except Exception as e:
        print(f"Ошибка установки {package}: {e}")
        return False

# Проверка наличия keyboard
try:
    import keyboard
except ImportError:
    print("Модуль 'keyboard' не найден. Пытаюсь установить...")
    if install_package("keyboard"):
        import keyboard
    else:
        print("Не удалось установить модуль keyboard. Установите вручную: pip install keyboard")
        sys.exit(1)


def _is_admin() -> bool:
    try:  # win only
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not _is_admin():  
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        f'"{os.path.abspath(__file__)}"', None, 1)
    sys.exit()


MOVEMENT = ('w', 'a', 's', 'd')       
ctrl_blocked = False                  
active      = False                  

def evaluate_block():
    """Решаем, нужно ли блокировать Ctrl прямо сейчас."""
    global ctrl_blocked
    if not active:                    
        if ctrl_blocked:
            keyboard.unblock_key('ctrl')
            ctrl_blocked = False
        return

    shift_down   = keyboard.is_pressed('shift')
    moving_down  = any(keyboard.is_pressed(k) for k in MOVEMENT)
    should_block = shift_down and not moving_down

    if should_block and not ctrl_blocked:
        keyboard.block_key('ctrl')
        keyboard.release('ctrl')
        ctrl_blocked = True
    elif not should_block and ctrl_blocked:
        keyboard.unblock_key('ctrl')
        ctrl_blocked = False

HOOK_KEYS = ('shift', 'ctrl') + MOVEMENT
for key in HOOK_KEYS:
    keyboard.on_press_key(key,  lambda e: evaluate_block())
    keyboard.on_release_key(key, lambda e: evaluate_block())

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
        evaluate_block()    

    def _on_close(self):
        keyboard.unblock_key('ctrl')
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
