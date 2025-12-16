
# main.py (full, updated: full yellow Step 0 + improved list visibility + yellow taskbar icon + robust Select/Deselect All + delete deselected + logging/signal fixes)
# colorFabb Filament Installer — 2026 look & feel

import sys, os, zipfile, shutil, hashlib, argparse, logging, tempfile
from pathlib import Path
from urllib.request import urlopen, Request

GUI_ENABLED = True
try:
    from PySide6.QtCore import Qt, QThread, Signal, QSize
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QListWidgetItem, QProgressBar, QStackedWidget, QCheckBox,
        QMessageBox, QFileDialog, QLineEdit
    )
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
except Exception:
    GUI_ENABLED = False

APP_DISPLAY_NAME = "colorFabb Filament Installer"
VERSION = "1.6.2"

GITHUB_ZIP_URL = "https://github.com/colorfabb/printer-profiles/archive/refs/heads/main.zip"
EXPECTED_SHA256 = None

PRUSA_EXTS = {".ini"}
JSON_EXTS  = {".json", ".jso"}

# ========= PATH HELPERS =========
def appdata_base() -> Path:
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    else:
        return Path.home() / ".config"

def slicer_targets_from_base(base: Path):
    return {
        "PrusaSlicer": {
            "filament": base / "PrusaSlicer" / "filament",
            "print":    base / "PrusaSlicer" / "print",
        },
        "OrcaSlicer": {
            "filament": base / "OrcaSlicer" / "user" / "default" / "filament",
            "process":  base / "OrcaSlicer" / "user" / "default" / "process",
        },
        "BambuStudio": {
            "filament": base / "BambuStudio" / "user" / "default" / "filament",
            "process":  base / "BambuStudio" / "user" / "default" / "process",
        },
    }

# ========= TEMP =========
TEMP_ROOT = Path(tempfile.gettempdir()) / "colorfabb_installer"
CACHE_DIR = TEMP_ROOT / "cache"
INSTALLED_LIST = TEMP_ROOT / "installed_files.txt"
LOG_FILE = TEMP_ROOT / "installer.log"

# ========= LOGO (MEIPASS-aware) =========
SCRIPT_DIR = Path(__file__).parent
LOGO_CANDIDATES = [
    ("logo/cF_Logo.png", "logo"),            # primair
    ("logo/logo.png",    "logo"),
    ("logo/colorfabb.png","logo"),
    ("logo/colorfabb_logo.png","logo"),
    ("logo.png",         ""),                # root fallback
]

def find_logo() -> Path | None:
    candidates = []
    if getattr(sys, "_MEIPASS", None):
        base = Path(sys._MEIPASS)
        for rel, _sub in LOGO_CANDIDATES:
            p = base / rel
            if p.exists():
                candidates.append(p)
    for rel, _sub in LOGO_CANDIDATES:
        p = SCRIPT_DIR / rel
        if p.exists():
            candidates.append(p)
    return candidates[0] if candidates else None

def make_yellow_icon(pm: QPixmap) -> QIcon:
    """
    Compose a square yellow icon (for taskbar/Alt-Tab) with the logo centered.
    Creates multiple sizes for crisp rendering.
    """
    def compose(size: int) -> QPixmap:
        canvas = QPixmap(size, size)
        canvas.fill(QColor("#FFC400"))
        painter = QPainter(canvas)
        # max logo area with margins
        margin = int(size * 0.12)
        target_w = size - 2*margin
        target_h = size - 2*margin
        scaled = pm.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (size - scaled.width()) // 2
        y = (size - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        return canvas

    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(componse := compose(s))
    return icon

# ========= LOGGING =========
def setup_logging():
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    handlers = []
    try:
        handlers.append(logging.FileHandler(LOG_FILE, encoding='utf-8'))
    except Exception:
        pass
    handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        handlers=handlers)

# ========= UTILS =========
def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def humanize_bytes(n: int) -> str:
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024.0:
            return f"{n:3.1f} {unit}" if unit != 'B' else f"{n} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# ========= DOWNLOAD THREAD =========
class ZipDownloader(QThread):
    progress    = Signal(int, int)
    finished_ok = Signal(Path, str)  # zip_path, sha256
    failed      = Signal(str)
    def __init__(self, url: str, dest_zip: Path):
        super().__init__()
        self.url = url
        self.dest_zip = dest_zip
    def run(self):
        try:
            ensure_dir(self.dest_zip.parent)
            req = Request(self.url, headers={"User-Agent":"colorFabb-Installer"})
            with urlopen(req) as r:
                total = int(r.headers.get("Content-Length", "0")) if r.headers.get("Content-Length") else 0
                downloaded = 0
                chunk = 8192
                with open(self.dest_zip, "wb") as f:
                    while True:
                        buf = r.read(chunk)
                        if not buf: break
                        f.write(buf)
                        downloaded += len(buf)
                        self.progress.emit(downloaded, total)
            with zipfile.ZipFile(self.dest_zip, 'r') as z:
                z.testzip()
            self.finished_ok.emit(self.dest_zip, sha256_file(self.dest_zip))
        except Exception as e:
            self.failed.emit(str(e))

