import json
from pathlib import Path
from utils import downloader, installer, logger, gitpack_sync

# Конфигурация путей
BASE_DIR = Path(__file__).resolve().parent
MODLIST_PATH = BASE_DIR / "modlists" / "example_modpack.json"
DOWNLOADS_DIR = BASE_DIR / ".cache" / "downloads"
GITHUB_ZIP_PATH = BASE_DIR / ".cache" / "github_config.zip"
GITHUB_EXTRACT_DIR = BASE_DIR / ".cache" / "github_config"
MODS_DIR = BASE_DIR / "mods"
CACHE_DIR = BASE_DIR / ".cache"
OVERWRITE_DIR = BASE_DIR / "overwrite"
PROFILES_DIR = BASE_DIR / "profiles"

# Инициализация директорий
for path in [DOWNLOADS_DIR, GITHUB_EXTRACT_DIR, MODS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Загрузка модлиста
try:
    with open(MODLIST_PATH, "r", encoding="utf-8") as file:
        modlist = json.load(file)
except Exception as e:
    logger.log(f"Ошибка при чтении модлиста: {e}")
    exit(1)

mods = modlist.get("mods", [])
github_zip_url = modlist.get("github_zip_url")

# Установка модов
for mod in mods:
    mod_name = mod.get("name")
    url = mod.get("url")

    if not mod_name or not url:
        logger.log(f"Пропущен мод без имени или URL: {mod}")
        continue

    zip_path = DOWNLOADS_DIR / f"{mod_name}.zip"

    logger.log(f"Скачиваю: {mod_name}")
    downloader.download_file(url, zip_path)

    logger.log(f"Распаковываю: {mod_name}")
    installer.extract_zip(zip_path, MODS_DIR / mod_name)

    logger.log(f"Генерация meta.ini для: {mod_name}")
    installer.create_meta_ini(mod_name, MODS_DIR)

logger.log("Установка модов завершена.")

# Загрузка и применение GitHub-пака
if github_zip_url:
    try:
        logger.log(f"Загружаю архив модпака: {github_zip_url}")
        gitpack_sync.download_config_zip(github_zip_url, GITHUB_ZIP_PATH)

        logger.log("Распаковываю архив модпака")
        gitpack_sync.extract_config_zip(GITHUB_ZIP_PATH, GITHUB_EXTRACT_DIR)

        logger.log("Применяю конфигурации из модпака")
        gitpack_sync.apply_configs(GITHUB_EXTRACT_DIR, OVERWRITE_DIR, PROFILES_DIR)

        logger.log("Конфигурации успешно применены.")
    except Exception as e:
        logger.log(f"Ошибка при применении пакета с GitHub: {e}")
else:
    logger.log("GitHub URL для модпака не указан.")

# Очистка кэша
installer.clean_cache(CACHE_DIR)
