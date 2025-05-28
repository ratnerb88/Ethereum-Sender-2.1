# 🚀 ETH Token Sender v2.1

<div align="center">

![Version](https://img.shields.io/badge/version-2.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

**Профессиональный инструмент для массовой отправки ETH токенов**  
**Professional tool for bulk ETH token sending**

[Русский](#русский) | [English](#english)

</div>

---

## Русский

### 📋 Описание

ETH Token Sender v2.1 - это продвинутый инструмент для массовой отправки Ethereum токенов с множеством умных функций оптимизации. Программа позволяет отправлять весь баланс ETH с кошельков, оставляя случайные остатки для безопасности.

### ✨ Основные возможности

- 🎲 **Случайные остатки** - оставляет случайный остаток ETH на каждом кошельке (0.000004-0.000008 ETH)
- ⏰ **Умные задержки** - адаптивные задержки между транзакциями (66-88 секунд)
- 🔀 **Перемешивание кошельков** - с сохранением соответствия отправитель-получатель
- ⛽ **Мониторинг газа** - проверка цены газа перед каждой транзакцией
- 🔄 **Автоповтор** - повторная обработка неудачных аккаунтов
- 📊 **Детальная статистика** - полная отчетность по всем операциям
- 🎨 **Цветное логирование** - с кликабельными ссылками на Etherscan
- 💾 **Сохранение результатов** - автоматическое сохранение в JSON файлы

### 🛠️ Технические особенности

- **Кэширование газа** - оптимизация RPC запросов (30 секунд)
- **Валидация данных** - проверка приватных ключей и адресов
- **Обработка ошибок** - устойчивость к сетевым проблемам
- **Интерактивное меню** - удобный пользовательский интерфейс
- **JSON сериализация** - корректное сохранение результатов

### 📦 Установка

1. **Клонируйте репозиторий:**
git clone https://github.com/yourusername/eth-token-sender.git
cd eth-token-sender

2. **Установите зависимости:**
pip install -r requirements.txt


### ⚙️ Настройка

1. **Настройте config.yaml:**
   - Укажите RPC URL для Ethereum
   - Настройте параметры газа и задержек
   - Установите диапазон случайных остатков

2. **Подготовьте файлы данных:**
   - `data/private_keys.txt` - приватные ключи (по одному на строку)
   - `data/send_to.txt` - адреса получателей (по одному на строку)

### 🚀 Использование

python main.py


Выберите нужную опцию в интерактивном меню:
- **1** - Запустить отправку токенов
- **2** - Показать текущий Gwei
- **3** - Выход

### 📁 Структура проекта

eth-token-sender/
├── main.py # Главный файл программы
├── config.yaml # Файл конфигурации
├── requirements.txt # Зависимости Python
├── src/ # Исходный код
│ ├── init.py
│ ├── colors.py # Цветовые коды
│ ├── logger.py # Система логирования
│ ├── sender.py # Основная логика отправки
│ └── utils.py # Вспомогательные функции
├── data/ # Входные данные
│ ├── private_keys.txt # Приватные ключи
│ └── send_to.txt # Адреса получателей
├── results/ # Результаты выполнения
├── logs/ # Файлы логов
└── README.md


### ⚠️ Важные замечания

- **Безопасность**: Никогда не делитесь приватными ключами
- **Тестирование**: Сначала протестируйте на тестовой сети
- **Газ**: Следите за ценой газа для экономии средств
- **Резервные копии**: Делайте резервные копии важных данных

### 📊 Пример конфигурации

network:
rpc_url: "https://ethereum-rpc.publicnode.com"
chain_id: 1

transaction:
gas_limit: 21000
use_dynamic_gas: true
random_remaining_balance_eth:
min: 0.000004
max: 0.000008

execution:
shuffle_wallets: true
random_delay_range:
min: 66
max: 88
skipped_account_delay: 2

gas_monitor:
enabled: true
max_gas_price_gwei: 1


### 🎯 Особенности v2.1

- **Проверка газа перед транзакцией** - максимальная эффективность
- **Короткие задержки для пропущенных** - 2 секунды вместо обычных 66-88
- **Кэширование цены газа** - уменьшение RPC запросов
- **Улучшенная валидация** - проверка всех входных данных

### 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста:

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

### 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

### 📞 Поддержка

Если у вас есть вопросы или проблемы:
- Создайте Issue в GitHub
- Проверьте существующие Issues
- Изучите документацию

---

## English

### 📋 Description

ETH Token Sender v2.1 is an advanced tool for bulk Ethereum token sending with multiple smart optimization features. The program allows sending entire ETH balance from wallets while leaving random remainders for security.

### ✨ Key Features

- 🎲 **Random Remainders** - leaves random ETH remainder on each wallet (0.000004-0.000008 ETH)
- ⏰ **Smart Delays** - adaptive delays between transactions (66-88 seconds)
- 🔀 **Wallet Shuffling** - preserving sender-recipient correspondence
- ⛽ **Gas Monitoring** - gas price check before each transaction
- 🔄 **Auto Retry** - reprocessing failed accounts
- 📊 **Detailed Statistics** - comprehensive reporting of all operations
- 🎨 **Colored Logging** - with clickable Etherscan links
- 💾 **Result Saving** - automatic saving to JSON files

### 🛠️ Technical Features

- **Gas Caching** - RPC request optimization (30 seconds)
- **Data Validation** - private key and address verification
- **Error Handling** - resilience to network issues
- **Interactive Menu** - user-friendly interface
- **JSON Serialization** - proper result saving

### 📦 Installation

1. **Clone the repository:**
git clone https://github.com/yourusername/eth-token-sender.git
cd eth-token-sender


2. **Install dependencies:**
pip install -r requirements.txt

3. **Create necessary folders:**
mkdir data results logs


### ⚙️ Configuration

1. **Configure config.yaml:**
   - Set RPC URL for Ethereum
   - Configure gas and delay parameters
   - Set random remainder range

2. **Prepare data files:**
   - `data/private_keys.txt` - private keys (one per line)
   - `data/send_to.txt` - recipient addresses (one per line)

### 🚀 Usage

python main.py


Choose the desired option from the interactive menu:
- **1** - Start token sending
- **2** - Show current Gwei
- **3** - Exit

### 📁 Project Structure

eth-token-sender/
├── main.py # Main program file
├── config.yaml # Configuration file
├── requirements.txt # Python dependencies
├── src/ # Source code
│ ├── init.py
│ ├── colors.py # Color codes
│ ├── logger.py # Logging system
│ ├── sender.py # Main sending logic
│ └── utils.py # Utility functions
├── data/ # Input data
│ ├── private_keys.txt # Private keys
│ └── send_to.txt # Recipient addresses
├── results/ # Execution results
├── logs/ # Log files
└── README.md

### ⚠️ Important Notes

- **Security**: Never share private keys
- **Testing**: Test on testnet first
- **Gas**: Monitor gas prices to save costs
- **Backups**: Make backups of important data

### 📊 Example Configuration

network:
rpc_url: "https://ethereum-rpc.publicnode.com"
chain_id: 1

transaction:
gas_limit: 21000
use_dynamic_gas: true
random_remaining_balance_eth:
min: 0.000004
max: 0.000008

execution:
shuffle_wallets: true
random_delay_range:
min: 66
max: 88
skipped_account_delay: 2

gas_monitor:
enabled: true
max_gas_price_gwei: 1

### 🎯 v2.1 Features

- **Gas check before transaction** - maximum efficiency
- **Short delays for skipped** - 2 seconds instead of usual 66-88
- **Gas price caching** - reduced RPC requests
- **Enhanced validation** - verification of all input data

### 🤝 Contributing

We welcome contributions to the project! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Create a Pull Request

### 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### 📞 Support

If you have questions or issues:
- Create an Issue on GitHub
- Check existing Issues
- Review the documentation

---

<div align="center">

**Made with ❤️ for the Ethereum community**

⭐ **Star this repo if you find it useful!** ⭐

</div>