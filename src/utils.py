import yaml
import os
from web3 import Web3

def validate_private_key(private_key):
    """Валидирует приватный ключ"""
    try:
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        if len(private_key) != 66:  # 0x + 64 символа
            return False
        
        # Проверяем, что это валидный hex
        int(private_key, 16)
        return True
    except:
        return False

def validate_address(address):
    """Валидирует Ethereum адрес"""
    try:
        Web3.to_checksum_address(address)
        return True
    except:
        return False

def load_config(config_path="config.yaml"):
    """Загружает конфигурацию из YAML-файла"""
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

def load_private_keys(file_path="data/private_keys.txt"):
    """Загружает приватные ключи из файла с валидацией"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл с приватными ключами не найден: {file_path}")
    
    valid_keys = []
    invalid_keys = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line_num, line in enumerate(file, 1):
            key = line.strip()
            if key:
                if validate_private_key(key):
                    valid_keys.append(key)
                else:
                    invalid_keys.append(f"Строка {line_num}: {key[:10]}...")
    
    if invalid_keys:
        print(f"⚠️ Найдены некорректные приватные ключи:")
        for invalid in invalid_keys:
            print(f"   {invalid}")
        
        if not valid_keys:
            raise ValueError("Не найдено ни одного валидного приватного ключа")
    
    return valid_keys

def load_recipient_addresses(file_path="data/send_to.txt"):
    """Загружает адреса получателей из файла с валидацией"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл с адресами получателей не найден: {file_path}")
    
    valid_addresses = []
    invalid_addresses = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line_num, line in enumerate(file, 1):
            address = line.strip()
            if address:
                if validate_address(address):
                    valid_addresses.append(Web3.to_checksum_address(address))
                else:
                    invalid_addresses.append(f"Строка {line_num}: {address}")
    
    if invalid_addresses:
        print(f"⚠️ Найдены некорректные адреса:")
        for invalid in invalid_addresses:
            print(f"   {invalid}")
        
        if not valid_addresses:
            raise ValueError("Не найдено ни одного валидного адреса")
    
    return valid_addresses

def to_checksum_address(address):
    """Преобразует адрес в формат checksum"""
    return Web3.to_checksum_address(address)