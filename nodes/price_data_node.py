"""
Price Data Node - Fetches price data from multiple sources
"""

import logging
import requests
from typing import Dict, Optional, List
import json
from datetime import datetime, timedelta

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class PriceDataNode:
    """Node for fetching price data with fallback sources"""
    
    def __init__(self):
        self.config = Config()
        self.alpaca_headers = {
            'APCA-API-KEY-ID': self.config.ALPACA_API_KEY,
            'APCA-API-SECRET-KEY': self.config.ALPACA_SECRET_KEY,
        }
        
        logger.info("Price Data Node initialized")
    
    def get_price_data(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive price data for a symbol with fallback sources"""
        try:
            # Try Alpaca first (primary source)
            price_data = self._get_alpaca_price_data(symbol)
            
            if price_data:
                logger.info(f"Got price data from Alpaca for {symbol}")
                return price_data
            
            # Fallback to Alpha Vantage
            logger.warning(f"Alpaca failed for {symbol}, trying Alpha Vantage")
            price_data = self._get_alpha_vantage_data(symbol)
            
            if price_data:
                logger.info(f"Got price data from Alpha Vantage for {symbol}")
                return price_data
            
            logger.error(f"All price data sources failed for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Price data error for {symbol}: {str(e)}")
            return None
    
    def _get_alpaca_price_data(self, symbol: str) -> Optional[Dict]:
        """Get price data from Alpaca"""
        try:
            # Get latest quote
            quote_url = f"{self.config.ALPACA_DATA_URL}/v2/stocks/{symbol}/quotes/latest"
            quote_response = requests.get(quote_url, headers=self.alpaca_headers)
            
            if quote_response.status_code != 200:
                logger.warning(f"Alpaca quote failed for {symbol}: {quote_response.status_code}")
                return None
            
            quote_data = quote_response.json().get('quote', {})
            
            # Get latest trade
            trade_url = f"{self.config.ALPACA_DATA_URL}/v2/stocks/{symbol}/trades/latest"
            trade_response = requests.get(trade_url, headers=self.alpaca_headers)
            
            trade_data = {}
            if trade_response.status_code == 200:
                trade_data = trade_response.json().get('trade', {})
            
            # Get bars for historical data
            bars_url = f"{self.config.ALPACA_DATA_URL}/v2/stocks/{symbol}/bars"
            end_time = datetime.now()
            start_time = end_time - timedelta(days=60)  # 60 days of data
            
            bars_params = {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'timeframe': '1Day',
                'limit': 50
            }
            
            bars_response = requests.get(bars_url, headers=self.alpaca_headers, params=bars_params)
            bars_data = []
            if bars_response.status_code == 200:
                bars_data = bars_response.json().get('bars', [])
            
            # Calculate current price
            current_price = 0
            if trade_data.get('price'):
                current_price = float(trade_data['price'])
            elif quote_data.get('bid_price') and quote_data.get('ask_price'):
                bid = float(quote_data['bid_price'])
                ask = float(quote_data['ask_price'])
                current_price = (bid + ask) / 2
            
            if current_price == 0:
                return None
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(bars_data, current_price)
            
            # Build comprehensive price data
            price_data = {
                'symbol': symbol,
                'current_price': current_price,
                'bid_price': float(quote_data.get('bid_price', 0)),
                'ask_price': float(quote_data.get('ask_price', 0)),
                'volume': int(trade_data.get('size', 0)),
                'timestamp': datetime.now().isoformat(),
                'source': 'alpaca',
                **indicators
            }
            
            return price_data
            
        except Exception as e:
            logger.error(f"Alpaca price data error for {symbol}: {str(e)}")
            return None
    
    def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Get price data from Alpha Vantage as fallback"""
        try:
            if not self.config.ALPHA_VANTAGE_API_KEY:
                logger.warning("Alpha Vantage API key not configured")
                return None
            
            # Get intraday data
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': '5min',
                'apikey': self.config.ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Check for API limit or error
            if 'Error Message' in data or 'Note' in data:
                logger.warning(f"Alpha Vantage API issue: {data}")
                return None
            
            time_series = data.get('Time Series (5min)', {})
            if not time_series:
                return None
            
            # Get latest data point
            latest_time = max(time_series.keys())
            latest_data = time_series[latest_time]
            
            current_price = float(latest_data['4. close'])
            volume = int(latest_data['5. volume'])
            
            # Get daily data for indicators
            daily_params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.config.ALPHA_VANTAGE_API_KEY
            }
            
            daily_response = requests.get(url, params=daily_params)
            daily_data = {}
            if daily_response.status_code == 200:
                daily_json = daily_response.json()
                daily_data = daily_json.get('Time Series (Daily)', {})
            
            # Calculate indicators from daily data
            bars_data = []
            for date, values in list(daily_data.items())[:50]:
                bars_data.append({
                    'close': float(values['4. close']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'volume': int(values['5. volume'])
                })
            
            indicators = self._calculate_indicators(bars_data, current_price)
            
            price_data = {
                'symbol': symbol,
                'current_price': current_price,
                'volume': volume,
                'timestamp': datetime.now().isoformat(),
                'source': 'alpha_vantage',
                **indicators
            }
            
            return price_data
            
        except Exception as e:
            logger.error(f"Alpha Vantage price data error for {symbol}: {str(e)}")
            return None
    
    def _calculate_indicators(self, bars_data: List[Dict], current_price: float) -> Dict:
        """Calculate technical indicators from historical data"""
        try:
            if len(bars_data) < 20:
                # Not enough data for indicators
                return {
                    'ma_20': current_price,
                    'ma_50': current_price,
                    'rsi': 50,
                    'price_change_percent': 0,
                    'volatility': 0
                }
            
            # Extract closing prices
            closes = [float(bar.get('close', current_price)) for bar in bars_data]
            closes.reverse()  # Ensure chronological order
            
            # Add current price
            closes.append(current_price)
            
            # Moving averages
            ma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
            ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else current_price
            
            # Price change percentage (from yesterday)
            price_change_percent = 0
            if len(closes) > 1:
                yesterday_price = closes[-2]
                price_change_percent = ((current_price - yesterday_price) / yesterday_price) * 100
            
            # RSI calculation (simplified)
            rsi = self._calculate_rsi(closes[-14:]) if len(closes) >= 14 else 50
            
            # Volatility (standard deviation of returns)
            volatility = 0
            if len(closes) > 10:
                returns = []
                for i in range(1, min(21, len(closes))):
                    ret = (closes[-i] - closes[-i-1]) / closes[-i-1]
                    returns.append(ret)
                
                if returns:
                    avg_return = sum(returns) / len(returns)
                    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                    volatility = (variance ** 0.5) * 100  # As percentage
            
            return {
                'ma_20': round(ma_20, 2),
                'ma_50': round(ma_50, 2),
                'rsi': round(rsi, 1),
                'price_change_percent': round(price_change_percent, 2),
                'volatility': round(volatility, 2)
            }
            
        except Exception as e:
            logger.error(f"Indicators calculation error: {str(e)}")
            return {
                'ma_20': current_price,
                'ma_50': current_price,
                'rsi': 50,
                'price_change_percent': 0,
                'volatility': 0
            }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"RSI calculation error: {str(e)}")
            return 50.0
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get price data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                price_data = self.get_price_data(symbol)
                if price_data:
                    results[symbol] = price_data
                else:
                    logger.warning(f"Failed to get price data for {symbol}")
            except Exception as e:
                logger.error(f"Error getting data for {symbol}: {str(e)}")
        
        return results
