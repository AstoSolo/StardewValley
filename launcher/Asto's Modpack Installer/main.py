import json
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse
from utils import downloader, installer, logger, gitpack_sync

def load_config():
    """Загружает конфигурацию с доступными модпаками"""
    config_path = BASE_DIR / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Ошибка при чтении конфигурации: {e}")
        exit(1)

def select_modpack(modpacks):
    """Позволяет пользователю выбрать модпак из списка"""
    if not modpacks:
        logger.error("Нет доступных модпаков в конфигурации.")
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
        install_mods = input("Установить моды? (Y/N): ").lower().strip()
        if install_mods in ['y', 'yes', 'д', 'да']:
            install_mods = True
            break
        elif install_mods in ['n', 'no', 'н', 'нет']:
            install_mods = False
            break
        else:
            print("Пожалуйста, введите Y/N (да/нет)")
    
    while True:
        sync_configs = input("Загрузить архив конфигов с GitHub? (Y/N): ").lower().strip()
        if sync_configs in ['y', 'yes', 'д', 'да']:
            sync_configs = True
            break
        elif sync_configs in ['n', 'no', 'н', 'нет']:
            sync_configs = False
            break
        else:
            print("Пожалуйста, введите Y/N (да/нет)")
    
    return install_mods, sync_configs

def download_modlist(modpack):
    """Скачивает модлист для выбранного модпака"""
    modlist_url = modpack.get("modlist_url")
    if not modlist_url:
        logger.error(f"URL модлиста не указан для модпака: {modpack['name']}")
        exit(1)
    
    modlist_path = DOWNLOADS_DIR / f"{modpack['slug']}_modlist.json"
    
    logger.info(f"Скачиваю модлист для {modpack['name']}...")
    try:
        downloader.download_file(modlist_url, modlist_path)
        with open(modlist_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Ошибка при скачивании или чтении модлиста: {e}")
        exit(1)

def install_mods(mods):
    """Устанавливает моды из списка"""
    logger.info(f"Начинаю установку {len(mods)} модов...")
    
    successful_installs = 0
    failed_installs = 0
    
    for i, mod in enumerate(mods, 1):
        mod_name = mod.get("name")
        url = mod.get("url")

        # Показываем прогресс
        logger.progress(i - 1, len(mods), f"Подготовка: {mod_name}")

        if not mod_name or not url:
            logger.warning(f"Пропущен мод без имени или URL: {mod}")
            failed_installs += 1
            continue

        # Определяем расширение из URL (поддержка .zip и .7z)
        ext = Path(urlparse(url).path).suffix.lower() or ".zip"
        archive_path = DOWNLOADS_DIR / f"{mod_name}{ext}"

        try:
            logger.progress(i - 1, len(mods), f"Скачиваю: {mod_name}")
            downloader.download_file(url, archive_path)

            logger.progress(i - 1, len(mods), f"Распаковываю: {mod_name}")
            installer.extract_archive(archive_path, MODS_DIR / mod_name)

            logger.progress(i - 1, len(mods), f"Создаю meta.ini: {mod_name}")
            installer.create_meta_ini(mod_name, MODS_DIR)
            
            successful_installs += 1
            logger.progress(i, len(mods), f"✓ {mod_name}")
        except Exception as e:
            logger.error(f"Ошибка при установке мода {mod_name}: {e}")
            failed_installs += 1
            logger.progress(i, len(mods), f"✗ {mod_name}")
            continue

    # Финальная статистика
    if successful_installs > 0:
        logger.success(f"Успешно установлено модов: {successful_installs}")
    if failed_installs > 0:
        logger.warning(f"Не удалось установить модов: {failed_installs}")
    
    logger.info("Установка модов завершена.")

def sync_github_configs(github_zip_url):
    """Синхронизирует конфигурации с GitHub"""
    if not github_zip_url:
        logger.warning("GitHub URL для модпака не указан.")
        return
    
    try:
        logger.info(f"Загружаю архив конфигураций с GitHub...")
        gitpack_sync.download_config_zip(github_zip_url, GITHUB_ZIP_PATH)

        logger.info("Распаковываю архив конфигураций...")
        gitpack_sync.extract_config_zip(GITHUB_ZIP_PATH, GITHUB_EXTRACT_DIR)

        logger.info("Применяю конфигурации модпака...")
        gitpack_sync.apply_configs(GITHUB_EXTRACT_DIR, OVERWRITE_DIR, PROFILES_DIR)

        logger.success("Конфигурации успешно применены!")
    except Exception as e:
        logger.error(f"Ошибка при применении пакета с GitHub: {e}")

# Конфигурация путей
BASE_DIR = Path(__file__).resolve().parent
LAUNCHER_DIR = BASE_DIR.parent  # Корневая папка launcher
DOWNLOADS_DIR = BASE_DIR / ".cache" / "downloads"
GITHUB_ZIP_PATH = BASE_DIR / ".cache" / "github_config.zip"
GITHUB_EXTRACT_DIR = BASE_DIR / ".cache" / "github_config"
MODS_DIR = LAUNCHER_DIR / "mods"
CACHE_DIR = BASE_DIR / ".cache"
OVERWRITE_DIR = LAUNCHER_DIR / "overwrite"
PROFILES_DIR = LAUNCHER_DIR / "profiles"

# Инициализация директорий
for path in [DOWNLOADS_DIR, GITHUB_EXTRACT_DIR, MODS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(description="Asto's Modpack Installer")
    parser.add_argument("--gui", action="store_true", help="Запустить графический интерфейс (PyQt6)")
    args = parser.parse_args()

    logger.header("Asto's Modpack Installer")

    # Загрузка конфигурации
    config = load_config()
    modpacks = config.get("modpacks", [])

    if args.gui:
        try:
            from gui import launch_gui
        except Exception as e:
            logger.error(f"Не удалось загрузить GUI: {e}. Убедитесь, что установлен PyQt6 и файл gui.py присутствует.")
            sys.exit(1)
        # Запуск GUI и выход после закрытия окна
        launch_gui(modpacks, BASE_DIR)
        return

    # CLI режим (по умолчанию)
    selected_modpack = select_modpack(modpacks)
    install_mods_enabled, sync_configs_enabled = get_user_preferences()
    modlist = download_modlist(selected_modpack)
    mods = modlist.get("mods", [])
    github_zip_url = modlist.get("github_zip_url")

    if install_mods_enabled:
        install_mods(mods)
    else:
        logger.info("Установка модов пропущена по выбору пользователя.")

    if sync_configs_enabled:
        sync_github_configs(github_zip_url)
    else:
        logger.info("Синхронизация конфигураций пропущена по выбору пользователя.")

    installer.clean_cache(CACHE_DIR)
    logger.success("Процесс установки завершен!")

if __name__ == "__main__":
    main()
