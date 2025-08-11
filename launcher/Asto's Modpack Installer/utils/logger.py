import sys
from pathlib import Path
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4

class Colors:
    """ANSI цветовые коды для консоли"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Цвета текста
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Яркие цвета
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'

class Logger:
    """Улучшенный логгер с поддержкой уровней и цветов"""
    
    def __init__(self, min_level=LogLevel.INFO, enable_colors=True):
        self.min_level = min_level
        self.enable_colors = enable_colors and sys.stdout.isatty()
        
        # Настройка путей
        self.base_dir = Path(__file__).resolve().parent.parent
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Настройки
        self.max_log_files = 5
        
        # Очистка старых логов
        self._cleanup_old_logs()
        
        # Создание файла лога
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.logs_dir / f"install_{timestamp}.txt"
        
        # Символы для разных уровней
        self.level_symbols = {
            LogLevel.DEBUG: "[DEBUG]",
            LogLevel.INFO: "[INFO]",
            LogLevel.SUCCESS: "[OK]",
            LogLevel.WARNING: "[WARN]",
            LogLevel.ERROR: "[ERROR]"
        }
        
        # Цвета для разных уровней
        self.level_colors = {
            LogLevel.DEBUG: Colors.DIM + Colors.CYAN,
            LogLevel.INFO: Colors.BLUE,
            LogLevel.SUCCESS: Colors.BRIGHT_GREEN,
            LogLevel.WARNING: Colors.BRIGHT_YELLOW,
            LogLevel.ERROR: Colors.BRIGHT_RED
        }
    
    def _cleanup_old_logs(self):
        """Удаляет старые лог-файлы"""
        log_files = sorted(self.logs_dir.glob("install_*.txt"), key=lambda f: f.stat().st_mtime)
        if len(log_files) >= self.max_log_files:
            to_delete = log_files[:len(log_files) - self.max_log_files + 1]
            for file in to_delete:
                try:
                    file.unlink()
                except Exception:
                    pass  # Игнорируем ошибки при удалении старых логов
    
    def _format_message(self, message: str, level: LogLevel, use_colors: bool = True) -> str:
        """Форматирует сообщение с временной меткой и уровнем"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = self.level_symbols.get(level, "•")
        
        if use_colors and self.enable_colors:
            color = self.level_colors.get(level, "")
            return f"{Colors.DIM}[{timestamp}]{Colors.RESET} {color}{symbol} {message}{Colors.RESET}"
        else:
            return f"[{timestamp}] {symbol} {message}"
    
    def _write_to_file(self, message: str, level: LogLevel):
        """Записывает сообщение в файл"""
        try:
            formatted_message = self._format_message(message, level, use_colors=False)
            with open(self.log_file, "a", encoding="utf-8") as file:
                file.write(formatted_message + "\n")
        except Exception:
            pass  # Игнорируем ошибки записи в файл
    
    def _log(self, message: str, level: LogLevel):
        """Основной метод логирования"""
        if level.value < self.min_level.value:
            return
        
        # Форматируем и выводим в консоль
        formatted_message = self._format_message(message, level)
        print(formatted_message)
        
        # Записываем в файл
        self._write_to_file(message, level)
    
    def debug(self, message: str):
        """Отладочное сообщение"""
        self._log(message, LogLevel.DEBUG)
    
    def info(self, message: str):
        """Информационное сообщение"""
        self._log(message, LogLevel.INFO)
    
    def success(self, message: str):
        """Сообщение об успехе"""
        self._log(message, LogLevel.SUCCESS)
    
    def warning(self, message: str):
        """Предупреждение"""
        self._log(message, LogLevel.WARNING)
    
    def error(self, message: str):
        """Ошибка"""
        self._log(message, LogLevel.ERROR)
    
    def log(self, message: str):
        """Обратная совместимость - обычное info сообщение"""
        self.info(message)
    
    def header(self, message: str):
        """Заголовок секции"""
        if self.enable_colors:
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*50}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{message.center(50)}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*50}{Colors.RESET}\n")
        else:
            print(f"\n{'='*50}")
            print(f"{message.center(50)}")
            print(f"{'='*50}\n")
        
        # Записываем в файл без цветов
        self._write_to_file(f"\n{'='*50}", LogLevel.INFO)
        self._write_to_file(message.center(50), LogLevel.INFO)
        self._write_to_file(f"{'='*50}\n", LogLevel.INFO)
    
    def progress(self, current: int, total: int, item_name: str = ""):
        """Показывает прогресс выполнения"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        if self.enable_colors:
            progress_msg = f"{Colors.BRIGHT_BLUE}[{bar}] {percentage:.1f}% ({current}/{total}){Colors.RESET}"
            if item_name:
                progress_msg += f" {Colors.DIM}{item_name}{Colors.RESET}"
        else:
            progress_msg = f"[{bar}] {percentage:.1f}% ({current}/{total})"
            if item_name:
                progress_msg += f" {item_name}"
        
        print(f"\r{progress_msg}", end="", flush=True)
        
        # Если это последний элемент, переходим на новую строку
        if current >= total:
            print()

# Создаем глобальный экземпляр логгера
_logger = Logger()

# Экспортируем функции для обратной совместимости
def log(message: str):
    """Обратная совместимость"""
    _logger.log(message)

def debug(message: str):
    """Отладочное сообщение"""
    _logger.debug(message)

def info(message: str):
    """Информационное сообщение"""
    _logger.info(message)

def success(message: str):
    """Сообщение об успехе"""
    _logger.success(message)

def warning(message: str):
    """Предупреждение"""
    _logger.warning(message)

def error(message: str):
    """Ошибка"""
    _logger.error(message)

def header(message: str):
    """Заголовок секции"""
    _logger.header(message)

def progress(current: int, total: int, item_name: str = ""):
    """Показывает прогресс выполнения"""
    _logger.progress(current, total, item_name)