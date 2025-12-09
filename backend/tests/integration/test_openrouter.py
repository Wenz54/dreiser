#!/usr/bin/env python3
"""
Тест OpenRouter - проверка что запросы идут на правильные модели
"""
import asyncio
import aiohttp
import os
from datetime import datetime


async def test_openrouter_model(api_key: str, model: str):
    """
    Тест: проверить что OpenRouter использует правильную модель
    
    Args:
        api_key: OpenRouter API ключ
        model: Модель для теста (например: "deepseek/deepseek-chat")
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",  # Optional
        "X-Title": "Draizer Test"  # Optional
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'test OK' if you are DeepSeek"}
        ],
        "route": "fallback",
        "fallback": []  # Отключить fallback
    }
    
    print(f"\n{'='*60}")
    print(f"🧪 Тестирую модель: {model}")
    print(f"{'='*60}\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            start_time = datetime.now()
            
            async with session.post(url, headers=headers, json=payload) as response:
                end_time = datetime.now()
                latency_ms = (end_time - start_time).total_microseconds() / 1000
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Ошибка: {response.status}")
                    print(f"   {error_text}")
                    return False
                
                result = await response.json()
                
                # Проверяем какая модель реально использовалась
                used_model = result.get("model", "unknown")
                provider = response.headers.get("X-Provider", "unknown")
                
                print(f"✅ Запрос успешен!")
                print(f"   Запрошенная модель: {model}")
                print(f"   Использованная модель: {used_model}")
                print(f"   Provider: {provider}")
                print(f"   Latency: {latency_ms:.1f}ms")
                print(f"   Response: {result['choices'][0]['message']['content']}")
                
                # Проверка соответствия
                if used_model == model:
                    print(f"\n✅ PASS: Модель совпадает!")
                    return True
                else:
                    print(f"\n⚠️ WARNING: Использована другая модель!")
                    print(f"   Возможно был fallback")
                    return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def test_all_models(api_key: str):
    """Тест всех важных моделей"""
    
    models_to_test = [
        ("deepseek/deepseek-chat", "DeepSeek для trading"),
        ("anthropic/claude-3.5-sonnet", "Claude для аналитики"),
        ("meta-llama/llama-3.1-70b-instruct", "Llama (бесплатная альтернатива)"),
    ]
    
    results = []
    
    for model, description in models_to_test:
        print(f"\n📋 {description}")
        success = await test_openrouter_model(api_key, model)
        results.append((model, success))
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТОВ")
    print(f"{'='*60}\n")
    
    for model, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {model}")
    
    print(f"\n{'='*60}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("OpenRouter правильно роутит запросы на указанные модели.")
    else:
        print("⚠️ Некоторые тесты провалились")
        print("Проверь API ключ и настройки")


async def check_credits(api_key: str):
    """Проверить остаток кредитов"""
    url = "https://openrouter.ai/api/v1/auth/key"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    credits = data.get("data", {}).get("limit", 0)
                    usage = data.get("data", {}).get("usage", 0)
                    remaining = credits - usage
                    
                    print(f"\n💰 БАЛАНС:")
                    print(f"   Всего кредитов: ${credits:.2f}")
                    print(f"   Использовано: ${usage:.2f}")
                    print(f"   Осталось: ${remaining:.2f}")
                else:
                    print(f"❌ Не удалось проверить баланс: {response.status}")
    
    except Exception as e:
        print(f"❌ Ошибка проверки баланса: {e}")


async def main():
    """Main function"""
    
    print("="*60)
    print("🧪 OPENROUTER ТЕСТ")
    print("="*60)
    
    # Получить API ключ
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("\n❌ API ключ не найден!")
        print("Установи переменную окружения:")
        print("  export OPENROUTER_API_KEY=sk-or-v1-твой_ключ")
        print("или")
        print("  set OPENROUTER_API_KEY=sk-or-v1-твой_ключ  (Windows)")
        return
    
    if not api_key.startswith("sk-or-"):
        print("\n⚠️ Это не похоже на OpenRouter ключ!")
        print(f"Твой ключ: {api_key[:10]}...")
        print("OpenRouter ключи начинаются с: sk-or-v1-...")
        
        proceed = input("\nПродолжить всё равно? (y/n): ")
        if proceed.lower() != 'y':
            return
    
    # Проверить баланс
    await check_credits(api_key)
    
    # Запустить тесты
    await test_all_models(api_key)
    
    print(f"\n{'='*60}")
    print("✅ Тестирование завершено!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())

