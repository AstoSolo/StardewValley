import sys
import json
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QMessageBox,
)

# Используем те же utils, что и в CLI, чтобы избежать циклического импорта main.py
from utils import downloader, installer, logger, gitpack_sync

# Пути такие же, как в main.py
BASE_DIR = Path(__file__).resolve().parent
LAUNCHER_DIR = BASE_DIR.parent
DOWNLOADS_DIR = BASE_DIR / ".cache" / "downloads"
GITHUB_ZIP_PATH = BASE_DIR / ".cache" / "github_config.zip"
GITHUB_EXTRACT_DIR = BASE_DIR / ".cache" / "github_config"
MODS_DIR = LAUNCHER_DIR / "mods"
CACHE_DIR = BASE_DIR / ".cache"
OVERWRITE_DIR = LAUNCHER_DIR / "overwrite"
PROFILES_DIR = LAUNCHER_DIR / "profiles"

for path in [DOWNLOADS_DIR, GITHUB_EXTRACT_DIR, MODS_DIR]:
    path.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    config_path = BASE_DIR / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении конфигурации: {e}")
        QMessageBox.critical(None, "Ошибка", f"Не удалось прочитать config.json: {e}")
        sys.exit(1)


def download_modlist(modpack: Dict[str, Any]) -> Dict[str, Any]:
    modlist_url = modpack.get("modlist_url")
    if not modlist_url:
        raise RuntimeError(f"URL модлиста не указан для модпака: {modpack['name']}")

    modlist_path = DOWNLOADS_DIR / f"{modpack['slug']}_modlist.json"

    logger.info(f"Скачиваю модлист для {modpack['name']}...")
    downloader.download_file(modlist_url, modlist_path)
    with open(modlist_path, "r", encoding="utf-8") as f:
        return json.load(f)


class InstallWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, modpack: Dict[str, Any], sync_configs: bool):
        super().__init__()
        self.modpack = modpack
        self.sync_configs = sync_configs

    def run(self):
        try:
            self.status.emit("Загружаю модлист...")
            modlist = download_modlist(self.modpack)
            mods = modlist.get("mods", [])
            github_zip_url = modlist.get("github_zip_url")

            total = max(1, len(mods))
            self.status.emit(f"Установка модов ({len(mods)})...")
            logger.info(f"Начинаю установку {len(mods)} модов...")

            successful = 0
            for i, mod in enumerate(mods, 1):
                mod_name = mod.get("name")
                url = mod.get("url")

                self.progress.emit(int((i - 1) / total * 80))
                self.status.emit(f"Скачиваю: {mod_name}")

                if not mod_name or not url:
                    logger.warning(f"Пропущен мод без имени или URL: {mod}")
                    continue

                # Определяем расширение из URL (поддержка .zip и .7z)
                ext = Path(urlparse(url).path).suffix.lower() or ".zip"
                archive_path = DOWNLOADS_DIR / f"{mod_name}{ext}"
                downloader.download_file(url, archive_path)

                self.status.emit(f"Распаковываю: {mod_name}")
                installer.extract_archive(archive_path, MODS_DIR / mod_name)

                installer.create_meta_ini(mod_name, MODS_DIR)
                successful += 1
                self.progress.emit(int((i) / total * 80))

            logger.success(f"Успешно установлено модов: {successful}")

            if self.sync_configs:
                self.progress.emit(90)
                self.status.emit("Синхронизация конфигураций...")
                if github_zip_url:
                    gitpack_sync.download_config_zip(github_zip_url, GITHUB_ZIP_PATH)
                    gitpack_sync.extract_config_zip(GITHUB_ZIP_PATH, GITHUB_EXTRACT_DIR)
                    gitpack_sync.apply_configs(GITHUB_EXTRACT_DIR, OVERWRITE_DIR, PROFILES_DIR)
                    logger.success("Конфигурации успешно применены!")
                else:
                    logger.warning("GitHub URL для модпака не указан.")

            self.progress.emit(95)
            self.status.emit("Очистка кэша...")
            installer.clean_cache(CACHE_DIR)

            self.progress.emit(100)
            self.status.emit("Готово")
            self.finished.emit(True, "Установка завершена успешно!")
        except Exception as e:
            logger.error(f"Ошибка при установке: {e}")
            self.finished.emit(False, f"Ошибка: {e}")


class ModpackInstallerGUI(QMainWindow):
    def __init__(self, modpacks, base_dir: Path | str | None = None):
        super().__init__()
        self.modpacks = modpacks
        self.base_dir = Path(base_dir) if base_dir else BASE_DIR
        self.worker: InstallWorker | None = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Установщик модпаков Stardew Valley")
        self.resize(700, 520)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("Выберите модпак для установки:")
        title.setStyleSheet("font-size:16px;font-weight:bold;margin:8px 0;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        for mp in self.modpacks:
            self.list_widget.addItem(mp["name"])
        layout.addWidget(self.list_widget)

        self.chk_sync = QCheckBox("Синхронизировать конфигурации с GitHub")
        self.chk_sync.setChecked(True)
        layout.addWidget(self.chk_sync)

        self.btn_install = QPushButton("Установить выбранный модпак")
        self.btn_install.clicked.connect(self._on_install_clicked)
        layout.addWidget(self.btn_install)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("Готов к установке")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)

    def _set_busy(self, busy: bool):
        self.list_widget.setEnabled(not busy)
        self.chk_sync.setEnabled(not busy)
        self.btn_install.setEnabled(not busy)
        self.progress.setVisible(busy)
        if busy:
            self.progress.setValue(0)

    def _on_install_clicked(self):
        items = self.list_widget.selectedItems()
        if not items:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите модпак")
            return
        name = items[0].text()
        modpack = next((m for m in self.modpacks if m["name"] == name), None)
        if not modpack:
            QMessageBox.critical(self, "Ошибка", "Выбранный модпак не найден")
            return

        if QMessageBox.question(
            self,
            "Подтверждение",
            f"Установить модпак \"{name}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True)
        self.worker = InstallWorker(modpack, self.chk_sync.isChecked())
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.status_lbl.setText)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success: bool, msg: str):
        self._set_busy(False)
        if success:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)


def launch_gui(modpacks, base_dir: Path | str):
    app = QApplication(sys.argv)
    window = ModpackInstallerGUI(modpacks, base_dir)
    window.show()
    sys.exit(app.exec())
