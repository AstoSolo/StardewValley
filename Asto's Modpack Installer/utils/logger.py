from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

MAX_LOG_FILES = 10  # Максимум файлов логов

def cleanup_old_logs():
    """Удаляет старые лог-файлы, если их больше MAX_LOG_FILES - 1 (без учета текущего)."""
    log_files = sorted(LOGS_DIR.glob("install_*.txt"), key=lambda f: f.stat().st_mtime)
    if len(log_files) >= MAX_LOG_FILES:
        to_delete = log_files[:len(log_files) - MAX_LOG_FILES + 1]  # +1, чтобы оставить место для нового
        for file in to_delete:
            try:
                file.unlink()
                time_prefix = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
                print(f"{time_prefix} Удалён старый лог: {file.name}")
            except Exception as e:
                time_prefix = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
                print(f"{time_prefix} Не удалось удалить {file.name}: {e}")

cleanup_old_logs()

# Генерация имени файла по дате и времени
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = LOGS_DIR / f"install_{timestamp}.txt"

def log(message: str):
    """Записывает сообщение в лог-файл и выводит его в консоль."""
    time_prefix = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    full_message = f"{time_prefix} {message}"

    # Печать в консоль
    print(full_message)

    # Запись в файл
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(full_message + "\n")