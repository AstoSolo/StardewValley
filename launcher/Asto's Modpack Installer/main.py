import json
from pathlib import Path
from utils import downloader, installer, logger, gitpack_sync

def load_config():
    """Загружает конфигурацию с доступными модпаками"""
    config_path = BASE_DIR / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.log(f"Ошибка при чтении конфигурации: {e}")
        exit(1)

def select_modpack(modpacks):
    """Позволяет пользователю выбрать модпак из списка"""
    if not modpacks:
        logger.log("Нет доступных модпаков в конфигурации.")
        exit(1)
    
    print("\nДоступные модпаки:")
    for i, modpack in enumerate(modpacks, 1):
        print(f"{i}. {modpack['name']}")
    
    while True:
        try:
            choice = int(input(f"\nВыберите модпак (1-{len(modpacks)}): ")) - 1
            if 0 <= choice < len(modpacks):
                return modpacks[choice]
            else:
                print(f"Пожалуйста, введите число от 1 до {len(modpacks)}")
        except ValueError:
            print("Пожалуйста, введите корректное число")

def get_user_preferences():
    """Получает настройки пользователя для установки модов и синхронизации конфигов"""
    print("\nНастройки установки:")
    
    while True:
        install_mods = input("Устанавливать моды? (y/n): ").lower().strip()
        if install_mods in ['y', 'yes', 'д', 'да']:
            install_mods = True
            break
        elif install_mods in ['n', 'no', 'н', 'нет']:
            install_mods = False
            break
        else:
            print("Пожалуйста, введите y/n (да/нет)")
    
    while True:
        sync_configs = input("Синхронизировать конфигурации с GitHub? (y/n): ").lower().strip()
        if sync_configs in ['y', 'yes', 'д', 'да']:
            sync_configs = True
            break
        elif sync_configs in ['n', 'no', 'н', 'нет']:
            sync_configs = False
            break
        else:
            print("Пожалуйста, введите y/n (да/нет)")
    
    return install_mods, sync_configs

def download_modlist(modpack):
    """Скачивает модлист для выбранного модпака"""
    modlist_url = modpack.get("modlist_url")
    if not modlist_url:
        logger.log(f"URL модлиста не указан для модпака: {modpack['name']}")
        exit(1)
    
    modlist_path = DOWNLOADS_DIR / f"{modpack['slug']}_modlist.json"
    
    logger.log(f"Скачиваю модлист для {modpack['name']}...")
    try:
        downloader.download_file(modlist_url, modlist_path)
        with open(modlist_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.log(f"Ошибка при скачивании или чтении модлиста: {e}")
        exit(1)

def install_mods(mods):
    """Устанавливает моды из списка"""
    logger.log("Начинаю установку модов...")
    
    for mod in mods:
        mod_name = mod.get("name")
        url = mod.get("url")

        if not mod_name or not url:
            logger.log(f"Пропущен мод без имени или URL: {mod}")
            continue

        zip_path = DOWNLOADS_DIR / f"{mod_name}.zip"

        logger.log(f"Скачиваю: {mod_name}")
        try:
            downloader.download_file(url, zip_path)

            logger.log(f"Распаковываю: {mod_name}")
            installer.extract_zip(zip_path, MODS_DIR / mod_name)

            logger.log(f"Генерация meta.ini для: {mod_name}")
            installer.create_meta_ini(mod_name, MODS_DIR)
        except Exception as e:
            logger.log(f"Ошибка при установке мода {mod_name}: {e}")
            continue

    logger.log("Установка модов завершена.")

def sync_github_configs(github_zip_url):
    """Синхронизирует конфигурации с GitHub"""
    if not github_zip_url:
        logger.log("GitHub URL для модпака не указан.")
        return
    
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

# Конфигурация путей
BASE_DIR = Path(__file__).resolve().parent
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

def main():
    """Основная функция программы"""
    logger.log("=== Asto's Modpack Installer ===")
    
    # Загрузка конфигурации
    config = load_config()
    modpacks = config.get("modpacks", [])
    
    # Выбор модпака
    selected_modpack = select_modpack(modpacks)
    logger.log(f"Выбран модпак: {selected_modpack['name']}")
    
    # Получение настроек пользователя
    install_mods_enabled, sync_configs_enabled = get_user_preferences()
    
    # Скачивание модлиста
    modlist = download_modlist(selected_modpack)
    mods = modlist.get("mods", [])
    github_zip_url = modlist.get("github_zip_url")
    
    # Установка модов (если включено)
    if install_mods_enabled:
        install_mods(mods)
    else:
        logger.log("Установка модов пропущена по выбору пользователя.")
    
    # Синхронизация конфигураций (если включено)
    if sync_configs_enabled:
        sync_github_configs(github_zip_url)
    else:
        logger.log("Синхронизация конфигураций пропущена по выбору пользователя.")
    
    # Очистка кэша
    installer.clean_cache(CACHE_DIR)
    
    logger.log("Процесс установки завершен!")

if __name__ == "__main__":
    main()
