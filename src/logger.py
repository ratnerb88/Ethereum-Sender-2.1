import logging
import os
from datetime import datetime
import sys
from .colors import Colors

class ColoredFormatter(logging.Formatter):
    """Кастомный форматтер для цветного логирования"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Цвета для разных уровней логирования
        self.COLORS = {
            logging.DEBUG: Colors.BRIGHT_BLACK,
            logging.INFO: Colors.WHITE,
            logging.WARNING: Colors.YELLOW,
            logging.ERROR: Colors.RED,
            logging.CRITICAL: Colors.BRIGHT_RED + Colors.BOLD,
        }
        
        # Специальные цвета для кастомных сообщений
        self.SUCCESS_COLOR = Colors.BRIGHT_GREEN
        self.SKIP_COLOR = Colors.YELLOW
        self.FAIL_COLOR = Colors.RED
        self.PROGRESS_COLOR = Colors.CYAN
        self.ACCOUNT_COLOR = Colors.BRIGHT_BLUE

    def format(self, record):
        # Сохраняем оригинальное сообщение
        original_msg = record.getMessage()
        
        # Определяем цвет на основе содержимого сообщения
        color = self.COLORS.get(record.levelno, Colors.WHITE)
        
        # Специальная обработка для разных типов сообщений
        if "успешно выполнена" in original_msg or "Отправлено" in original_msg:
            color = self.SUCCESS_COLOR
            record.msg = f"✅ {original_msg}"
        elif "пропущен" in original_msg.lower() or "skip" in original_msg.lower():
            color = self.SKIP_COLOR
            record.msg = f"⏭️ {original_msg}"
        elif "ошибка" in original_msg.lower() or "error" in original_msg.lower() or "не удалась" in original_msg:
            color = self.FAIL_COLOR
            record.msg = f"❌ {original_msg}"
        elif "Аккаунт" in original_msg:
            color = self.ACCOUNT_COLOR
            record.msg = f"👤 {original_msg}"
        elif "Цена газа приемлема" in original_msg:
            color = self.SUCCESS_COLOR
            record.msg = f"⛽ {original_msg}"
        elif "Высокая цена газа" in original_msg:
            color = self.FAIL_COLOR
            record.msg = f"⛽ {original_msg}"
        elif "Прогресс" in original_msg or "%" in original_msg:
            color = self.PROGRESS_COLOR
        else:
            record.msg = original_msg
        
        # Применяем цвет к сообщению
        record.msg = f"{color}{record.msg}{Colors.RESET}"
        
        return super().format(record)

def create_clickable_link(url, text=None, color=Colors.BRIGHT_GREEN):
    """Создает кликабельную ссылку с цветом"""
    if text is None:
        text = url
    
    # Используем ANSI escape последовательности для создания кликабельной ссылки
    return f"{color}{Colors.UNDERLINE}\033]8;;{url}\033\\{text}\033]8;;\033\\{Colors.RESET}"

def setup_logger():
    """Настраивает логгер с цветным выводом"""
    # Создаем директорию для логов
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Настраиваем формат логирования
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Создаем логгер
    logger = logging.getLogger("eth_sender")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    # Создаем обработчик для консоли с цветами
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    
    # Создаем обработчик для файла (без цветов)
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_handler = logging.FileHandler(
        f"{logs_dir}/eth_sender_{current_time}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    
    # Добавляем обработчики
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Добавляем кастомные методы для логирования
    def log_transaction_success(self, account_id, tx_hash, explorer_url, amount, token_symbol, from_address):
        """Логирует успешную транзакцию с кликабельной ссылкой"""
        full_url = f"{explorer_url}{tx_hash}"
        clickable_link = create_clickable_link(full_url, tx_hash, Colors.BRIGHT_GREEN)
        self.info(f"[Аккаунт {account_id}] Транзакция успешно выполнена: {clickable_link}")
        self.info(f"[Аккаунт {account_id}] Отправлено {amount} {token_symbol} с {from_address[:10]}...{from_address[-6:]}")
    
    def log_account_skipped(self, account_id, reason, balance=None):
        """Логирует пропущенный аккаунт"""
        if balance:
            self.warning(f"[Аккаунт {account_id}] {reason}. Баланс: {balance}")
        else:
            self.warning(f"[Аккаунт {account_id}] {reason}")
    
    def log_account_failed(self, account_id, error_msg):
        """Логирует неудачную попытку"""
        self.error(f"[Аккаунт {account_id}] {error_msg}")
    
    def log_progress(self, current, total, success, failed, skipped):
        """Логирует прогресс выполнения"""
        progress_percent = (current / total) * 100
        self.info(f"Прогресс: {current}/{total} ({progress_percent:.1f}%) | ✅ {success} | ❌ {failed} | ⏭️ {skipped}")
    
    # Привязываем методы к логгеру
    logging.Logger.log_transaction_success = log_transaction_success
    logging.Logger.log_account_skipped = log_account_skipped
    logging.Logger.log_account_failed = log_account_failed
    logging.Logger.log_progress = log_progress
    
    return logger