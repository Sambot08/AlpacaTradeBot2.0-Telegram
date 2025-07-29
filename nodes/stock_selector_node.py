"""
Stock Selector Node - AI-powered stock selection for trading
"""

import logging
import requests
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class StockSelectorNode:
    """Node for intelligent stock selection using multiple criteria"""
    
    def __init__(self):
        self.config = Config()
        self.alpaca_headers = {
            'APCA-API-KEY-ID': self.config.ALPACA_API_KEY,
            'APCA-API-SECRET-KEY': self.config.ALPACA_SECRET_KEY,
        }
        
        # Stock universe - popular and liquid stocks
        self.stock_universe = [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK',
            # Consumer
            'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM',
            # Energy
            'XOM', 'CVX', 'COP',
            # ETFs for diversification
            'SPY', 'QQQ', 'IWM', 'VTI'
        ]
        
        logger.info("Stock Selector Node initialized")
    
    def select_trading_candidates(self, max_stocks: int = 5) -> List[str]:
        """Select the best stocks to trade based on multiple criteria"""
        try:
            logger.info(f"Selecting top {max_stocks} trading candidates...")
            
            # Get market data for all stocks
            stock_data = self._get_market_data_batch(self.stock_universe)
            
            if not stock_data:
                logger.warning("No market data available, using default stocks")
                return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY']
            
            # Score each stock
            scored_stocks = []
            for symbol, data in stock_data.items():
                score = self._calculate_stock_score(symbol, data)
                if score > 0:
                    scored_stocks.append({
                        'symbol': symbol,
                        'score': score,
                        'data': data
                    })
            
            # Sort by score and select top candidates
            scored_stocks.sort(key=lambda x: x['score'], reverse=True)
            selected = [stock['symbol'] for stock in scored_stocks[:max_stocks]]
            
            logger.info(f"Selected stocks for trading: {selected}")
            
            # Log selection reasoning
            for i, stock in enumerate(scored_stocks[:max_stocks]):
                logger.info(f"#{i+1} {stock['symbol']}: score={stock['score']:.2f}")
            
            return selected
            
        except Exception as e:
            logger.error(f"Stock selection error: {str(e)}")
            # Fallback to default selection
            return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY']
    
    def _get_market_data_batch(self, symbols: List[str]) -> Dict:
        """Get market data for multiple symbols efficiently"""
        try:
            market_data = {}
            
            # Get quotes for all symbols
            symbols_str = ','.join(symbols)
            url = f"{self.config.ALPACA_DATA_URL}/v2/stocks/quotes/latest"
            params = {'symbols': symbols_str}
            
            response = requests.get(url, headers=self.alpaca_headers, params=params)
            
            if response.status_code == 200:
                quotes_data = response.json().get('quotes', {})
                
                # Get bars for technical analysis
                bars_url = f"{self.config.ALPACA_DATA_URL}/v2/stocks/bars/latest"
                bars_response = requests.get(bars_url, headers=self.alpaca_headers, params=params)
                bars_data = {}
                
                if bars_response.status_code == 200:
                    bars_data = bars_response.json().get('bars', {})
                
                # Get historical bars for trend analysis
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)
                
                hist_params = {
                    'symbols': symbols_str,
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'timeframe': '1Day',
                    'limit': 30
                }
                
                hist_url = f"{self.config.ALPACA_DATA_URL}/v2/stocks/bars"
                hist_response = requests.get(hist_url, headers=self.alpaca_headers, params=hist_params)
                hist_data = {}
                
                if hist_response.status_code == 200:
                    hist_data = hist_response.json().get('bars', {})
                
                # Combine all data
                for symbol in symbols:
                    if symbol in quotes_data:
                        quote = quotes_data[symbol]
                        bar = bars_data.get(symbol, {})
                        hist_bars = hist_data.get(symbol, [])
                        
                        market_data[symbol] = {
                            'quote': quote,
                            'latest_bar': bar,
                            'historical_bars': hist_bars,
                            'price': self._get_price_from_quote(quote),
                            'volume': bar.get('volume', 0)
                        }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Batch market data error: {str(e)}")
            return {}
    
    def _calculate_stock_score(self, symbol: str, data: Dict) -> float:
        """Calculate a composite score for stock selection"""
        try:
            score = 0.0
            
            # Base score for all stocks
            score += 10.0
            
            # Price and volume criteria
            price = data.get('price', 0)
            volume = data.get('volume', 0)
            
            # Price range preference (avoid penny stocks and very expensive stocks)
            if 10 <= price <= 500:
                score += 15.0
            elif 5 <= price < 10 or 500 < price <= 1000:
                score += 8.0
            else:
                score -= 5.0
            
            # Volume preference (higher volume = better liquidity)
            if volume > 1000000:  # 1M+ volume
                score += 20.0
            elif volume > 500000:  # 500K+ volume
                score += 15.0
            elif volume > 100000:  # 100K+ volume
                score += 10.0
            else:
                score -= 10.0  # Low volume penalty
            
            # Historical analysis
            hist_bars = data.get('historical_bars', [])
            if len(hist_bars) >= 20:
                score += self._analyze_technical_patterns(hist_bars)
            
            # Sector preferences
            score += self._get_sector_preference_score(symbol)
            
            # Volatility analysis
            if hist_bars:
                volatility_score = self._calculate_volatility_score(hist_bars)
                score += volatility_score
            
            return max(0, score)  # Ensure non-negative score
            
        except Exception as e:
            logger.error(f"Score calculation error for {symbol}: {str(e)}")
            return 0.0
    
    def _analyze_technical_patterns(self, bars: List[Dict]) -> float:
        """Analyze technical patterns for scoring"""
        try:
            if len(bars) < 20:
                return 0
            
            score = 0.0
            closes = [float(bar['close']) for bar in bars[-20:]]
            
            # Moving average trend
            recent_avg = sum(closes[-5:]) / 5
            older_avg = sum(closes[-20:-15]) / 5
            
            if recent_avg > older_avg:
                score += 10.0  # Uptrend bonus
            else:
                score -= 5.0   # Downtrend penalty
            
            # Price momentum
            current_price = closes[-1]
            week_ago_price = closes[-5] if len(closes) >= 5 else current_price
            
            momentum = (current_price - week_ago_price) / week_ago_price * 100
            
            if -2 <= momentum <= 8:  # Moderate positive momentum
                score += 15.0
            elif momentum > 8:  # Strong momentum but might be overbought
                score += 5.0
            elif momentum < -5:  # Strong negative momentum
                score -= 10.0
            
            # Volatility check
            daily_returns = []
            for i in range(1, len(closes)):
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                daily_returns.append(ret)
            
            if daily_returns:
                volatility = (sum(r*r for r in daily_returns) / len(daily_returns)) ** 0.5
                
                if 0.01 <= volatility <= 0.04:  # Moderate volatility
                    score += 10.0
                elif volatility > 0.06:  # High volatility
                    score -= 5.0
            
            return score
            
        except Exception as e:
            logger.error(f"Technical analysis error: {str(e)}")
            return 0.0
    
    def _get_sector_preference_score(self, symbol: str) -> float:
        """Give preference scores based on sector/stock type"""
        
        # Tech stocks preference
        tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX']
        if symbol in tech_stocks:
            return 15.0
        
        # Financial sector
        finance_stocks = ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA']
        if symbol in finance_stocks:
            return 12.0
        
        # ETFs for stability
        etfs = ['SPY', 'QQQ', 'IWM', 'VTI']
        if symbol in etfs:
            return 10.0
        
        # Consumer staples
        consumer_stocks = ['KO', 'PEP', 'WMT', 'HD', 'MCD']
        if symbol in consumer_stocks:
            return 8.0
        
        # Healthcare
        healthcare_stocks = ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK']
        if symbol in healthcare_stocks:
            return 7.0
        
        return 5.0  # Default for other stocks
    
    def _calculate_volatility_score(self, bars: List[Dict]) -> float:
        """Calculate volatility-based score"""
        try:
            if len(bars) < 10:
                return 0
            
            closes = [float(bar['close']) for bar in bars[-10:]]
            returns = []
            
            for i in range(1, len(closes)):
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(ret)
            
            if not returns:
                return 0
            
            # Calculate standard deviation
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
            
            # Optimal volatility range for trading
            if 0.015 <= volatility <= 0.035:  # 1.5% to 3.5% daily volatility
                return 15.0
            elif 0.01 <= volatility < 0.015 or 0.035 < volatility <= 0.05:
                return 8.0
            elif volatility > 0.08:  # Very high volatility
                return -10.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Volatility score error: {str(e)}")
            return 0.0
    
    def _get_price_from_quote(self, quote: Dict) -> float:
        """Extract price from quote data"""
        try:
            bid = float(quote.get('bid_price', 0))
            ask = float(quote.get('ask_price', 0))
            
            if bid > 0 and ask > 0:
                return (bid + ask) / 2
            elif bid > 0:
                return bid
            elif ask > 0:
                return ask
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Price extraction error: {str(e)}")
            return 0.0
    
    def get_market_sectors_analysis(self) -> Dict:
        """Analyze performance by market sectors"""
        try:
            sectors = {
                'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA'],
                'Finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA'],
                'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK'],
                'Consumer': ['KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE'],
                'Energy': ['XOM', 'CVX', 'COP']
            }
            
            sector_performance = {}
            
            for sector, symbols in sectors.items():
                sector_data = self._get_market_data_batch(symbols[:3])  # Limit for efficiency
                
                if sector_data:
                    total_score = sum(
                        self._calculate_stock_score(symbol, data) 
                        for symbol, data in sector_data.items()
                    )
                    avg_score = total_score / len(sector_data) if sector_data else 0
                    
                    sector_performance[sector] = {
                        'average_score': round(avg_score, 2),
                        'stocks_analyzed': len(sector_data),
                        'recommendation': 'BUY' if avg_score > 50 else 'HOLD' if avg_score > 30 else 'AVOID'
                    }
            
            return sector_performance
            
        except Exception as e:
            logger.error(f"Sector analysis error: {str(e)}")
            return {}
    
    def update_stock_universe(self, new_symbols: List[str]):
        """Update the stock universe with new symbols"""
        try:
            # Validate symbols format
            valid_symbols = [s.upper().strip() for s in new_symbols if s.strip().isalpha()]
            
            if valid_symbols:
                self.stock_universe.extend(valid_symbols)
                # Remove duplicates
                self.stock_universe = list(set(self.stock_universe))
                logger.info(f"Updated stock universe with {len(valid_symbols)} new symbols")
            else:
                logger.warning("No valid symbols provided for universe update")
                
        except Exception as e:
            logger.error(f"Stock universe update error: {str(e)}")