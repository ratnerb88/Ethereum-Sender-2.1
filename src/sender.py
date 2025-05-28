import asyncio
from web3 import Web3
from web3.middleware import geth_poa_middleware
import time
from datetime import datetime, timedelta
import json
import os
import random
from decimal import Decimal

class TokenSender:
    """Оптимизированный класс для отправки ETH со случайными остатками и задержками"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.w3 = self._setup_web3()
        self.semaphore = asyncio.Semaphore(config['execution']['max_concurrent'])
        self.last_gas_notification = None
        
        # Кэширование для оптимизации
        self._gas_price_cache = None
        self._gas_price_cache_time = None
        self._cache_duration = 30  # Кэшируем цену газа на 30 секунд
        
        # Статистика
        self.stats = {
            'successful_accounts': [],
            'failed_accounts': [],
            'skipped_accounts': [],
            'total_sent': 0,
            'total_gas_used': 0,
            'total_delay_time': 0,
            'start_time': None,
            'end_time': None
        }

    def _setup_web3(self):
        """Настраивает подключение к Web3"""
        w3 = Web3(Web3.HTTPProvider(self.config['network']['rpc_url']))
        
        if self.config['network']['chain_id'] != 1:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            raise ConnectionError(f"Не удалось подключиться к RPC: {self.config['network']['rpc_url']}")
        
        self.logger.info(f"Успешное подключение к RPC: {self.config['network']['rpc_url']}")
        return w3

    def shuffle_wallets_data(self, private_keys, recipient_addresses):
        """Перемешивает кошельки с сохранением соответствия отправитель-получатель"""
        if not self.config.get('execution', {}).get('shuffle_wallets', False):
            return private_keys, recipient_addresses
        
        # Создаем пары (приватный_ключ, адрес_получателя)
        wallet_pairs = list(zip(private_keys, recipient_addresses))
        
        # Перемешиваем пары
        random.shuffle(wallet_pairs)
        
        # Разделяем обратно на два списка
        shuffled_private_keys, shuffled_recipient_addresses = zip(*wallet_pairs)
        
        self.logger.info("🔀 Кошельки перемешаны (с сохранением соответствия отправитель-получатель)")
        
        return list(shuffled_private_keys), list(shuffled_recipient_addresses)

    def get_random_delay(self):
        """Возвращает случайную задержку между транзакциями"""
        min_delay = self.config['execution']['random_delay_range']['min']
        max_delay = self.config['execution']['random_delay_range']['max']
        return random.uniform(min_delay, max_delay)

    def get_skipped_delay(self):
        """Возвращает задержку для пропущенных аккаунтов"""
        return self.config['execution'].get('skipped_account_delay', 2)

    def get_random_remaining_balance_wei(self):
        """Возвращает случайный остаток в wei"""
        min_remaining = self.config['transaction']['random_remaining_balance_eth']['min']
        max_remaining = self.config['transaction']['random_remaining_balance_eth']['max']
        random_remaining_eth = random.uniform(min_remaining, max_remaining)
        return self.w3.to_wei(random_remaining_eth, 'ether'), random_remaining_eth

    def get_current_gas_price(self):
        """Получает текущую цену газа из сети с кэшированием"""
        current_time = time.time()
        
        # Проверяем кэш
        if (self._gas_price_cache is not None and 
            self._gas_price_cache_time is not None and 
            current_time - self._gas_price_cache_time < self._cache_duration):
            return self._gas_price_cache
        
        try:
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price, 'gwei')
            
            # Обновляем кэш
            self._gas_price_cache = (gas_price, gas_price_gwei)
            self._gas_price_cache_time = current_time
            
            return gas_price, gas_price_gwei
        except Exception as e:
            self.logger.error(f"Ошибка при получении цены газа: {str(e)}")
            return None, None

    async def wait_for_acceptable_gas_price(self, account_id):
        """Ждет пока цена газа не станет приемлемой (вызывается перед каждой транзакцией)"""
        if not self.config.get('gas_monitor', {}).get('enabled', False):
            return True

        max_gas_gwei = self.config['gas_monitor']['max_gas_price_gwei']
        check_interval = self.config['gas_monitor']['check_interval']
        max_wait_time = self.config['gas_monitor']['max_wait_time']
        notification_interval = self.config['gas_monitor']['notification_interval']
        
        start_time = datetime.now()
        
        while True:
            gas_price_wei, gas_price_gwei = self.get_current_gas_price()
            
            if gas_price_wei is None:
                self.logger.warning(f"[Аккаунт {account_id}] Не удалось получить цену газа, продолжаем без проверки")
                return True
            
            if gas_price_gwei <= max_gas_gwei:
                self.logger.info(f"[Аккаунт {account_id}] Цена газа приемлема: {gas_price_gwei:.2f} Gwei (лимит: {max_gas_gwei} Gwei)")
                return True
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            if elapsed_time >= max_wait_time:
                self.logger.warning(f"[Аккаунт {account_id}] ⏰ Достигнуто максимальное время ожидания ({max_wait_time/60:.1f} минут)")
                self.logger.warning(f"[Аккаунт {account_id}] Продолжаем с текущей ценой газа: {gas_price_gwei:.2f} Gwei")
                return True
            
            now = datetime.now()
            if (self.last_gas_notification is None or 
                (now - self.last_gas_notification).total_seconds() >= notification_interval):
                
                remaining_time = max_wait_time - elapsed_time
                self.logger.warning(f"[Аккаунт {account_id}] Высокая цена газа: {gas_price_gwei:.2f} Gwei (лимит: {max_gas_gwei} Gwei)")
                self.logger.warning(f"[Аккаунт {account_id}] ⏳ Ожидаем снижения... Осталось времени: {remaining_time/60:.1f} минут")
                self.last_gas_notification = now
            else:
                # Показываем текущий газ при каждой проверке
                remaining_time = max_wait_time - elapsed_time
                self.logger.info(f"[Аккаунт {account_id}] ⛽ Текущий газ: {gas_price_gwei:.2f} Gwei | Лимит: {max_gas_gwei} Gwei | Осталось времени: {remaining_time/60:.1f} минут")
            
            await asyncio.sleep(check_interval)

    def get_gas_price(self):
        """Получает рекомендуемую цену газа"""
        if self.config['transaction'].get('use_dynamic_gas', False):
            try:
                gas_price = self.w3.eth.gas_price
                multiplier = self.config['transaction'].get('gas_price_multiplier', 1.2)
                gas_price = int(gas_price * multiplier)
                return gas_price
            except Exception as e:
                self.logger.warning(f"Не удалось получить динамическую цену газа: {str(e)}. Используем значение из конфига.")
        
        return self.w3.to_wei(self.config['transaction']['gas_price_gwei'], 'gwei')

    def calculate_send_amount(self, balance, gas_price, gas_limit):
        """Вычисляет сумму для отправки (весь баланс минус комиссия и случайный остаток)"""
        total_gas_cost = gas_price * gas_limit
        remaining_wei, remaining_eth = self.get_random_remaining_balance_wei()
        
        amount_to_send = balance - total_gas_cost - remaining_wei
        
        if amount_to_send <= 0:
            return 0, remaining_eth
        
        return amount_to_send, remaining_eth

    def convert_to_serializable(self, obj):
        """Конвертирует объект в JSON-сериализуемый формат"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self.convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_serializable(item) for item in obj]
        else:
            return obj

    def will_next_account_be_skipped(self, next_private_key):
        """Предварительно проверяет, будет ли следующий аккаунт пропущен"""
        if not next_private_key:
            return False
        
        try:
            account = self.w3.eth.account.from_key(next_private_key)
            from_address = account.address
            balance = self.w3.eth.get_balance(from_address)
            balance_eth = float(self.w3.from_wei(balance, 'ether'))
            
            # Проверяем минимальный баланс
            if self.config.get('balance_check', {}).get('enabled', False):
                min_balance = self.config['balance_check']['minimum_balance']
                return balance_eth < min_balance
            
            return False
        except Exception:
            return False

    async def send_native_token(self, private_key, to_address, account_id):
        """Отправляет нативные токены (ETH) с одного кошелька на указанный адрес"""
        async with self.semaphore:
            account = self.w3.eth.account.from_key(private_key)
            from_address = account.address

            self.logger.info(f"[Аккаунт {account_id}] Начало отправки ETH с {from_address} на {to_address}")

            # Получаем баланс
            try:
                balance = self.w3.eth.get_balance(from_address)
                balance_eth = float(self.w3.from_wei(balance, 'ether'))
            except Exception as e:
                error_msg = f"Ошибка при получении баланса: {str(e)}"
                self.logger.log_account_failed(account_id, error_msg)
                self.stats['failed_accounts'].append({
                    'account_id': account_id,
                    'address': from_address,
                    'reason': error_msg
                })
                return False

            # Проверяем минимальный баланс
            if self.config.get('balance_check', {}).get('enabled', False):
                min_balance = self.config['balance_check']['minimum_balance']
                if balance_eth < min_balance:
                    skip_msg = self.config['balance_check']['skip_message']
                    self.logger.log_account_skipped(account_id, skip_msg, f"{balance_eth:.8f} ETH")
                    self.stats['skipped_accounts'].append({
                        'account_id': account_id,
                        'address': from_address,
                        'balance': balance_eth,
                        'min_required': min_balance
                    })
                    return "skipped"
                
                self.logger.info(f"[Аккаунт {account_id}] Баланс проверен: {balance_eth:.8f} ETH (минимум: {min_balance} ETH) ✓")

            # Получаем цену газа и лимит
            gas_price = self.get_gas_price()
            gas_limit = self.config['transaction']['gas_limit']

            # Вычисляем сумму для отправки
            amount_wei, target_remaining = self.calculate_send_amount(balance, gas_price, gas_limit)
            
            if amount_wei <= 0:
                error_msg = "Невозможно отправить транзакцию: недостаточно средств для покрытия комиссии и остатка"
                self.logger.log_account_failed(account_id, error_msg)
                self.stats['failed_accounts'].append({
                    'account_id': account_id,
                    'address': from_address,
                    'reason': error_msg
                })
                return False

            # Логируем информацию о транзакции
            remaining_balance = balance - amount_wei - (gas_price * gas_limit)
            remaining_eth = float(self.w3.from_wei(remaining_balance, 'ether'))
            
            min_range = self.config['transaction']['random_remaining_balance_eth']['min']
            max_range = self.config['transaction']['random_remaining_balance_eth']['max']
            
            amount_eth = float(self.w3.from_wei(amount_wei, 'ether'))
            
            self.logger.info(f"[Аккаунт {account_id}] Отправляем весь баланс: {amount_eth:.8f} ETH")
            self.logger.info(f"[Аккаунт {account_id}] 🎲 Случайный остаток: {target_remaining:.8f} ETH (диапазон: {min_range}-{max_range} ETH)")
            self.logger.info(f"[Аккаунт {account_id}] Останется на кошельке: {remaining_eth:.8f} ETH")

            # Проверяем баланс на покрытие суммы и газа
            total_cost = amount_wei + gas_price * gas_limit
            if balance < total_cost:
                total_cost_eth = float(self.w3.from_wei(total_cost, 'ether'))
                error_msg = f"Недостаточно ETH на балансе для суммы и газа. Требуется: {total_cost_eth:.8f} ETH, Доступно: {balance_eth:.8f} ETH"
                self.logger.log_account_failed(account_id, error_msg)
                self.stats['failed_accounts'].append({
                    'account_id': account_id,
                    'address': from_address,
                    'reason': error_msg
                })
                return False

            # 🔥 ПРОВЕРЯЕМ ЦЕНУ ГАЗА НЕПОСРЕДСТВЕННО ПЕРЕД ОТПРАВКОЙ ТРАНЗАКЦИИ
            self.logger.info(f"[Аккаунт {account_id}] 🔍 Проверяем цену газа перед отправкой транзакции...")
            if not await self.wait_for_acceptable_gas_price(account_id):
                error_msg = "Отмена транзакции из-за высокой цены газа"
                self.logger.log_account_failed(account_id, error_msg)
                self.stats['failed_accounts'].append({
                    'account_id': account_id,
                    'address': from_address,
                    'reason': error_msg
                })
                return False

            # Отправляем транзакцию
            for attempt in range(1, self.config['execution']['retry_count'] + 1):
                try:
                    nonce = self.w3.eth.get_transaction_count(from_address)
                    tx = {
                        'chainId': self.config['network']['chain_id'],
                        'nonce': nonce,
                        'to': to_address,
                        'value': amount_wei,
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                    }

                    gas_price_gwei = float(self.w3.from_wei(gas_price, 'gwei'))
                    self.logger.info(f"[Аккаунт {account_id}] Используем цену газа: {gas_price_gwei:.2f} Gwei")

                    signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    self.logger.info(f"[Аккаунт {account_id}] Транзакция отправлена: {tx_hash.hex()}")

                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

                    if receipt['status'] == 1:
                        explorer_url = self.config.get('explorer', {}).get('base_url', 'https://etherscan.io/tx/')
                        amount_formatted = f"{amount_eth:.8f}"
                        
                        self.logger.log_transaction_success(
                            account_id, 
                            tx_hash.hex(), 
                            explorer_url, 
                            amount_formatted, 
                            "ETH", 
                            from_address
                        )
                        
                        # Обновляем статистику (конвертируем все в float)
                        gas_used = int(receipt.get('gasUsed', gas_limit))
                        self.stats['successful_accounts'].append({
                            'account_id': account_id,
                            'address': from_address,
                            'amount_sent': amount_eth,
                            'gas_used': gas_used,
                            'tx_hash': tx_hash.hex(),
                            'target_remaining': target_remaining
                        })
                        self.stats['total_sent'] += amount_eth
                        self.stats['total_gas_used'] += gas_used
                        
                        # Показываем финальный баланс
                        try:
                            final_balance = self.w3.eth.get_balance(from_address)
                            final_balance_eth = float(self.w3.from_wei(final_balance, 'ether'))
                            self.logger.info(f"[Аккаунт {account_id}] Финальный баланс кошелька: {final_balance_eth:.8f} ETH")
                        except:
                            pass
                        
                        return True
                    else:
                        error_msg = f"Транзакция не удалась: {tx_hash.hex()}"
                        if attempt < self.config['execution']['retry_count']:
                            self.logger.warning(f"[Аккаунт {account_id}] {error_msg}. Повторная попытка {attempt + 1}/{self.config['execution']['retry_count']}")
                            await asyncio.sleep(5)
                        else:
                            self.logger.log_account_failed(account_id, error_msg)
                            self.stats['failed_accounts'].append({
                                'account_id': account_id,
                                'address': from_address,
                                'reason': error_msg
                            })
                            return False

                except Exception as e:
                    error_msg = f"Ошибка при отправке транзакции (попытка {attempt}): {str(e)}"
                    
                    if "insufficient funds" in str(e).lower():
                        self.logger.log_account_failed(account_id, "Недостаточно средств для транзакции")
                        self.stats['failed_accounts'].append({
                            'account_id': account_id,
                            'address': from_address,
                            'reason': "Недостаточно средств"
                        })
                        return False
                    
                    if attempt < self.config['execution']['retry_count']:
                        self.logger.warning(f"[Аккаунт {account_id}] {error_msg}. Повторная попытка {attempt + 1}/{self.config['execution']['retry_count']}")
                        await asyncio.sleep(5)
                    else:
                        self.logger.log_account_failed(account_id, error_msg)
                        self.stats['failed_accounts'].append({
                            'account_id': account_id,
                            'address': from_address,
                            'reason': str(e)
                        })
                        return False

            return False

    def save_results_to_files(self):
        """Сохраняет результаты в файлы с правильной JSON сериализацией"""
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Сохраняем неудачные аккаунты
        if self.stats['failed_accounts']:
            failed_file = f"{results_dir}/failed_accounts_{timestamp}.json"
            try:
                serializable_data = self.convert_to_serializable(self.stats['failed_accounts'])
                with open(failed_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Список неудачных аккаунтов сохранен в {failed_file}")
            except Exception as e:
                self.logger.error(f"Ошибка при сохранении неудачных аккаунтов: {e}")

        # Сохраняем пропущенные аккаунты
        if self.stats['skipped_accounts']:
            skipped_file = f"{results_dir}/skipped_accounts_{timestamp}.json"
            try:
                serializable_data = self.convert_to_serializable(self.stats['skipped_accounts'])
                with open(skipped_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Список пропущенных аккаунтов сохранен в {skipped_file}")
            except Exception as e:
                self.logger.error(f"Ошибка при сохранении пропущенных аккаунтов: {e}")

    async def process_transfers(self, private_keys, recipient_addresses):
        """Обрабатывает все переводы асинхронно с правильной логикой задержек"""
        self.stats['start_time'] = datetime.now()
        
        total_accounts = len(private_keys)
        
        if len(private_keys) != len(recipient_addresses):
            self.logger.error(f"Количество приватных ключей ({len(private_keys)}) не соответствует "
                             f"количеству адресов получателей ({len(recipient_addresses)})")
            return

        # Перемешиваем кошельки если включено
        private_keys, recipient_addresses = self.shuffle_wallets_data(private_keys, recipient_addresses)

        # Показываем настройки
        min_remaining = self.config['transaction']['random_remaining_balance_eth']['min']
        max_remaining = self.config['transaction']['random_remaining_balance_eth']['max']
        min_delay = self.config['execution']['random_delay_range']['min']
        max_delay = self.config['execution']['random_delay_range']['max']
        skipped_delay = self.get_skipped_delay()
        
        self.logger.info(f"🎲 Режим случайного остатка: {min_remaining} - {max_remaining} ETH")
        self.logger.info(f"⏰ Режим случайной задержки: {min_delay} - {max_delay} секунд")
        self.logger.info(f"⏭️ Задержка после пропущенного аккаунта: {skipped_delay} секунд")
        
        if self.config.get('execution', {}).get('shuffle_wallets', False):
            self.logger.info(f"🔀 Перемешивание кошельков: включено")
        
        self.logger.info(f"🚀 Начинаем обработку {total_accounts} аккаунтов...")
        self.logger.info(f"⛽ Проверка газа будет выполняться перед каждой транзакцией")

        # Обрабатываем аккаунты последовательно с правильной логикой задержек
        for i, (private_key, to_address) in enumerate(zip(private_keys, recipient_addresses)):
            account_id = i + 1
            
            # Показываем прогресс
            if self.config.get('execution', {}).get('show_progress', True) and i > 0:
                success_count = len(self.stats['successful_accounts'])
                failed_count = len(self.stats['failed_accounts'])
                skipped_count = len(self.stats['skipped_accounts'])
                self.logger.log_progress(i, total_accounts, success_count, failed_count, skipped_count)
            
            # Отправляем транзакцию
            result = await self.send_native_token(private_key, to_address, account_id)
            
            # Логика задержки ПОСЛЕ обработки аккаунта
            if i < len(private_keys) - 1:  # Если это не последний аккаунт
                current_account_was_skipped = (result == "skipped")
                
                if current_account_was_skipped:
                    # Текущий аккаунт пропущен - проверяем следующий
                    next_private_key = private_keys[i + 1] if i + 1 < len(private_keys) else None
                    next_will_be_skipped = self.will_next_account_be_skipped(next_private_key)
                    
                    if next_will_be_skipped:
                        # Следующий тоже будет пропущен - короткая задержка
                        delay = skipped_delay
                        self.logger.info(f"⏭️ Короткая задержка (следующий тоже будет пропущен): {delay} секунд...")
                    else:
                        # Следующий НЕ будет пропущен - обычная задержка
                        delay = self.get_random_delay()
                        self.logger.info(f"⏰ Обычная задержка после пропущенного (следующий будет обработан): {delay:.1f} секунд...")
                else:
                    # Текущий аккаунт обработан успешно - обычная задержка
                    delay = self.get_random_delay()
                    self.logger.info(f"⏳ Ожидание {delay:.1f} секунд перед следующей транзакцией...")
                
                self.stats['total_delay_time'] += delay
                await asyncio.sleep(delay)
        
        self.stats['end_time'] = datetime.now()

        # Финальная статистика
        success_count = len(self.stats['successful_accounts'])
        failed_count = len(self.stats['failed_accounts'])
        skipped_count = len(self.stats['skipped_accounts'])
        
        execution_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        self.logger.info("=" * 60)
        self.logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Успешных транзакций: {success_count}")
        self.logger.error(f"❌ Неудачных транзакций: {failed_count}")
        if skipped_count > 0:
            self.logger.warning(f"⏭️ Пропущенных аккаунтов: {skipped_count}")
        
        if self.config.get('execution', {}).get('detailed_stats', True):
            self.logger.info(f"💰 Общая сумма отправлено: {self.stats['total_sent']:.8f} ETH")
            self.logger.info(f"⛽ Общий газ использовано: {self.stats['total_gas_used']:,}")
            self.logger.info(f"⏱️ Время выполнения: {execution_time:.1f} секунд")
            self.logger.info(f"⏳ Общее время задержек: {self.stats['total_delay_time']:.1f} секунд")
            
            if success_count > 0:
                avg_amount = self.stats['total_sent'] / success_count
                self.logger.info(f"📈 Средняя сумма на транзакцию: {avg_amount:.8f} ETH")
                
                # Статистика по остаткам
                remaining_amounts = [acc.get('target_remaining', 0) for acc in self.stats['successful_accounts'] if acc.get('target_remaining')]
                if remaining_amounts:
                    avg_remaining = sum(remaining_amounts) / len(remaining_amounts)
                    min_remaining_actual = min(remaining_amounts)
                    max_remaining_actual = max(remaining_amounts)
                    self.logger.info(f"🎲 Статистика остатков: мин={min_remaining_actual:.8f}, макс={max_remaining_actual:.8f}, среднее={avg_remaining:.8f} ETH")

        self.save_results_to_files()
        self.logger.info("=" * 60)