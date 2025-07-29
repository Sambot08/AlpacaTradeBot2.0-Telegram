"""
Stock Selector Node - AI-powered stock selection for trading
"""

import logging
import requests
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta
import openai

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class StockSelectorNode:
    """Node for intelligent stock selection using multiple criteria"""
    
    def __init__(self):
        self.config = Config()
        self.client = openai.OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.alpaca_headers = {
            'APCA-API-KEY-ID': self.config.ALPACA_API_KEY,
            'APCA-API-SECRET-KEY': self.config.ALPACA_SECRET_KEY,
        }
        
        # Sector ETFs for dynamic weighting
        self.sector_etfs = {
            'XLK': 'Technology',
            'XLF': 'Financial', 
            'XLV': 'Healthcare',
            'XLI': 'Industrial',
            'XLE': 'Energy',
            'XLY': 'Consumer Discretionary',
            'XLP': 'Consumer Staples',
            'XLU': 'Utilities',
            'XLB': 'Materials'
        }
        
        # Stock to sector mapping
        self.stock_sectors = {
            # Tech
            'AAPL': 'XLK', 'MSFT': 'XLK', 'GOOGL': 'XLK', 'AMZN': 'XLK', 'META': 'XLK', 
            'TSLA': 'XLK', 'NVDA': 'XLK', 'NFLX': 'XLK',
            # Finance
            'JPM': 'XLF', 'BAC': 'XLF', 'WFC': 'XLF', 'GS': 'XLF', 'MS': 'XLF', 'V': 'XLF', 'MA': 'XLF',
            # Healthcare
            'JNJ': 'XLV', 'PFE': 'XLV', 'UNH': 'XLV', 'ABBV': 'XLV', 'MRK': 'XLV',
            # Consumer
            'KO': 'XLP', 'PEP': 'XLP', 'WMT': 'XLP', 'HD': 'XLY', 'MCD': 'XLP', 'NKE': 'XLY',
            # Industrial
            'BA': 'XLI', 'CAT': 'XLI', 'GE': 'XLI', 'MMM': 'XLI',
            # Energy
            'XOM': 'XLE', 'CVX': 'XLE', 'COP': 'XLE'
        }
        
        # Trade history for learning
        self.trade_history = []
        
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
            
            # 1. Check time-of-day awareness
            current_time = datetime.now().time()
            time_factor = self._get_time_factor(current_time)
            
            # 2. Get dynamic sector weights
            sector_weights = self._get_dynamic_sector_weights()
            
            # 3. Get market data for all stocks
            stock_data = self._get_market_data_batch(self.stock_universe)
            
            if not stock_data:
                logger.warning("No market data available, using default stocks")
                return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY']
            
            # 4. Score each stock with enhanced criteria
            scored_stocks = []
            for symbol, data in stock_data.items():
                try:
                    base_score = self._calculate_stock_score(symbol, data)
                    
                    # Apply sector weighting
                    sector = self.stock_sectors.get(symbol)
                    sector_bonus = sector_weights.get(sector, 1.0) if sector else 1.0
                    
                    # Apply time factor
                    adjusted_score = base_score * sector_bonus * time_factor
                    
                    # Signal confirmation layer
                    if self._has_confirmation_signals(symbol, data):
                        adjusted_score *= 1.2  # 20% bonus for confirmed signals
                    
                    if adjusted_score > 0:
                        scored_stocks.append({
                            'symbol': symbol,
                            'score': adjusted_score,
                            'data': data,
                            'sector': sector,
                            'sector_bonus': sector_bonus
                        })
                        
                except Exception as e:
                    logger.warning(f"Scoring error for {symbol}: {str(e)}")
                    continue
            
            # 5. Sort by score and get top candidates
            scored_stocks.sort(key=lambda x: x['score'], reverse=True)
            top_candidates = scored_stocks[:max_stocks * 2]  # Get 2x for LLM filtering
            
            # 6. Apply LLM sentiment filter (if available)
            selected = self._apply_llm_sentiment_filter(top_candidates, max_stocks)
            
            logger.info(f"Selected stocks for trading: {selected}")
            
            # Log selection reasoning with enhanced details
            for i, stock in enumerate(selected[:max_stocks]):
                stock_info = next((s for s in scored_stocks if s['symbol'] == stock), None)
                if stock_info:
                    logger.info(f"#{i+1} {stock}: score={stock_info['score']:.2f}, sector={stock_info.get('sector', 'N/A')}, sector_bonus={stock_info.get('sector_bonus', 1.0):.2f}")
            
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
    
    def _get_time_factor(self, current_time) -> float:
        """Calculate time-based adjustment factor"""
        try:
            hour = current_time.hour
            minute = current_time.minute
            
            # Market hours: 9:30 AM - 4:00 PM ET
            # High activity periods: market open (9:30-10:30) and close (3:00-4:00)
            # Low activity: lunch time (12:00-2:00)
            
            if hour == 9 and minute >= 30:  # Market open hour
                return 1.3  # 30% boost for market open
            elif hour == 15:  # Market close hour (3 PM)
                return 1.2  # 20% boost for market close
            elif 12 <= hour <= 13:  # Lunch hours
                return 0.8  # 20% reduction for low volume period
            elif 10 <= hour <= 14:  # Normal trading hours
                return 1.0  # Normal factor
            else:  # After hours
                return 0.9  # Slight reduction for after hours
                
        except Exception as e:
            logger.warning(f"Time factor calculation error: {str(e)}")
            return 1.0
    
    def _get_dynamic_sector_weights(self) -> Dict[str, float]:
        """Calculate dynamic sector weights based on recent performance"""
        try:
            sector_performance = {}
            
            # Get 7-day performance for each sector ETF
            for etf_symbol, sector_name in self.sector_etfs.items():
                try:
                    # Get recent price data for sector ETF
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)
                    
                    url = f"{self.config.ALPACA_DATA_URL}/v2/stocks/bars"
                    params = {
                        'symbols': etf_symbol,
                        'timeframe': '1Day',
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d')
                    }
                    
                    response = requests.get(url, headers=self.alpaca_headers, params=params)
                    
                    if response.status_code == 200:
                        data = response.json().get('bars', {}).get(etf_symbol, [])
                        if len(data) >= 2:
                            # Calculate 7-day return
                            latest_close = float(data[-1]['c'])
                            week_ago_close = float(data[0]['c'])
                            weekly_return = (latest_close - week_ago_close) / week_ago_close
                            sector_performance[etf_symbol] = weekly_return
                        else:
                            sector_performance[etf_symbol] = 0.0
                    else:
                        sector_performance[etf_symbol] = 0.0
                        
                except Exception as e:
                    logger.warning(f"Sector performance error for {etf_symbol}: {str(e)}")
                    sector_performance[etf_symbol] = 0.0
            
            # Convert performance to weights (outperforming sectors get higher weights)
            if sector_performance:
                avg_performance = sum(sector_performance.values()) / len(sector_performance)
                sector_weights = {}
                
                for etf, performance in sector_performance.items():
                    if performance > avg_performance:
                        weight = 1.0 + min((performance - avg_performance) * 5, 0.5)  # Max 50% bonus
                    else:
                        weight = 1.0 + max((performance - avg_performance) * 3, -0.3)  # Max 30% penalty
                    sector_weights[etf] = weight
                    
                logger.info(f"Dynamic sector weights: {sector_weights}")
                return sector_weights
            else:
                # Fallback to equal weights
                return {etf: 1.0 for etf in self.sector_etfs.keys()}
                
        except Exception as e:
            logger.warning(f"Dynamic sector weighting error: {str(e)}")
            return {etf: 1.0 for etf in self.sector_etfs.keys()}
    
    def _has_confirmation_signals(self, symbol: str, data: Dict) -> bool:
        """Check for signal confirmation indicators"""
        try:
            current_price = float(data.get('price', 0))
            volume = int(data.get('volume', 0))
            avg_volume = int(data.get('avg_volume', volume))
            
            confirmations = 0
            
            # Volume confirmation (higher than average)
            if volume > avg_volume * 1.5:
                confirmations += 1
            
            # Price momentum confirmation
            price_change_pct = float(data.get('change_percent', 0))
            if abs(price_change_pct) > 2.0:  # Significant price movement
                confirmations += 1
            
            # Technical breakout confirmation (simplified)
            high_52w = float(data.get('high_52w', current_price))
            low_52w = float(data.get('low_52w', current_price))
            
            # Near 52-week high (potential breakout)
            if current_price > high_52w * 0.95:
                confirmations += 1
            
            # Return True if at least 2 confirmations
            return confirmations >= 2
            
        except Exception as e:
            logger.warning(f"Confirmation signals error for {symbol}: {str(e)}")
            return False
    
    def _apply_llm_sentiment_filter(self, candidates: List[Dict], max_stocks: int) -> List[str]:
        """Apply LLM sentiment analysis to filter final selections"""
        try:
            if not candidates:
                return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY']
            
            # Extract top symbols for LLM analysis
            symbols = [c['symbol'] for c in candidates[:max_stocks * 2]]
            
            # Get sentiment scores (with fallback if LLM fails)
            sentiment_scores = self._get_llm_sentiment_scores(symbols)
            
            # Combine technical scores with sentiment
            final_scores = []
            for candidate in candidates:
                symbol = candidate['symbol']
                technical_score = candidate['score']
                sentiment_score = sentiment_scores.get(symbol, 0.5)  # Neutral if no sentiment
                
                # Weight: 70% technical, 30% sentiment
                combined_score = technical_score * 0.7 + sentiment_score * technical_score * 0.3
                
                final_scores.append({
                    'symbol': symbol,
                    'combined_score': combined_score,
                    'technical_score': technical_score,
                    'sentiment_score': sentiment_score
                })
            
            # Sort by combined score and return top selections
            final_scores.sort(key=lambda x: x['combined_score'], reverse=True)
            selected = [stock['symbol'] for stock in final_scores[:max_stocks]]
            
            # Log the reasoning
            logger.info("LLM-enhanced selection reasoning:")
            for i, stock in enumerate(final_scores[:max_stocks]):
                logger.info(f"#{i+1} {stock['symbol']}: combined={stock['combined_score']:.2f}, technical={stock['technical_score']:.2f}, sentiment={stock['sentiment_score']:.2f}")
            
            return selected
            
        except Exception as e:
            logger.warning(f"LLM sentiment filter error: {str(e)}")
            # Fallback to technical scores only
            return [c['symbol'] for c in candidates[:max_stocks]]
    
    def _get_llm_sentiment_scores(self, symbols: List[str]) -> Dict[str, float]:
        """Get sentiment scores from LLM for given symbols"""
        try:
            symbols_str = ", ".join(symbols)
            
            prompt = f"""
            Analyze market sentiment for these stocks: {symbols_str}
            
            For each stock, provide a sentiment score from 0.0 to 1.0 where:
            - 0.0-0.3 = Bearish/Negative
            - 0.4-0.6 = Neutral
            - 0.7-1.0 = Bullish/Positive
            
            Consider recent market trends, sector performance, and any notable developments.
            
            Respond ONLY in this JSON format:
            {{
                "AAPL": 0.8,
                "MSFT": 0.7,
                ...
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a market sentiment analyst. Provide only JSON responses with sentiment scores."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            if not response_text:
                return {}
                
            # Parse JSON response
            sentiment_data = json.loads(response_text.strip())
            
            # Validate and normalize scores
            sentiment_scores = {}
            for symbol, score in sentiment_data.items():
                if isinstance(score, (int, float)) and 0.0 <= score <= 1.0:
                    sentiment_scores[symbol] = float(score)
                else:
                    sentiment_scores[symbol] = 0.5  # Default neutral
                    
            logger.info(f"LLM sentiment scores: {sentiment_scores}")
            return sentiment_scores
            
        except Exception as e:
            logger.warning(f"LLM sentiment analysis error: {str(e)}")
            # Return neutral scores for all symbols
            return {symbol: 0.5 for symbol in symbols}
    
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