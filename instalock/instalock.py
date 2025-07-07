import sys, time, random, json, subprocess, importlib, ctypes
from pathlib import Path

if sys.platform == "win32":
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)

def ensure(pkg):
    try:
        importlib.import_module(pkg)
    except ImportError:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs = {}
        if sys.platform == "win32":
            kwargs["startupinfo"] = startupinfo
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], **kwargs)
        importlib.invalidate_caches()

for _p in ("PySide6", "valclient", "pynput"):
    ensure(_p)

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QSystemTrayIcon, QMenu, QDialog, QGridLayout
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from valclient.client import Client
from pynput import keyboard

CONFIG_PATH = Path.home() / ".valorant_instalocker.json"

MAP_UUID = {
    "7eaecc1b-4337-bbf9-6ab9-04b8f06b3319": "Ascent",
    "2c9d57ec-4431-2c5e-1d4f-23b95f3cac94": "Bind",
    "2fe4ed3a-450a-948b-6d4c-1e3961b32dc4": "Haven",
    "d960549e-485c-e861-8d71-aa9d1aed12a2": "Split",
    "e2ad5c54-4114-a870-9641-8ea21279579a": "Icebox",
    "2d373b0d-4cbe-3fdb-9e3c-0cfdda3dc7dc": "Breeze",
    "9f0e2b41-4cb0-368f-0fda-17f19d1a5e04": "Fracture",
    "fd267378-4d1d-484f-ff52-77821ed10dc2": "Pearl",
    "2ce03784-4fe5-d7fd-14be-bbd1280e61a2": "Lotus",
    "2fe4a9ca-4bef-921c-0f90-458d9f4f4035": "Sunset",
}
MAP_UUID = {k.lower(): v for k, v in MAP_UUID.items()}

MAP_CODE = {
    "ascent": "Ascent",
    "duality": "Bind",
    "triad": "Haven",
    "bonsai": "Split",
    "port": "Icebox",
    "foxtrot": "Breeze",
    "canyon": "Fracture",
    "pitt": "Pearl",
    "jam": "Lotus",
    "juliett": "Sunset",
}

AGENTS = {
    "jett": "add6443a-41bd-e414-f6ad-e58d267f4e95",
    "reyna": "a3bfb853-43b2-7238-a4f1-ad90e9e46bcc",
    "raze": "f94c3b30-42be-e959-889c-5aa313dba261",
    "yoru": "7f94d92c-4234-0a36-9646-3a87eb8b5c89",
    "phoenix": "eb93336a-449b-9c1b-0a54-a891f7921d69",
    "neon": "bb2a4828-46eb-8cd1-e765-15848195d751",
    "breach": "5f8d3a7f-467b-97f3-062c-13acf203c006",
    "skye": "6f2a04ca-43e0-be17-7f36-b3908627744d",
    "sova": "320b2a48-4d9b-a075-30f1-1f93a9b638fa",
    "kayo": "601dbbe7-43ce-be57-2a40-4abd24953621",
    "killjoy": "1e58de9c-4950-5125-93e9-a0aee9f98746",
    "cypher": "117ed9e3-49f3-6512-3ccf-0cada7e3823b",
    "sage": "569fdd95-4d10-43ab-ca70-79becc718b46",
    "chamber": "22697a3d-45bf-8dd7-4fec-84a9e28c69d7",
    "omen": "8e253930-4c05-31dd-1b6c-968525494517",
    "brimstone": "9f0d8ba9-4140-b941-57d3-a7ad57c6b417",
    "astra": "41fb69c1-4189-7b37-f117-bcaf1e96f1bf",
    "viper": "707eab51-4836-f488-046a-cda6bf494859",
    "fade": "dade69b4-4f5a-8528-247b-219e5a1facd6",
    "gekko": "e370fa57-4757-3604-3648-499e1f642d3f",
    "harbor": "95b78ed7-4637-86d9-7e41-71ba8c293152",
    "deadlock": "cc8b64c8-4b25-4ff9-6e7f-37b4da43d235",
    "iso": "0e38b510-41a8-5780-5e8f-568b2a4f2d6c",
    "clove": "1dbf2edd-4729-0984-3115-daa5eed44993",
    "vyse": "eb85b0c8-4258-e95f-f433-0db2e21f857",
}

