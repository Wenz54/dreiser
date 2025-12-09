"""Binance API integration service"""
import requests
import hmac
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.config import settings


class BinanceService:
    """Binance API service (testnet/mainnet)"""
    
    def __init__(self):
        if settings.BINANCE_USE_TESTNET:
            self.base_url = "https://testnet.binance.vision"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.base_url = "https://api.binance.com"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        self.api_key = settings.BINANCE_API_KEY
        self.api_secret = settings.BINANCE_API_SECRET
        self.session = requests.Session()  # Reuse session for better performance
        
        # 💾 Кэш для данных с таймстампами
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 120  # Считаем данные свежими 2 минуты
    
    def get_ticker_price(self, symbol: str = "BTCUSDT") -> Tuple[Optional[Decimal], bool]:
        """
        Получить текущую цену с Binance (с кэшированием и retry)
        
        Returns: (price, is_stale)
        - price: цена или None
        - is_stale: True если данные из кэша (старые)
        """
        url = f"{self.base_url}/api/v3/ticker/price"
        params = {"symbol": symbol}
        
        # Пытаемся получить свежие данные с retry (3 попытки по 7 секунд)
        response = self._fetch_with_retry(url, params, retries=3, timeout=7)
        
        if response:
            try:
                data = response.json()
                price = Decimal(str(data["price"]))
                self._set_cache(symbol, "price", price)
                return price, False  # Свежие данные
            except Exception as e:
                print(f"❌ Error parsing price: {e}")
        
        # Если не удалось получить - используем кэш
        cached_price, is_stale = self._get_cache(symbol, "price")
        if cached_price:
            print(f"⚠️ Using cached price for {symbol} (stale: {is_stale})")
            return cached_price, True
        
        print(f"❌ No data for {symbol} (fresh or cached)")
        return None, False
    
    def get_24h_ticker(self, symbol: str = "BTCUSDT") -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Получить 24h статистику (с кэшированием и retry)
        
        Returns: (ticker, is_stale)
        """
        url = f"{self.base_url}/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        
        response = self._fetch_with_retry(url, params, retries=3, timeout=7)
        
        if response:
            try:
                data = response.json()
                ticker = {
                    "symbol": data["symbol"],
                    "price": Decimal(str(data["lastPrice"])),
                    "change_24h": Decimal(str(data["priceChangePercent"])),
                    "high_24h": Decimal(str(data["highPrice"])),
                    "low_24h": Decimal(str(data["lowPrice"])),
                    "volume_24h": Decimal(str(data["volume"])),
                }
                self._set_cache(symbol, "ticker", ticker)
                return ticker, False
            except Exception as e:
                print(f"❌ Error parsing ticker: {e}")
        
        # Fallback на кэш
        cached_ticker, is_stale = self._get_cache(symbol, "ticker")
        if cached_ticker:
            print(f"⚠️ Using cached ticker for {symbol} (stale: {is_stale})")
            return cached_ticker, True
        
        return None, False
    
    def get_klines(
        self, 
        symbol: str = "BTCUSDT", 
        interval: str = "15m", 
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Получить свечи (OHLCV) для анализа (с кэшированием и retry)
        
        Returns: (candles, is_stale)
        """
        url = f"{self.base_url}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        
        response = self._fetch_with_retry(url, params, retries=3, timeout=7)
        
        if response:
            try:
                raw_data = response.json()
                candles = []
                for candle in raw_data:
                    candles.append({
                        "open_time": candle[0],
                        "open": Decimal(str(candle[1])),
                        "high": Decimal(str(candle[2])),
                        "low": Decimal(str(candle[3])),
                        "close": Decimal(str(candle[4])),
                        "volume": Decimal(str(candle[5])),
                        "close_time": candle[6],
                    })
                
                self._set_cache(symbol, "klines", candles)
                return candles, False
            except Exception as e:
                print(f"❌ Error parsing klines: {e}")
        
        # Fallback на кэш
        cached_klines, is_stale = self._get_cache(symbol, "klines")
        if cached_klines:
            print(f"⚠️ Using cached klines for {symbol} (stale: {is_stale})")
            return cached_klines, True
        
        return [], False
    
    def get_order_book(self, symbol: str = "BTCUSDT", limit: int = 10) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Получить order book (с кэшированием и retry)
        
        Returns: (order_book, is_stale)
        """
        url = f"{self.base_url}/api/v3/depth"
        params = {"symbol": symbol, "limit": limit}
        
        response = self._fetch_with_retry(url, params, retries=3, timeout=7)
        
        if response:
            try:
                data = response.json()
                order_book = {
                    "bids": [[Decimal(str(price)), Decimal(str(qty))] for price, qty in data["bids"]],
                    "asks": [[Decimal(str(price)), Decimal(str(qty))] for price, qty in data["asks"]],
                }
                self._set_cache(symbol, "orderbook", order_book)
                return order_book, False
            except Exception as e:
                print(f"❌ Error parsing order book: {e}")
        
        # Fallback на кэш
        cached_orderbook, is_stale = self._get_cache(symbol, "orderbook")
        if cached_orderbook:
            print(f"⚠️ Using cached order book for {symbol} (stale: {is_stale})")
            return cached_orderbook, True
        
        return None, False
    
    def _sign_request(self, params: Dict[str, Any]) -> str:
        """Sign request for authenticated endpoints (NOT USED in MVP - no real trading)"""
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        """Генерация ключа кэша"""
        return f"{symbol}_{data_type}"
    
    def _set_cache(self, symbol: str, data_type: str, data: Any) -> None:
        """Сохранение данных в кэш с таймстампом"""
        key = self._get_cache_key(symbol, data_type)
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.utcnow(),
            "is_stale": False
        }
    
    def _get_cache(self, symbol: str, data_type: str) -> Tuple[Optional[Any], bool]:
        """
        Получение данных из кэша
        Returns: (data, is_stale)
        - data: кэшированные данные или None
        - is_stale: True если данные старые (>2 мин)
        """
        key = self._get_cache_key(symbol, data_type)
        if key not in self._cache:
            return None, False
        
        cached = self._cache[key]
        age = (datetime.utcnow() - cached["timestamp"]).total_seconds()
        is_stale = age > self._cache_ttl
        
        return cached["data"], is_stale
    
    def _fetch_with_retry(self, url: str, params: Dict[str, Any], retries: int = 1, timeout: int = 7) -> Optional[requests.Response]:
        """
        Запрос с retry и оптимизированным timeout
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 200:
                    return response
            except requests.exceptions.Timeout:
                if attempt < retries - 1:
                    print(f"⚠️ Timeout (attempt {attempt + 1}/{retries}), retrying...")
                    time.sleep(0.5)
                    continue
                else:
                    print(f"❌ Final timeout after {retries} attempts")
            except Exception as e:
                print(f"❌ Request error: {e}")
                break
        
        return None
    
    def get_volume_analysis(self, symbol: str = "BTCUSDT") -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Получить анализ объёма для подтверждения движений
        
        Returns: (volume_data, is_stale)
        volume_data = {
            "current_5m_volume": Decimal,  # Объём текущей 5m свечи
            "avg_15m_volume": Decimal,      # Средний объём за 15 свечей (5m)
            "volume_ratio": float,          # current / avg (для AI prompt)
        }
        """
        # Получить последние 20 свечей 5m
        candles, is_stale = self.get_klines(symbol, interval="5m", limit=20)
        
        if not candles or len(candles) < 15:
            return None, is_stale
        
        try:
            # Текущий volume (последняя свеча)
            current_volume = candles[-1]["volume"]
            
            # Средний volume за последние 15 свечей (исключая текущую)
            volumes = [c["volume"] for c in candles[-16:-1]]  # Последние 15 закрытых свечей
            avg_volume = sum(volumes) / len(volumes)
            
            # Volume ratio (для AI анализа)
            volume_ratio = float(current_volume / avg_volume) if avg_volume > 0 else 1.0
            
            return {
                "current_5m_volume": current_volume,
                "avg_15m_volume": avg_volume,
                "volume_ratio": round(volume_ratio, 2),
            }, is_stale
            
        except Exception as e:
            print(f"❌ Error calculating volume analysis for {symbol}: {e}")
            return None, is_stale
    
    def calculate_ema(self, symbol: str = "BTCUSDT", period: int = 15) -> Tuple[Optional[Decimal], bool]:
        """
        Рассчитать EMA (Exponential Moving Average) для structure confirmation
        
        Returns: (ema_value, is_stale)
        """
        # Получить свечи (нужно period * 2 для точного расчёта EMA)
        candles, is_stale = self.get_klines(symbol, interval="5m", limit=period * 2)
        
        if not candles or len(candles) < period:
            return None, is_stale
        
        try:
            # Получить цены закрытия
            closes = [c["close"] for c in candles]
            
            # EMA расчёт
            # EMA = Price(t) * k + EMA(y) * (1 – k)
            # k = 2 / (period + 1)
            k = Decimal(2) / Decimal(period + 1)
            
            # Первая EMA = SMA (простое среднее)
            ema = sum(closes[:period]) / Decimal(period)
            
            # Рассчитываем EMA для остальных точек
            for i in range(period, len(closes)):
                ema = closes[i] * k + ema * (Decimal(1) - k)
            
            return ema, is_stale
            
        except Exception as e:
            print(f"❌ Error calculating EMA for {symbol}: {e}")
            return None, is_stale


# Singleton instance
binance_service = BinanceService()



