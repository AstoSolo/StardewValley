import json
from pathlib import Path
from utils import downloader, installer, logger

BASE_DIR = Path(__file__).resolve().parent
MODLIST_PATH = BASE_DIR / "modlists" / "example.json"
DOWNLOADS_DIR = BASE_DIR / ".cache" / "downloads"
EXTRACT_DIR = BASE_DIR / ".." / "mods"
CACHE_DIR = BASE_DIR / ".cache"

DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

with open(MODLIST_PATH, "r", encoding="utf-8") as file:
    mods = json.load(file)

for mod in mods:
    mod_name = mod["name"]
    url = mod["url"]
    zip_path = DOWNLOADS_DIR / f"{mod_name}.zip"

    logger.log(f"Скачиваю: {mod_name}")
    downloader.download_file(url, zip_path)

    logger.log(f"Распаковываю: {mod_name}")
    installer.extract_zip(zip_path, EXTRACT_DIR / mod_name)

    logger.log(f"Генерация meta.ini для: {mod_name}")
    installer.create_meta_ini(mod_name, EXTRACT_DIR)

    logger.log("Установка завершена.")

installer.clean_cache(CACHE_DIR)