#!/usr/bin/env python3
"""
Простой тест API - без async, без aiohttp
"""
import os
import requests
from datetime import datetime


def test_openrouter(api_key):
    """Тест OpenRouter DeepSeek"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ: OpenRouter + DeepSeek")
    print("="*60 + "\n")
    
    if not api_key:
        print("❌ API ключ не установлен!")
        print("Установи: $env:DEEPSEEK_API_KEY='sk-or-v1-...'")
        return False
    
    print(f"ℹ️  API Key: {api_key[:20]}...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": "Reply: DeepSeek OK"}],
        "max_tokens": 20
    }
    
    try:
        print("⏳ Отправляю запрос...")
        start = datetime.now()
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        latency = (datetime.now() - start).total_seconds() * 1000
        
        if response.status_code != 200:
            print(f"❌ Ошибка: HTTP {response.status_code}")
            print(f"   {response.text[:200]}")
            return False
        
        result = response.json()
        model = result.get("model", "unknown")
        message = result["choices"][0]["message"]["content"]
        
        print(f"✅ Успешно!")
        print(f"   Модель: {model}")
        print(f"   Latency: {latency:.0f}ms")
        print(f"   Ответ: {message}")
        
        if model == "deepseek/deepseek-chat":
            print(f"✅ Правильная модель DeepSeek!")
            return True
        else:
            print(f"⚠️  Используется {model}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - нет ответа")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_binance(api_key=None):
    """Тест Binance Testnet"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ: Binance Testnet")
    print("="*60 + "\n")
    
    url = "https://testnet.binance.vision/api/v3/ticker/price?symbol=BTCUSDT"
    
    try:
        print("⏳ Получаю цену BTC...")
        start = datetime.now()
        response = requests.get(url, timeout=10)
        latency = (datetime.now() - start).total_seconds() * 1000
        
        if response.status_code != 200:
            print(f"❌ Ошибка: HTTP {response.status_code}")
            return False
        
        result = response.json()
        price = float(result["price"])
        
        print(f"✅ Успешно!")
        print(f"   BTC/USDT: ${price:,.2f}")
        print(f"   Latency: {latency:.0f}ms")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def check_balance(api_key):
    """Проверка баланса OpenRouter"""
    print("\n" + "="*60)
    print("💰 БАЛАНС OpenRouter")
    print("="*60 + "\n")
    
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            limit = data.get("data", {}).get("limit", 0)
            usage = data.get("data", {}).get("usage", 0)
            remaining = limit - usage
            
            print(f"💵 Всего: ${limit:.2f}")
            print(f"💸 Использовано: ${usage:.2f}")
            print(f"💰 Осталось: ${remaining:.2f}")
            
            if remaining < 0.50:
                print(f"⚠️  Мало! Пополни на openrouter.ai")
            elif remaining < 1.00:
                print(f"⚠️  Хватит на 1-2 дня тестов")
            else:
                print(f"✅ Достаточно для тестирования!")
    except:
        print("⚠️  Не удалось проверить баланс")


def load_env_file():
    """Загрузить .env файл если есть"""
    if os.path.exists('.env'):
        print("📁 Найден .env файл, загружаю...")
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value and not os.environ.get(key):
                        os.environ[key] = value
        print("✅ .env загружен\n")


def main():
    print("\n" + "="*60)
    print("🧪 ПРОВЕРКА ДОСТУПА К API")
    print("="*60)
    
    # Загрузить .env если есть
    load_env_file()
    
    # Получить ключи
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    binance_key = os.environ.get("BINANCE_API_KEY", "")
    
    if not deepseek_key and not binance_key:
        print("\n❌ Ключи не найдены!")
        print("\n📋 Два способа установить:\n")
        print("Способ 1: Создать .env файл")
        print("  cp .env.example .env")
        print("  notepad .env")
        print("  # Заполни ключи")
        print("\nСпособ 2: Установить в PowerShell")
        print('  $env:DEEPSEEK_API_KEY="sk-or-v1-твой_ключ"')
        print('  $env:BINANCE_API_KEY="твой_binance_ключ"')
        return
    
    results = []
    
    # Тест 1: OpenRouter
    if deepseek_key:
        result = test_openrouter(deepseek_key)
        results.append(("OpenRouter DeepSeek", result))
    
    # Тест 2: Binance
    result = test_binance(binance_key)
    results.append(("Binance Testnet", result))
    
    # Баланс
    if deepseek_key:
        check_balance(deepseek_key)
    
    # Итоги
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ")
    print("="*60 + "\n")
    
    for service, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {service}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\n✅ Пройдено: {passed}/{total}\n")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Можно запускать проект!\n")
    else:
        print("⚠️  Настрой недостающие API ключи\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван\n")

