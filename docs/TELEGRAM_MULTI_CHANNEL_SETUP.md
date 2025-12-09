# 📰 Multi-Channel Telegram Monitoring

## Как добавить мониторинг нескольких Telegram каналов

### Вариант 1: Через .env (простой)

```env
# .env
TELEGRAM_NEWS_CHANNELS=@crypto_news,@binance_announcements,@whale_alert
```

**Код** (`backend/app/tasks/news_tasks.py`):

```python
async def _monitor_telegram_news_async():
    """Monitor multiple channels"""
    
    channels = settings.TELEGRAM_NEWS_CHANNELS.split(',')
    
    for channel in channels:
        channel = channel.strip()
        try:
            result = await telegram_monitor.process_channel(channel)
            # Save to DB...
        except Exception as e:
            print(f"Error monitoring {channel}: {e}")
```

### Вариант 2: Separate Celery Tasks

```python
# celery_app.py

celery_app.conf.beat_schedule = {
    "monitor-binance-news": {
        "task": "app.tasks.news_tasks.monitor_channel",
        "schedule": crontab(minute="*/30"),
        "args": ["@binance_announcements"]
    },
    "monitor-crypto-news": {
        "task": "app.tasks.news_tasks.monitor_channel",
        "schedule": crontab(minute="*/30"),
        "args": ["@crypto_news"]
    },
    "monitor-whale-alerts": {
        "task": "app.tasks.news_tasks.monitor_channel",
        "schedule": crontab(minute="*/15"),  # Чаще для whale alerts
        "args": ["@whale_alert"]
    },
}
```

### Вариант 3: Real-Time Listener (вместо polling)

Для **реал-тайм** мониторинга (без 30-мин интервала):

```python
# backend/app/services/telegram_realtime.py

from telethon import TelegramClient, events

class TelegramRealtimeMonitor:
    """Real-time Telegram channel listener"""
    
    def __init__(self):
        self.client = TelegramClient('draizer_realtime', api_id, api_hash)
    
    async def start_listening(self, channels: List[str]):
        """
        Start listening to channels in REAL-TIME
        
        Args:
            channels: List of channel usernames (e.g., ["@crypto_news"])
        """
        await self.client.start()
        
        @self.client.on(events.NewMessage(chats=channels))
        async def handler(event):
            """Triggered IMMEDIATELY when new message arrives"""
            message_text = event.message.text
            channel = await event.get_chat()
            
            print(f"🔔 New message in {channel.username}:")
            print(f"   {message_text[:100]}...")
            
            # Немедленно отправить в GPT для анализа
            await self._process_message_realtime(message_text, channel.username)
        
        # Keep listening
        await self.client.run_until_disconnected()
    
    async def _process_message_realtime(self, text: str, channel: str):
        """Process single message in real-time"""
        # 1. GPT анализ
        # 2. Relevance scoring
        # 3. If relevant → notify DeepSeek immediately
        pass
```

**Запуск**:
```python
# В отдельном процессе/сервисе
realtime_monitor = TelegramRealtimeMonitor()
await realtime_monitor.start_listening([
    "@crypto_news",
    "@binance_announcements",
    "@whale_alert"
])
```

**Pros**:
- ✅ Instant notifications (нет задержки 30 мин)
- ✅ Меньше нагрузки (не polling каждые 30 мин)

**Cons**:
- ❌ Постоянное соединение (долгоживущий процесс)
- ❌ Нужен отдельный сервис/контейнер

## Рекомендация

**Для MVP**: Оставь **polling каждые 30 мин** (текущая реализация).

**Для production**: Переходи на **real-time listener**, если нужна максимальная скорость реакции.

