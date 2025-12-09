#!/usr/bin/env python3
"""
Тест доступа к API - проверка всех ключей
"""
import asyncio
import aiohttp
import os
from datetime import datetime


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


async def test_openrouter_deepseek(api_key: str):
    """Тест OpenRouter с DeepSeek моделью"""
    print_header("ТЕСТ 1: OpenRouter + DeepSeek")
    
    if not api_key:
        print_error("DEEPSEEK_API_KEY не установлен")
        print_info("Установи: export DEEPSEEK_API_KEY=sk-or-v1-...")
        return False
    
    print_info(f"API Key: {api_key[:15]}...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": "Reply with: DeepSeek OK"}
        ],
        "max_tokens": 20
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            start = datetime.now()
            async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                latency = (datetime.now() - start).total_seconds() * 1000
                
                if response.status != 200:
                    error = await response.text()
                    print_error(f"HTTP {response.status}")
                    print(f"   {error[:200]}")
                    return False
                
                result = await response.json()
                
                model_used = result.get("model", "unknown")
                message = result["choices"][0]["message"]["content"]
                
                print_success("DeepSeek доступен!")
                print(f"   Модель: {model_used}")
                print(f"   Latency: {latency:.0f}ms")
                print(f"   Ответ: {message}")
                
                if model_used == "deepseek/deepseek-chat":
                    print_success("Используется правильная модель DeepSeek!")
                    return True
                else:
                    print_warning(f"Используется {model_used} вместо DeepSeek")
                    return False
                
    except asyncio.TimeoutError:
        print_error("Timeout - нет ответа от API")
        return False
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False


async def test_openrouter_claude(api_key: str):
    """Тест OpenRouter с Claude моделью"""
    print_header("ТЕСТ 2: OpenRouter + Claude")
    
    if not api_key:
        print_error("OPENAI_API_KEY не установлен")
        return False
    
    print_info(f"API Key: {api_key[:15]}...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000"
    }
    
    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "user", "content": "Reply with: Claude OK"}
        ],
        "max_tokens": 20
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            start = datetime.now()
            async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                latency = (datetime.now() - start).total_seconds() * 1000
                
                if response.status != 200:
                    error = await response.text()
                    print_error(f"HTTP {response.status}")
                    print(f"   {error[:200]}")
                    return False
                
                result = await response.json()
                
                model_used = result.get("model", "unknown")
                message = result["choices"][0]["message"]["content"]
                
                print_success("Claude доступен!")
                print(f"   Модель: {model_used}")
                print(f"   Latency: {latency:.0f}ms")
                print(f"   Ответ: {message}")
                return True
                
    except asyncio.TimeoutError:
        print_error("Timeout - нет ответа от API")
        return False
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False


async def test_binance_testnet(api_key: str, api_secret: str):
    """Тест Binance Testnet API"""
    print_header("ТЕСТ 3: Binance Testnet")
    
    if not api_key or not api_secret:
        print_warning("Binance API ключи не установлены")
        print_info("Получи на: https://testnet.binance.vision/")
        return False
    
    print_info(f"API Key: {api_key[:15]}...")
    
    # Простой публичный endpoint (не требует подписи)
    url = "https://testnet.binance.vision/api/v3/ticker/price?symbol=BTCUSDT"
    
    try:
        async with aiohttp.ClientSession() as session:
            start = datetime.now()
            async with session.get(url, timeout=10) as response:
                latency = (datetime.now() - start).total_seconds() * 1000
                
                if response.status != 200:
                    error = await response.text()
                    print_error(f"HTTP {response.status}")
                    print(f"   {error[:200]}")
                    return False
                
                result = await response.json()
                
                price = float(result["price"])
                
                print_success("Binance Testnet доступен!")
                print(f"   BTC/USDT: ${price:,.2f}")
                print(f"   Latency: {latency:.0f}ms")
                return True
                
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False


async def check_openrouter_credits(api_key: str):
    """Проверка баланса OpenRouter"""
    print_header("БАЛАНС OpenRouter")
    
    if not api_key:
        return
    
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    limit = data.get("data", {}).get("limit", 0)
                    usage = data.get("data", {}).get("usage", 0)
                    remaining = limit - usage
                    
                    print_success(f"Баланс: ${remaining:.2f} / ${limit:.2f}")
                    
                    if remaining < 0.50:
                        print_warning(f"Осталось мало! Пополни на openrouter.ai")
                    elif remaining < 1.00:
                        print_warning(f"Осталось ~{remaining:.2f}$ (хватит на 1-2 дня)")
                    else:
                        print_success(f"Достаточно для тестирования!")
                else:
                    print_warning("Не удалось проверить баланс")
    except Exception as e:
        print_warning(f"Ошибка проверки баланса: {e}")


async def main():
    """Main test function"""
    
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"🧪 ПРОВЕРКА ДОСТУПА К API")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Получить переменные окружения
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    binance_key = os.environ.get("BINANCE_API_KEY", "")
    binance_secret = os.environ.get("BINANCE_API_SECRET", "")
    
    results = []
    
    # Тест 1: DeepSeek через OpenRouter
    if deepseek_key:
        result = await test_openrouter_deepseek(deepseek_key)
        results.append(("DeepSeek (Trading AI)", result))
        await asyncio.sleep(1)
    else:
        print_header("ТЕСТ 1: OpenRouter + DeepSeek")
        print_warning("DEEPSEEK_API_KEY не установлен")
        results.append(("DeepSeek (Trading AI)", False))
    
    # Тест 2: Claude через OpenRouter
    if openai_key or deepseek_key:
        key = openai_key or deepseek_key
        result = await test_openrouter_claude(key)
        results.append(("Claude (Analytics)", result))
        await asyncio.sleep(1)
    else:
        print_header("ТЕСТ 2: OpenRouter + Claude")
        print_warning("OPENAI_API_KEY не установлен")
        results.append(("Claude (Analytics)", False))
    
    # Тест 3: Binance
    result = await test_binance_testnet(binance_key, binance_secret)
    results.append(("Binance Testnet", result))
    
    # Проверка баланса
    if deepseek_key:
        await check_openrouter_credits(deepseek_key)
    
    # Итоги
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"📊 РЕЗУЛЬТАТЫ")
    print(f"{'='*60}{Colors.RESET}\n")
    
    for service, success in results:
        if success:
            print_success(f"{service}")
        else:
            print_error(f"{service}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Пройдено: {passed}/{total}{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!{Colors.RESET}")
        print(f"{Colors.GREEN}Можно запускать проект!{Colors.RESET}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Настрой недостающие API ключи{Colors.RESET}\n")
        
        if not deepseek_key:
            print_info("1. OpenRouter API: https://openrouter.ai/")
        if not binance_key:
            print_info("2. Binance Testnet: https://testnet.binance.vision/")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Тест прерван{Colors.RESET}\n")