# ========= EXTRACT & PARSE REPO =========
def extract_zip(zip_path: Path, dest_dir: Path):
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    ensure_dir(dest_dir)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest_dir)

def _casefold(s: str) -> str:
    return s.replace("\\", "/").lower()

def collect_repo_profiles_robust(extracted_root: Path):
    filament_items = []
    process_items  = []
    for p in extracted_root.rglob("*"):
        if not p.is_file(): continue
        ext  = p.suffix.lower()
        path = _casefold(str(p))
        if "/prusaslicer/" in path and ext in PRUSA_EXTS:
            if "/filament/" in path:
                filament_items.append({"slicer":"PrusaSlicer","src":p})
            elif "/print/" in path:
                process_items.append({"slicer":"PrusaSlicer","src":p,"category":"print"})
            continue
        if "/orcaslicer/" in path and ext in JSON_EXTS:
            if "/filament/" in path:
                filament_items.append({"slicer":"OrcaSlicer","src":p})
            elif "/process/" in path:
                process_items.append({"slicer":"OrcaSlicer","src":p,"category":"process"})
            continue
        if ("/bambustudio/" in path or "/bambu studio/" in path) and ext in JSON_EXTS:
            if "/filament/" in path:
                filament_items.append({"slicer":"BambuStudio","src":p})
            elif "/process/" in path:
                process_items.append({"slicer":"BambuStudio","src":p,"category":"process"})
            continue
    return filament_items, process_items

