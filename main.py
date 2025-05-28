import asyncio
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.logger import setup_logger
from src.utils import load_config, load_private_keys, load_recipient_addresses
from src.sender import TokenSender
from src.colors import Colors
from web3 import Web3

def print_header():
    """Выводит красивый заголовок программы"""
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}🚀 ETH TOKEN SENDER v2.1{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")

def get_current_gas_info(config):
    """Получает информацию о текущем газе"""
    try:
        w3 = Web3(Web3.HTTPProvider(config['network']['rpc_url']))
        if not w3.is_connected():
            return None, None
        
        # Получаем текущую цену газа
        gas_price = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')
        
        # Рассчитываем стоимость транзакции в ETH
        gas_limit = config['transaction']['gas_limit']
        transaction_cost_wei = gas_price * gas_limit
        transaction_cost_eth = w3.from_wei(transaction_cost_wei, 'ether')
        
        return gas_price_gwei, transaction_cost_eth
        
    except Exception as e:
        return None, None

def show_gas_info(config):
    """Показывает информацию о текущем газе и автоматически возвращается в меню"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}⛽ ИНФОРМАЦИЯ О ГАЗЕ:{Colors.RESET}")
    print(f"{Colors.YELLOW}Получаем данные...{Colors.RESET}")
    
    gas_price_gwei, transaction_cost_eth = get_current_gas_info(config)
    
    if gas_price_gwei is not None:
        print(f"{Colors.GREEN}✅ Текущая цена газа: {gas_price_gwei:.2f} Gwei{Colors.RESET}")
        print(f"{Colors.BLUE}💰 Стоимость транзакции: {transaction_cost_eth:.8f} ETH{Colors.RESET}")
        
        # Показываем лимит из конфига
        max_gas_gwei = config.get('gas_monitor', {}).get('max_gas_price_gwei', 'не установлен')
        if isinstance(max_gas_gwei, (int, float)):
            if gas_price_gwei <= max_gas_gwei:
                print(f"{Colors.GREEN}✅ Газ в пределах лимита (лимит: {max_gas_gwei} Gwei){Colors.RESET}")
            else:
                print(f"{Colors.RED}⚠️ Газ превышает лимит (лимит: {max_gas_gwei} Gwei){Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}ℹ️ Лимит газа: {max_gas_gwei}{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Не удалось получить информацию о газе{Colors.RESET}")
        print(f"{Colors.YELLOW}Проверьте подключение к RPC: {config['network']['rpc_url']}{Colors.RESET}")

def show_startup_menu():
    """Показывает стартовое меню"""
    while True:
        print(f"\n{Colors.BOLD}{Colors.WHITE}📋 ГЛАВНОЕ МЕНЮ:{Colors.RESET}")
        print(f"{Colors.GREEN}1.{Colors.RESET} {Colors.WHITE}🚀 Запустить отправку токенов{Colors.RESET}")
        print(f"{Colors.BLUE}2.{Colors.RESET} {Colors.WHITE}⛽ Показать текущий Gwei{Colors.RESET}")
        print(f"{Colors.RED}3.{Colors.RESET} {Colors.WHITE}❌ Выход{Colors.RESET}")
        
        try:
            choice = input(f"\n{Colors.YELLOW}Выберите пункт (1-3): {Colors.RESET}").strip()
            if choice == "1":
                return "start"
            elif choice == "2":
                return "gas_info"
            elif choice == "3":
                print(f"{Colors.RED}👋 Программа завершена пользователем{Colors.RESET}")
                return "exit"
            else:
                print(f"{Colors.RED}❌ Неверный выбор. Введите 1, 2 или 3{Colors.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}👋 Программа завершена пользователем{Colors.RESET}")
            return "exit"

def show_retry_menu(failed_accounts, skipped_accounts):
    """Показывает меню для повторного запуска неудачных аккаунтов"""
    total_failed = len(failed_accounts) + len(skipped_accounts)
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠️ ОБНАРУЖЕНЫ НЕУДАЧНЫЕ АККАУНТЫ:{Colors.RESET}")
    print(f"{Colors.RED}❌ Неудачных транзакций: {len(failed_accounts)}{Colors.RESET}")
    print(f"{Colors.YELLOW}⏭️ Пропущенных аккаунтов: {len(skipped_accounts)}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 Всего для повтора: {total_failed}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.WHITE}📋 МЕНЮ ПОВТОРА:{Colors.RESET}")
    print(f"{Colors.GREEN}1.{Colors.RESET} {Colors.WHITE}🔄 Повторить только неудачные аккаунты{Colors.RESET}")
    print(f"{Colors.RED}2.{Colors.RESET} {Colors.WHITE}❌ Завершить работу{Colors.RESET}")
    
    while True:
        try:
            choice = input(f"\n{Colors.YELLOW}Выберите пункт (1-2): {Colors.RESET}").strip()
            if choice == "1":
                return True
            elif choice == "2":
                print(f"{Colors.RED}👋 Программа завершена{Colors.RESET}")
                return False
            else:
                print(f"{Colors.RED}❌ Неверный выбор. Введите 1 или 2{Colors.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}👋 Программа завершена пользователем{Colors.RESET}")
            return False

def get_failed_account_data(failed_accounts, skipped_accounts, all_private_keys, all_recipient_addresses):
    """Извлекает данные для неудачных аккаунтов"""
    failed_private_keys = []
    failed_recipient_addresses = []
    
    # Собираем ID всех неудачных аккаунтов
    failed_account_ids = set()
    
    for account in failed_accounts + skipped_accounts:
        account_id = account.get('account_id')
        if account_id:
            failed_account_ids.add(account_id - 1)  # -1 потому что account_id начинается с 1
    
    # Извлекаем соответствующие ключи и адреса
    for account_index in failed_account_ids:
        if account_index < len(all_private_keys) and account_index < len(all_recipient_addresses):
            failed_private_keys.append(all_private_keys[account_index])
            failed_recipient_addresses.append(all_recipient_addresses[account_index])
    
    return failed_private_keys, failed_recipient_addresses

async def run_token_sender(logger, config, private_keys, recipient_addresses, is_retry=False):
    """Запускает отправку токенов"""
    try:
        if is_retry:
            logger.info(f"🔄 Повторный запуск для {len(private_keys)} неудачных аккаунтов")
        else:
            logger.info(f"🚀 Первичный запуск для {len(private_keys)} аккаунтов")
        
        # Создаем экземпляр TokenSender
        token_sender = TokenSender(config, logger)
        
        # Запускаем процесс отправки токенов
        await token_sender.process_transfers(private_keys, recipient_addresses)
        
        return token_sender.stats
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        return None

async def main():
    """Основная функция с постоянным интерактивным меню"""
    print_header()
    
    # Настраиваем логгер
    logger = setup_logger()
    
    try:
        # Загружаем конфигурацию
        config = load_config()
        logger.info("Конфигурация успешно загружена")
        
        # Главный цикл меню
        while True:
            menu_choice = show_startup_menu()
            
            if menu_choice == "exit":
                return
            elif menu_choice == "gas_info":
                show_gas_info(config)
                continue  # Автоматически возвращаемся в меню
            elif menu_choice == "start":
                break
        
        # Загружаем приватные ключи и адреса получателей
        all_private_keys = load_private_keys()
        all_recipient_addresses = load_recipient_addresses()
        
        logger.info(f"Загружено {len(all_private_keys)} приватных ключей и {len(all_recipient_addresses)} адресов получателей")
        
        # Первый запуск
        stats = await run_token_sender(logger, config, all_private_keys, all_recipient_addresses, is_retry=False)
        
        if stats is None:
            logger.error("❌ Не удалось выполнить отправку токенов")
            return
        
        # Проверяем результаты и всегда предлагаем повтор если есть неудачные
        failed_accounts = stats.get('failed_accounts', [])
        skipped_accounts = stats.get('skipped_accounts', [])
        successful_accounts = stats.get('successful_accounts', [])
        
        total_accounts = len(all_private_keys)
        total_failed = len(failed_accounts) + len(skipped_accounts)
        
        # Если все успешно - завершаем
        if total_failed == 0:
            logger.info(f"🎉 Все {total_accounts} аккаунтов обработаны успешно!")
            logger.info("✅ Программа завершена успешно")
            return
        
        # Если есть неудачные - всегда предлагаем повтор
        if show_retry_menu(failed_accounts, skipped_accounts):
            # Получаем данные для неудачных аккаунтов
            failed_private_keys, failed_recipient_addresses = get_failed_account_data(
                failed_accounts, skipped_accounts, all_private_keys, all_recipient_addresses
            )  # ИСПРАВЛЕНО: добавлена закрывающая скобка
            
            if failed_private_keys:
                logger.info(f"🔄 Начинаем повторную обработку {len(failed_private_keys)} аккаунтов...")
                
                # Повторный запуск
                retry_stats = await run_token_sender(
                    logger, config, failed_private_keys, failed_recipient_addresses, is_retry=True
                )
                
                if retry_stats:
                    retry_successful = len(retry_stats.get('successful_accounts', []))
                    retry_failed = len(retry_stats.get('failed_accounts', [])) + len(retry_stats.get('skipped_accounts', []))
                    
                    logger.info(f"🔄 Результаты повтора: ✅ {retry_successful} успешно, ❌ {retry_failed} неудачно")
                    
                    # Общая статистика
                    total_successful = len(successful_accounts) + retry_successful
                    total_remaining_failed = retry_failed
                    
                    logger.info(f"📊 ИТОГОВАЯ СТАТИСТИКА ПО ВСЕМ ЗАПУСКАМ:")
                    logger.info(f"✅ Всего успешных: {total_successful}/{total_accounts}")
                    logger.info(f"❌ Всего неудачных: {total_remaining_failed}/{total_accounts}")
                    
                    if total_remaining_failed == 0:
                        logger.info("🎉 Все аккаунты успешно обработаны после повтора!")
                    else:
                        logger.warning(f"⚠️ Остались необработанные аккаунты: {total_remaining_failed}")
            else:
                logger.warning("⚠️ Не удалось извлечь данные для повторной обработки")
        
    except FileNotFoundError as e:
        logger.error(f"Ошибка при загрузке файлов: {str(e)}")
        print(f"{Colors.RED}❌ Проверьте наличие необходимых файлов{Colors.RESET}")
    except ConnectionError as e:
        logger.error(f"Ошибка подключения: {str(e)}")
        print(f"{Colors.RED}❌ Проверьте подключение к интернету и RPC{Colors.RESET}")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {str(e)}")
        print(f"{Colors.RED}❌ Произошла непредвиденная ошибка{Colors.RESET}")
    
    logger.info("👋 Программа завершена")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}👋 Программа прервана пользователем{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Критическая ошибка: {str(e)}{Colors.RESET}")