class OneShotLocker:
    def __init__(self):
        self.region = "eu"
        self.map_pref = {name: "jett" for name in MAP_UUID.values()}
        self._load_config()

    def _load_config(self):
        if CONFIG_PATH.is_file():
            try:
                data = json.loads(CONFIG_PATH.read_text("utf-8"))
                self.region = data.get("region", self.region)
                self.map_pref.update(data.get("map_pref", {}))
            except Exception:
                pass

    def save_config(self):
        try:
            CONFIG_PATH.write_text(json.dumps({"region": self.region, "map_pref": self.map_pref}, indent=2, ensure_ascii=False))
        except Exception:
            pass

    @staticmethod
    def resolve_map(map_id_raw):
        mid = map_id_raw.lower()
        if mid in MAP_UUID:
            return MAP_UUID[mid]
        if mid.startswith("/game/maps/"):
            parts = mid.split("/")
            if len(parts) > 3:
                return MAP_CODE.get(parts[3])
        return MAP_CODE.get(mid)

    def lock_once(self, echo=print):
        try:
            echo("Activating client…")
            client = Client(region=self.region)
            client.activate()
            pre = client.pregame_fetch_match()
            if client.fetch_presence(client.puuid)["sessionLoopState"] != "PREGAME":
                echo("Not in agent-select")
                return
            map_name = self.resolve_map(pre["MapID"])
            if not map_name:
                echo(f"Unknown map ID: {pre['MapID']}")
                return
            agent_key = self.map_pref.get(map_name, "").lower()
            if agent_key not in AGENTS:
                echo(f"No agent set for {map_name}")
                return
            time.sleep(random.uniform(0.2, 0.6))
            agent_id = AGENTS[agent_key]
            client.pregame_select_character(agent_id)
            client.pregame_lock_character(agent_id)
            echo(f"{map_name} → locked {agent_key.capitalize()} ✔")
        except Exception as exc:
            echo(f"Lock failed: {exc}")

locker = OneShotLocker()

class PrefDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map Preferences")
        self.setFixedSize(360, 400)
        grid = QGridLayout(self)
        self.boxes = {}
        for row, m in enumerate(sorted(MAP_UUID.values())):
            grid.addWidget(QLabel(m + ':'), row, 0)
            cb = QComboBox()
            cb.addItems(sorted(AGENTS.keys(), key=str.casefold))
            cb.setCurrentText(locker.map_pref.get(m, "jett"))
            grid.addWidget(cb, row, 1)
            self.boxes[m] = cb
        QPushButton("Save & Close", self, clicked=self.accept)
        grid.addWidget(self.children()[-1], row + 1, 0, 1, 2)

    def accept(self):
        locker.map_pref = {m: cb.currentText().lower() for m, cb in self.boxes.items()}
        locker.save_config()
        super().accept()

class MiniUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Valorant Instalocker")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFixedSize(280, 230)
        self.setStyleSheet(
            "QWidget {background:#181818; color:#fff; font:13px 'Segoe UI';}"
            "QComboBox, QPushButton {background:#242424; border:0; padding:6px; border-radius:6px;}"
            "QComboBox:hover, QPushButton:hover {background:#003399;}"
            "QPushButton#pref {background:#444;}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(15, 15, 15, 15)
        title = QLabel("<b>Valorant Instalocker</b> <span style='color:#0f0'>@Encoder_net</span>")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        lay.addWidget(QLabel("Region:"))
        self.cmb_region = QComboBox()
        self.cmb_region.addItems(["lan", "las", "br", "eu", "na", "ap", "kr"])
        self.cmb_region.setCurrentText(locker.region)
        lay.addWidget(self.cmb_region)
        btn_pref = QPushButton("Edit map preferences")
        btn_pref.setObjectName("pref")
        btn_pref.clicked.connect(lambda: PrefDialog(self).exec())
        lay.addWidget(btn_pref)
        self.lbl_status = QLabel("Ready • press F8")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_status)
        QPushButton("Lock once", self, clicked=self.trigger_lock)
        lay.addWidget(self.children()[-1])
        tray = QSystemTrayIcon(QIcon.fromTheme("applications-games"), self)
        menu = QMenu()
        menu.addAction(QAction("Show", self, triggered=self.showNormal))
        menu.addAction(QAction("Quit", self, triggered=QApplication.quit))
        tray.setContextMenu(menu)
        tray.show()

    def trigger_lock(self):
        locker.region = self.cmb_region.currentText()
        locker.save_config()
        locker.lock_once(self.lbl_status.setText)

def listen_hotkeys():
    combo = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('l')}
    pressed = set()
    def on_press(k):
        pressed.add(k)
        if k == keyboard.Key.f8 or combo <= pressed:
            ui.trigger_lock()
    def on_release(k):
        pressed.discard(k)
    with keyboard.Listener(on_press=on_press, on_release=on_release):
        QApplication.instance().exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MiniUI()
    ui.show()
    listen_hotkeys()