# ========= STATE =========
def read_installed_set() -> set[Path]:
    s = set()
    if INSTALLED_LIST.exists():
        with open(INSTALLED_LIST, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line: s.add(Path(line))
    return s

def rewrite_installed_list(remove_paths: list[Path], add_paths: list[Path]):
    current = read_installed_set()
    for p in remove_paths: current.discard(Path(p))
    for p in add_paths:    current.add(Path(p))
    try:
        INSTALLED_LIST.parent.mkdir(parents=True, exist_ok=True)
        with open(INSTALLED_LIST, 'w', encoding='utf-8') as f:
            for p in sorted(current):
                f.write(str(p) + "\n")
    except Exception:
        pass

def uninstall_installed_files(dry_run: bool = False) -> tuple[int, int]:
    current = read_installed_set()
    total = len(current); deleted = 0
    for p in list(current):
        if p.exists() and p.is_file():
            logging.info(f"Uninstall: removing {p}")
            if not dry_run:
                try:
                    p.unlink(); deleted += 1
                except Exception as e:
                    logging.error(f"Failed to remove {p}: {e}")
        else:
            logging.info(f"Uninstall: not found {p}")
    if not dry_run:
        rewrite_installed_list(remove_paths=list(current), add_paths=[])
    return (deleted, total)

# ========= THEMES =========
APP_QSS = """
* { font-family: 'Segoe UI', 'Inter', 'Calibri', 'Arial'; font-size: 12.5pt; }
QWidget { background: #FAFBFE; color: #121212; }
QPushButton { background: #111; color: #fff; border: 0; padding: 10px 18px; border-radius: 10px; }
QPushButton:hover { background: #222; }
QPushButton:disabled { background: #AAB0B7; color: #fff; }
QLineEdit { background: #fff; border: 1px solid #E3E5EA; border-radius: 8px; padding: 8px 10px; }
QListWidget { background: #fff; border: 1px solid #E3E5EA; border-radius: 10px; }
QListWidget::item { padding: 6px; }
QListWidget::item:hover { background: #FFF6CC; }
QListWidget::item:selected { background: #FFE27A; color: #111; }  /* duidelijk geselecteerd */
QProgressBar { border: 1px solid #E3E5EA; border-radius: 10px; background: #fff; text-align: center; height: 16px; }
QProgressBar::chunk { background: #FFC400; border-radius: 10px; }
QCheckBox { spacing: 8px; }
"""
WELCOME_QSS = """
* { font-family: 'Segoe UI', 'Inter', 'Calibri', 'Arial'; font-size: 12.5pt; }
QWidget { background: #FFC400; color: #111; }
QPushButton { background: #111; color: #fff; border: 0; padding: 10px 18px; border-radius: 10px; }
QPushButton:hover { background: #222; }
QPushButton:disabled { background: #AAB0B7; color: #fff; }
QLineEdit { background: #fff; border: 1px solid #E3E5EA; border-radius: 8px; padding: 8px 10px; }
QListWidget { background: #fff; border: 1px solid #E3E5EA; border-radius: 10px; }
QListWidget::item { padding: 6px; }
QListWidget::item:selected { background: #FFE27A; color: #111; }
QProgressBar { border: 1px solid #E3E5EA; border-radius: 10px; background: #fff; text-align: center; height: 16px; }
QProgressBar::chunk { background: #111; border-radius: 10px; }
"""
HEADER_QSS = "background:#FFC400; padding:14px; border:0; border-bottom:1px solid #e6e6e6;"

# ========= GUI =========
if GUI_ENABLED:

    class PageWelcome(QWidget):
        next_requested = Signal()
        def __init__(self):
            super().__init__()
            self.logo_path = find_logo()
            root = QVBoxLayout(self)
            root.setContentsMargins(36, 36, 36, 36)

            self.logo_label = QLabel()
            self.logo_label.setAlignment(Qt.AlignCenter)

            title = QLabel("colorFabb Filament Installer")
            title.setStyleSheet("font-size:32pt; font-weight:800; color:#111;")
            title.setAlignment(Qt.AlignLeft)

            subtitle = QLabel("Install or update filament & print/process profiles for your slicers.\nFast, clean, and always up-to-date.")
            subtitle.setStyleSheet("font-size:13.5pt; color:#111;")
            subtitle.setAlignment(Qt.AlignLeft)

            root.addWidget(self.logo_label, 4)
            root.addSpacing(8)
            root.addWidget(title, 0, Qt.AlignLeft)
            root.addWidget(subtitle, 0, Qt.AlignLeft)
            root.addStretch(2)

        def resizeEvent(self, e):
            if self.logo_path:
                pm = QPixmap(str(self.logo_path))
                if not pm.isNull():
                    target_w = int(self.width() * 0.60)
                    target_h = int(self.height() * 0.40)
                    scaled = pm.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.logo_label.setPixmap(scaled)
            else:
                self.logo_label.clear()
            super().resizeEvent(e)

    class Header(QWidget):
        def __init__(self, text: str):
            super().__init__()
            lay = QHBoxLayout(self); lay.setContentsMargins(14,10,14,10)
            lp = find_logo()
            if lp:
                pm = QPixmap(str(lp))
                if not pm.isNull():
                    logo = QLabel()
                    logo.setPixmap(pm.scaledToHeight(28, Qt.SmoothTransformation))
                    lay.addWidget(logo)
            title = QLabel(text)
            title.setStyleSheet("font-size:18pt; font-weight:800; margin-left:12px; color:#111;")
            lay.addWidget(title); lay.addStretch(1)
            self.setStyleSheet(HEADER_QSS)

    class PageSlicers(QWidget):
        selection_changed = Signal()
        base_changed = Signal()
        def __init__(self):
            super().__init__()
            self.base = appdata_base()
            self.targets = slicer_targets_from_base(self.base)
            outer = QVBoxLayout(self)
            outer.addWidget(Header("Step 1 of 4: Select Slicer Software"))

            self.checks = {}
            self.path_edits = {}
            def mk_status_text(files_found: int) -> str:
                return f"✔ {files_found} profiles detected" if files_found > 0 else "✘ Not detected"

            for name in ["PrusaSlicer","OrcaSlicer","BambuStudio"]:
                row = QHBoxLayout()
                box = QCheckBox(name)
                box.stateChanged.connect(lambda *_: self.selection_changed.emit())
                box.toggled.connect(lambda *_: self.selection_changed.emit())
                self.checks[name] = box

                cats = self.targets[name]
                files_found = 0
                for p in cats.values():
                    if p.exists():
                        files_found += sum(1 for f in p.glob("**/*") if f.is_file())
                status = QLabel(mk_status_text(files_found))
                status.setStyleSheet("color:{};".format("#0a8f08" if files_found>0 else "#c60000"))

                edit = QLineEdit(str(self.base)); edit.setFixedWidth(360)
                self.path_edits[name] = edit

                btn = QPushButton("Browse…"); btn.setStyleSheet("QPushButton{background:#FFC400;color:#111;border-radius:8px;}")
                def pick(s=name):
                    dlg = QFileDialog(self); dlg.setFileMode(QFileDialog.Directory); dlg.setOption(QFileDialog.ShowDirsOnly, True)
                    if dlg.exec():
                        sel = dlg.selectedFiles()
                        if sel:
                            self.path_edits[s].setText(sel[0])
                            self.update_targets()
                            cats2 = self.targets[s]
                            files = 0
                            for pth in cats2.values():
                                if pth.exists():
                                    files += sum(1 for f in pth.glob("**/*") if f.is_file())
                            status.setText(mk_status_text(files))
                            status.setStyleSheet("color:{};".format("#0a8f08" if files>0 else "#c60000"))
                            self.base_changed.emit()
                btn.clicked.connect(pick)

                row.addWidget(box); row.addWidget(status)
                row.addWidget(edit); row.addWidget(btn)
                outer.addLayout(row)

            outer.addStretch(1)
            self.selection_changed.emit()

        def update_targets(self):
            for name in ["PrusaSlicer","OrcaSlicer","BambuStudio"]:
                base = Path(self.path_edits[name].text())
                self.targets[name] = slicer_targets_from_base(base)[name]

        def selected_slicers(self):
            return [n for n,b in self.checks.items() if b.checkState() == Qt.Checked]

        def targets_for_selected(self):
            self.update_targets()
            return {n:self.targets[n] for n in self.selected_slicers()}

    # ------- Select/Deselect All helper mixin -------
    class SelectListMixin:
        def are_all_selected(self, list_widget: QListWidget) -> bool:
            return all(list_widget.item(i).checkState() == Qt.Checked for i in range(list_widget.count())) if list_widget.count() else False
        def are_none_selected(self, list_widget: QListWidget) -> bool:
            return all(list_widget.item(i).checkState() == Qt.Unchecked for i in range(list_widget.count())) if list_widget.count() else True
        def set_all(self, list_widget: QListWidget, checked: bool):
            for i in range(list_widget.count()):
                it = list_widget.item(i)
                it.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    class PageFilament(QWidget, SelectListMixin):
        selection_changed = Signal()
        request_download = Signal()
        def __init__(self):
            super().__init__()
            self.items = []
            outer = QVBoxLayout(self)
            outer.addWidget(Header("Step 2 of 4: Select Filament Profiles"))

            self.select_all = QCheckBox("Select All")
            self.select_all.clicked.connect(self.on_select_all_clicked)  # slimme toggle
            outer.addWidget(self.select_all)

            self.list = QListWidget()
            self.list.setAlternatingRowColors(True)
            self.list.itemChanged.connect(self.on_item_changed)  # label/updating
            outer.addWidget(self.list, 1)

            self.info = QLabel("Loading profiles...")
            self.info.setStyleSheet("color:#5f6368;"); outer.addWidget(self.info)

            row = QHBoxLayout()
            self.btn_load = QPushButton("Load Profiles")
            self.btn_load.setStyleSheet("QPushButton{background:#FFC400;color:#111;border-radius:8px;}")
            self.btn_load.clicked.connect(self.request_download.emit)
            row.addWidget(self.btn_load); row.addStretch(1)
            outer.addLayout(row)
            self.loaded = False

        def on_item_changed(self, _item):
            # update label van Select All
            self.refresh_select_all_label()
            self.selection_changed.emit()

        def refresh_select_all_label(self):
            if self.list.count() == 0:
                self.select_all.setText("Select All")
                self.select_all.setChecked(False)
                return
            if self.are_all_selected(self.list):
                self.select_all.setText("Deselect All")
                self.select_all.setChecked(True)
            else:
                self.select_all.setText("Select All")
                # Houd checkbox-state sync met "niet alles geselecteerd"
                self.select_all.setChecked(False)

        def on_select_all_clicked(self, _checked: bool):
            # Toggle op basis van huidige staat van de lijst
            if self.are_all_selected(self.list):
                self.set_all(self.list, False)
            else:
                self.set_all(self.list, True)
            self.refresh_select_all_label()
            self.selection_changed.emit()

        def set_items(self, items, selected_slicers):
            self.items = [it for it in items if it["slicer"] in selected_slicers]
            self.list.blockSignals(True)
            self.list.clear()
            for it in self.items:
                label = f"[{it['slicer']} | filament] {it['src'].name}"
                li = QListWidgetItem(label)
                li.setFlags(li.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                li.setCheckState(Qt.Checked)
                li.setToolTip(str(it['src']))
                self.list.addItem(li)
            self.list.blockSignals(False)
            self.loaded = True
            # Start: alles geselecteerd → label wordt "Deselect All"
            self.refresh_select_all_label()
            self.info.setText(f"Loaded {self.list.count()} filament profiles.")
            self.selection_changed.emit()

        def selected_indices(self):
            return [i for i in range(self.list.count()) if self.list.item(i).checkState()==Qt.Checked]

    class PageProcess(QWidget, SelectListMixin):
        selection_changed = Signal()
        def __init__(self):
            super().__init__()
            self.items = []
            outer = QVBoxLayout(self)
            outer.addWidget(Header("Step 3 of 4: Select Print / Process Profiles"))

            self.select_all = QCheckBox("Select All")
            self.select_all.clicked.connect(self.on_select_all_clicked)
            outer.addWidget(self.select_all)

            self.list = QListWidget()
            self.list.setAlternatingRowColors(True)
            self.list.itemChanged.connect(self.on_item_changed)
            outer.addWidget(self.list, 1)

            self.info = QLabel("Loading profiles...")
            self.info.setStyleSheet("color:#5f6368;"); outer.addWidget(self.info)
            self.loaded = False

        def on_item_changed(self, _item):
            self.refresh_select_all_label()
            self.selection_changed.emit()

        def refresh_select_all_label(self):
            if self.list.count() == 0:
                self.select_all.setText("Select All")
                self.select_all.setChecked(False)
                return
            if self.are_all_selected(self.list):
                self.select_all.setText("Deselect All")
                self.select_all.setChecked(True)
            else:
                self.select_all.setText("Select All")
                self.select_all.setChecked(False)

        def on_select_all_clicked(self, _checked: bool):
            if self.are_all_selected(self.list):
                self.set_all(self.list, False)
            else:
                self.set_all(self.list, True)
            self.refresh_select_all_label()
            self.selection_changed.emit()

        def set_items(self, items, selected_slicers):
            self.items = [it for it in items if it["slicer"] in selected_slicers]
            self.list.blockSignals(True)
            self.list.clear()
            for it in self.items:
                cat = it.get("category","process")
                label = f"[{it['slicer']} | {cat}] {it['src'].name}"
                li = QListWidgetItem(label)
                li.setFlags(li.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                li.setCheckState(Qt.Checked)
                li.setToolTip(str(it['src']))
                self.list.addItem(li)
            self.list.blockSignals(False)
            self.loaded = True
            self.refresh_select_all_label()
            self.info.setText(f"Loaded {self.list.count()} print/process profiles.")
            self.selection_changed.emit()

        def selected_indices(self):
            return [i for i in range(self.list.count()) if self.list.item(i).checkState()==Qt.Checked]

    class PageInstall(QWidget):
        start_install = Signal()
        def __init__(self):
            super().__init__()
            outer = QVBoxLayout(self)
            outer.addWidget(Header("Step 4 of 4: Install"))
            self.label = QLabel("Installing files...")
            outer.addWidget(self.label)
            self.progress = QProgressBar(); self.progress.setMinimum(0); self.progress.setValue(0)
            outer.addWidget(self.progress)
            self.detail = QLabel(""); self.detail.setStyleSheet("color:#5f6368;")
            outer.addWidget(self.detail)
            outer.addStretch(1)

    class PageDone(QWidget):
        def __init__(self):
            super().__init__()
            outer = QVBoxLayout(self)
            outer.addWidget(Header("Done"))
            self.summary = QLabel("")
            outer.addWidget(self.summary)
            outer.addStretch(1)

    class InstallerWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(APP_DISPLAY_NAME)
            self.setMinimumSize(QSize(1024, 680))

            # Heldere (gele) taskbar icon
            lp = find_logo()
            if lp:
                try:
                    pm = QPixmap(str(lp))
                    if not pm.isNull():
                        icon = make_yellow_icon(pm)
                        self.setWindowIcon(icon)
                        QApplication.instance().setWindowIcon(icon)
                except Exception:
                    pass

            self.zip_path    = CACHE_DIR / "profiles.zip"
            self.extract_dir = CACHE_DIR / "profiles_extracted"

            layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
            self.stack = QStackedWidget(); self.stack.setContentsMargins(0,0,0,0)
            layout.addWidget(self.stack, 1)

            self.pg_welcome  = PageWelcome()      # Step 0
            self.pg_slicers  = PageSlicers()      # Step 1
            self.pg_filament = PageFilament()     # Step 2
            self.pg_process  = PageProcess()      # Step 3
            self.pg_install  = PageInstall()      # Step 4
            self.pg_done     = PageDone()
            for pg in [self.pg_welcome, self.pg_slicers, self.pg_filament, self.pg_process, self.pg_install, self.pg_done]:
                self.stack.addWidget(pg)

            nav = QHBoxLayout()
            nav.setContentsMargins(24, 12, 24, 24)
            nav.setSpacing(16)
            self.btn_back = QPushButton("← Back"); self.btn_back.setStyleSheet("QPushButton{background:#eaecef;color:#111;border-radius:8px;}")
            self.btn_next = QPushButton("Get started")
            nav.addWidget(self.btn_back); nav.addStretch(1); nav.addWidget(self.btn_next)
            layout.addLayout(nav)

            self.btn_back.clicked.connect(self.on_back)
            self.btn_next.clicked.connect(self.on_next)
            self.pg_filament.request_download.connect(self.download_profiles)
            self.pg_slicers.selection_changed.connect(self.update_nav)
            self.pg_slicers.base_changed.connect(self.update_nav)
            self.pg_filament.selection_changed.connect(self.update_nav)
            self.pg_process.selection_changed.connect(self.update_nav)
            # Install is triggered via the shared bottom-right navigation button.

            self.repo_filament_all = []
            self.repo_process_all  = []
            self.copy_plan   = []
            self.delete_plan = []
            self.total_ops   = 0

            self.apply_theme()
            self.update_nav()

        # Theming per stap
        def apply_theme(self):
            app = QApplication.instance()
            idx = self.stack.currentIndex()
            if idx == 0:
                app.setStyleSheet(WELCOME_QSS)   # alles geel
            else:
                app.setStyleSheet(APP_QSS)       # licht thema

        def update_nav(self):
            self.apply_theme()
            idx = self.stack.currentIndex()
            self.btn_back.setEnabled(idx > 0)
            if idx == 0:
                self.btn_next.setText("Get started")
                self.btn_next.setEnabled(True)
            elif idx == 1:
                self.btn_next.setText("Next →")
                self.btn_next.setEnabled(len(self.pg_slicers.selected_slicers()) > 0)
            elif idx == 2:
                self.btn_next.setText("Next →")
                self.btn_next.setEnabled(self.pg_filament.loaded)
            elif idx == 3:
                self.btn_next.setText("Install")
                self.btn_next.setEnabled(self.pg_process.loaded)
            elif idx == 4:
                self.btn_next.setText("Install")
                self.btn_next.setEnabled(True)
            else:
                self.btn_next.setText("Close")
                self.btn_next.setEnabled(True)

        def on_back(self):
            i = self.stack.currentIndex()
            if i > 0: self.stack.setCurrentIndex(i - 1)
            self.update_nav()

        def on_next(self):
            self.update_nav()
            i = self.stack.currentIndex()
            if i == 0:
                self.stack.setCurrentIndex(1)
            elif i == 1:
                self.stack.setCurrentIndex(2)
                self.download_profiles()  # auto-load
            elif i == 2:
                self.stack.setCurrentIndex(3)
            elif i == 3:
                self.prepare_copy_and_delete_plans()
                self.stack.setCurrentIndex(4)
            elif i == 4:
                self.install_selected()
            else:
                self.close()
            self.update_nav()

        # DOWNLOAD
        def download_profiles(self):
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                self.pg_filament.btn_load.setEnabled(False)
                self.pg_filament.info.setText("Downloading profiles ZIP from GitHub...")
                self.downloader = ZipDownloader(GITHUB_ZIP_URL, self.zip_path)
                self.downloader.progress.connect(self.on_download_progress)
                self.downloader.finished_ok.connect(self.on_download_done)
                self.downloader.failed.connect(self.on_download_failed)
                self.downloader.start()
            except Exception as e:
                QMessageBox.critical(self, "Download error", str(e))
                self.pg_filament.btn_load.setEnabled(True)

        def on_download_progress(self, downloaded: int, total: int):
            if total > 0:
                self.pg_filament.info.setText(f"Downloading... {humanize_bytes(downloaded)} / {humanize_bytes(total)}")
            else:
                self.pg_filament.info.setText(f"Downloading... {humanize_bytes(downloaded)}")

        def on_download_done(self, zip_path: Path, digest: str):
            try:
                if EXPECTED_SHA256 and digest.lower() != EXPECTED_SHA256.lower():
                    raise RuntimeError(f"SHA256 mismatch. Got {digest}, expected {EXPECTED_SHA256}")
                self.pg_filament.info.setText(f"Extracting ZIP... (sha256: {digest[:12]}…)")
                extract_zip(zip_path, self.extract_dir)
                fil, proc = collect_repo_profiles_robust(self.extract_dir)
                self.repo_filament_all = fil
                self.repo_process_all  = proc
                sel = self.pg_slicers.selected_slicers()
                self.pg_filament.set_items(self.repo_filament_all, sel)
                self.pg_process.set_items(self.repo_process_all, sel)
                if not self.repo_filament_all and not self.repo_process_all:
                    raise RuntimeError("No profiles found in ZIP. Check repo structure and extensions.")
            except Exception as e:
                QMessageBox.critical(self, "Extract error", str(e))
            finally:
                self.pg_filament.btn_load.setEnabled(True)
                self.update_nav()

        def on_download_failed(self, msg: str):
            QMessageBox.critical(self, "Download failed", msg)
            self.pg_filament.btn_load.setEnabled(True)
            self.update_nav()

        # PLANS
        def _dest_for_item(self, it, targets):
            slicer = it["slicer"]
            category = it.get("category", "filament")
            base = targets.get(slicer, {}).get(category)
            if not base: return None
            return base / it["src"].name

        def prepare_copy_and_delete_plans(self):
            targets = self.pg_slicers.targets_for_selected()
            for slicer, cats in targets.items():
                for d in cats.values(): ensure_dir(d)

            all_dests = set()
            for it in self.pg_filament.items:
                dst = self._dest_for_item(it, targets)
                if dst: all_dests.add(dst)
            for it in self.pg_process.items:
                dst = self._dest_for_item(it, targets)
                if dst: all_dests.add(dst)

            sel_dests = set()
            for idx in self.pg_filament.selected_indices():
                it = self.pg_filament.items[idx]; dst = self._dest_for_item(it, targets)
                if dst: sel_dests.add(dst)
            for idx in self.pg_process.selected_indices():
                it = self.pg_process.items[idx];  dst = self._dest_for_item(it, targets)
                if dst: sel_dests.add(dst)

            self.delete_plan = [p for p in all_dests - sel_dests if p.exists() and p.is_file()]
            self.copy_plan   = []
            for idx in self.pg_filament.selected_indices():
                it = self.pg_filament.items[idx]; dst = self._dest_for_item(it, targets)
                if dst: self.copy_plan.append((it["src"], dst))
            for idx in self.pg_process.selected_indices():
                it = self.pg_process.items[idx];  dst = self._dest_for_item(it, targets)
                if dst: self.copy_plan.append((it["src"], dst))

            self.total_ops = len(self.copy_plan)
            self.pg_install.progress.setMaximum(max(1, self.total_ops))
            self.pg_install.label.setText(f"Installing {self.total_ops} files (removing {len(self.delete_plan)} deselected)...")
            self.pg_install.detail.setText("Ready.")

        # INSTALL
        def install_selected(self):
            try:
                # Disable navigation during install to prevent double-clicks.
                self.btn_back.setEnabled(False)
                self.btn_next.setEnabled(False)
                removed = []
                for dst in self.delete_plan:
                    try:
                        dst.unlink()
                        removed.append(dst)
                        self.pg_install.detail.setText(f"Removed {dst.name} from {dst.parent}")
                        QApplication.processEvents()
                    except Exception as e:
                        logging.error(f"Failed to remove {dst}: {e}")
                rewrite_installed_list(remove_paths=removed, add_paths=[])
                done = 0; added = []
                for src, dst in self.copy_plan:
                    ensure_dir(dst.parent)
                    shutil.copy2(src, dst)
                    added.append(dst)
                    done += 1
                    self.pg_install.progress.setValue(done)
                    self.pg_install.detail.setText(f"Copying {src.name} → {dst}")
                    QApplication.processEvents()
                rewrite_installed_list(remove_paths=[], add_paths=added)
                self.pg_install.detail.setText("Done.")
                self.pg_done.summary.setText(
                    f"Installed {self.total_ops} files.\nRemoved {len(removed)} deselected files.\nYou can close the installer."
                )
                self.stack.setCurrentIndex(5)
            except Exception as e:
                QMessageBox.critical(self, "Install error", str(e))
            finally:
                self.btn_back.setEnabled(True)
                self.btn_next.setEnabled(True)

# ========= CLI =========
def parse_args():
    ap = argparse.ArgumentParser(description=APP_DISPLAY_NAME)
    ap.add_argument('--silent', action='store_true', help='Run headless without GUI')
    ap.add_argument('--all', action='store_true', help='With --silent, install for all detected slicers')
    ap.add_argument('--slicers', nargs='*', default=None, help='Limit to specific slicers')
    ap.add_argument('--uninstall', action='store_true', help='Remove files installed by this installer')
    ap.add_argument('--dry-run', action='store_true', help='Only report what would be removed (with --uninstall)')
    ap.add_argument('--check-download', action='store_true', help='Download + validate the profiles ZIP (no install)')
    ap.add_argument('--base', default=None, help='Override base folder (defaults to %APPDATA%)')
    return ap.parse_args()

def check_download_only() -> None:
    """Download and validate the profiles ZIP without installing anything."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = CACHE_DIR / "profiles.zip"
    extract_dir = CACHE_DIR / "profiles_extracted"

    logging.info(f"Download check: {GITHUB_ZIP_URL}")
    req = Request(GITHUB_ZIP_URL, headers={"User-Agent": "colorFabb-Installer"})
    with urlopen(req) as r, open(zip_path, 'wb') as f:
        shutil.copyfileobj(r, f)

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.testzip()

    digest = sha256_file(zip_path)
    logging.info(f"ZIP sha256 = {digest}")
    if EXPECTED_SHA256 and digest.lower() != EXPECTED_SHA256.lower():
        raise RuntimeError(f"SHA256 mismatch: got {digest}, expected {EXPECTED_SHA256}")

    extract_zip(zip_path, extract_dir)
    fil, proc = collect_repo_profiles_robust(extract_dir)
    logging.info(f"Extract OK. Found {len(fil)} filament + {len(proc)} process profiles.")

    # Write a small marker file for quick verification (useful for windowed EXE).
    try:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        marker = TEMP_ROOT / "download_check_ok.txt"
        marker.write_text(
            f"OK\nsha256={digest}\nurl={GITHUB_ZIP_URL}\nfilament={len(fil)}\nprocess={len(proc)}\n",
            encoding='utf-8',
        )
        logging.info(f"Wrote marker: {marker}")
    except Exception as e:
        logging.warning(f"Could not write marker file: {e}")

def detect_slicers(base: Path) -> list[str]:
    targets = slicer_targets_from_base(base)
    return [s for s,cats in targets.items() if any(Path(p).exists() or Path(p).parent.exists() for p in cats.values())]

def headless_install(selected_slicers: list[str], base: Path):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = CACHE_DIR / "profiles.zip"
    extract_dir = CACHE_DIR / "profiles_extracted"
    logging.info(f"Downloading: {GITHUB_ZIP_URL}")
    req = Request(GITHUB_ZIP_URL, headers={"User-Agent":"colorFabb-Installer"})
    with urlopen(req) as r, open(zip_path, 'wb') as f:
        shutil.copyfileobj(r, f)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.testzip()
    digest = sha256_file(zip_path)
    logging.info(f"ZIP sha256 = {digest}")
    if EXPECTED_SHA256 and digest.lower() != EXPECTED_SHA256.lower():
        raise RuntimeError(f"SHA256 mismatch: got {digest}, expected {EXPECTED_SHA256}")
    extract_zip(zip_path, extract_dir)
    fil, proc = collect_repo_profiles_robust(extract_dir)
    targets = slicer_targets_from_base(base)
    targets = {k:v for k,v in targets.items() if k in selected_slicers}
    plan = []
    for it in fil + proc:
        cat = it.get("category", "filament")
        base_path = targets.get(it["slicer"], {}).get(cat)
        if base_path:
            plan.append((it["src"], base_path / it["src"].name))
    logging.info(f"Copy plan: {len(plan)} files")
    added = []
    for src, dst in plan:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        added.append(dst)
        logging.info(f"Copied {src.name} -> {dst}")
    rewrite_installed_list(remove_paths=[], add_paths=added)
    logging.info("Headless install complete.")

# ========= ENTRY =========
def main():
    setup_logging()
    args = parse_args()

    base = Path(args.base) if args.base else appdata_base()
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    if args.uninstall:
        deleted, total = uninstall_installed_files(dry_run=args.dry_run)
        logging.info(f"Uninstall complete: deleted {deleted}/{total}")
        return

    if args.check_download:
        try:
            check_download_only()
            logging.info("Download check OK.")
            if GUI_ENABLED and not args.silent:
                try:
                    app = QApplication.instance() or QApplication(sys.argv)
                    QMessageBox.information(None, APP_DISPLAY_NAME, "Download check OK. Profiles ZIP downloaded and validated.")
                except Exception:
                    pass
            return
        except Exception as e:
            logging.error(f"Download check failed: {e}")
            if GUI_ENABLED and not args.silent:
                try:
                    app = QApplication.instance() or QApplication(sys.argv)
                    QMessageBox.critical(None, APP_DISPLAY_NAME, f"Download check failed:\n{e}")
                except Exception:
                    pass
            raise

    if args.silent:
        selected = args.slicers or (detect_slicers(base) if args.all or not args.slicers else [])
        if not selected:
            selected = ["PrusaSlicer","OrcaSlicer","BambuStudio"]
        logging.info(f"Silent mode: slicers={selected}; base={base}")
        headless_install(selected_slicers=selected, base=base)
        return

    if not GUI_ENABLED:
        print("GUI libraries not available; use --silent or install PySide6")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyleSheet(WELCOME_QSS)  # start geel
    # Zet geel icoon (taskbar duidelijk)
    lp = find_logo()
    if lp:
        try:
            pm = QPixmap(str(lp))
            if not pm.isNull():
                icon = make_yellow_icon(pm)
                app.setWindowIcon(icon)
        except Exception:
            pass

    w = InstallerWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
