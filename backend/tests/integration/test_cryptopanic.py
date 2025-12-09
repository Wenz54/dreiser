#!/usr/bin/env python3
"""
Тест CryptoPanic API
"""
import os
import requests
from datetime import datetime


def test_cryptopanic():
    """Тест CryptoPanic новостей"""
    
    print("\n" + "="*60)
    print("🔥 ТЕСТ: CryptoPanic API")
    print("="*60 + "\n")
    
    # Получить token
    token = os.environ.get("CRYPTOPANIC_API_TOKEN")
    
    if not token:
        # Попробовать из .env
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('CRYPTOPANIC_API_TOKEN'):
                        token = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
    
    if not token:
        print("❌ CRYPTOPANIC_API_TOKEN не найден!")
        print("\n📋 Как получить:")
        print("  1. https://cryptopanic.com/developers/api/")
        print("  2. Get your free API token")
        print('  3. Добавь в .env: CRYPTOPANIC_API_TOKEN=твой_token')
        return False
    
    print(f"ℹ️  Token: {token[:20]}...")
    
    # Test request
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": token,
        "currencies": "BTC",
        "filter": "hot",
        "public": "true",
        "kind": "news"
    }
    
    try:
        print("⏳ Получаю hot news...")
        start = datetime.now()
        response = requests.get(url, params=params, timeout=10)
        latency = (datetime.now() - start).total_seconds() * 1000
        
        if response.status_code != 200:
            print(f"❌ Ошибка: HTTP {response.status_code}")
            print(f"   {response.text[:200]}")
            return False
        
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            print("⚠️  Новостей нет (странно)")
            return False
        
        print(f"✅ Успешно!")
        print(f"   Получено новостей: {len(results)}")
        print(f"   Latency: {latency:.0f}ms")
        print(f"\n📰 Первые 3 новости:\n")
        
        for i, item in enumerate(results[:3], 1):
            title = item.get("title", "No title")
            source = item.get("domain", "unknown")
            votes = item.get("votes", {})
            positive = votes.get("positive", 0)
            negative = votes.get("negative", 0)
            
            # Sentiment
            if positive + negative > 0:
                ratio = positive / (positive + negative)
                if ratio >= 0.65:
                    sentiment = "📈 BULLISH"
                elif ratio <= 0.35:
                    sentiment = "📉 BEARISH"
                else:
                    sentiment = "➡️  NEUTRAL"
            else:
                sentiment = "➡️  NEUTRAL"
            
            print(f"{i}. {sentiment}")
            print(f"   {title[:70]}...")
            print(f"   Source: {source} | Votes: +{positive} -{negative}")
            print()
        
        print("="*60)
        print("🎉 CryptoPanic работает отлично!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    try:
        test_cryptopanic()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван\n")

