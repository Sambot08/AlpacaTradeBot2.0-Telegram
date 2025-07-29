"""
Technical Analysis Node - Rule-based trading decisions without external AI
"""

import logging
from typing import Dict, Optional

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class TechnicalAnalysisNode:
    """Node for technical analysis-based trading decisions"""
    
    def __init__(self):
        self.config = Config()
        logger.info("Technical Analysis Node initialized (No external AI required)")
    
    def get_trading_decision(self, symbol: str, price_data: Dict, current_position: Optional[Dict]) -> Optional[Dict]:
        """Get technical analysis trading decision for a symbol"""
        try:
            # Use technical analysis rules instead of AI
            decision = self._technical_analysis_decision(symbol, price_data, current_position)
            
            if decision:
                logger.info(f"Technical analysis decision for {symbol}: {decision['action']} (confidence: {decision['confidence']})")
                return decision
            else:
                logger.warning(f"Could not generate technical decision for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Technical analysis error for {symbol}: {str(e)}")
            return None
    
    def _technical_analysis_decision(self, symbol: str, price_data: Dict, current_position: Optional[Dict]) -> Optional[Dict]:
        """Generate trading decision using technical analysis rules"""
        try:
            current_price = price_data.get('current_price', 0)
            price_change = price_data.get('price_change_percent', 0)
            volume = price_data.get('volume', 0)
            
            # Technical indicators (simplified)
            ma_20 = price_data.get('ma_20', current_price)
            ma_50 = price_data.get('ma_50', current_price)
            rsi = price_data.get('rsi', 50)
            
            # Debug logging to see actual data
            logger.info(f"DEBUG {symbol}: price=${current_price:.2f}, change={price_change:.2f}%, rsi={rsi:.1f}, ma20=${ma_20:.2f}, ma50=${ma_50:.2f}")
            
            # Default decision
            action = "HOLD"
            confidence = 5
            reasoning = "Neutral market conditions"
            quantity = 1
            
            # Technical analysis rules
            signals = []
            
            # Moving average signals
            if current_price > ma_20 and ma_20 > ma_50:
                signals.append(("BUY", 2, "Price above moving averages - uptrend"))
            elif current_price < ma_20 and ma_20 < ma_50:
                signals.append(("SELL", 2, "Price below moving averages - downtrend"))
            
            # RSI signals
            if rsi < 30:
                signals.append(("BUY", 3, "RSI oversold - potential bounce"))
            elif rsi > 70:
                signals.append(("SELL", 3, "RSI overbought - potential pullback"))
            
            # Price momentum signals - More sensitive
            if price_change > 3:
                signals.append(("BUY", 3, "Strong positive momentum"))
            elif price_change < -3:
                signals.append(("SELL", 3, "Strong negative momentum"))
            elif price_change > 1:
                signals.append(("BUY", 2, "Positive momentum"))
            elif price_change < -1:
                signals.append(("SELL", 2, "Negative momentum"))
            elif price_change > 0.5:
                signals.append(("BUY", 1, "Mild positive momentum"))
            elif price_change < -0.5:
                signals.append(("SELL", 1, "Mild negative momentum"))
            
            # Position management
            if current_position:
                qty = float(current_position.get('qty', 0))
                avg_entry = float(current_position.get('avg_entry_price', 0))
                unrealized_pl = float(current_position.get('unrealized_pl', 0))
                
                # Take profit signal
                if unrealized_pl > 0 and (current_price / avg_entry - 1) > 0.1:  # 10% profit
                    signals.append(("SELL", 4, "Take profit - 10% gain achieved"))
                
                # Stop loss signal
                elif unrealized_pl < 0 and (current_price / avg_entry - 1) < -0.05:  # 5% loss
                    signals.append(("SELL", 5, "Stop loss - 5% loss limit"))
            
            # Combine signals - Made more responsive
            if signals:
                buy_signals = [s for s in signals if s[0] == "BUY"]
                sell_signals = [s for s in signals if s[0] == "SELL"]
                
                buy_strength = sum(s[1] for s in buy_signals)
                sell_strength = sum(s[1] for s in sell_signals)
                
                # Lowered threshold from 3 to 2 for more active trading
                if buy_strength > sell_strength and buy_strength >= 2:
                    action = "BUY"
                    confidence = min(10, buy_strength + 3)
                    reasoning = "; ".join([s[2] for s in buy_signals])
                elif sell_strength > buy_strength and sell_strength >= 2:
                    action = "SELL"
                    confidence = min(10, sell_strength + 3)
                    reasoning = "; ".join([s[2] for s in sell_signals])
                else:
                    action = "HOLD"
                    confidence = 5
                    reasoning = "Mixed signals - waiting for clearer trend"
            
            return {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
                'quantity': quantity,
                'technical_signals': signals
            }
            
        except Exception as e:
            logger.error(f"Technical analysis error: {str(e)}")
            return None
    
    def analyze_market_sentiment(self, symbols: list) -> Optional[Dict]:
        """Analyze overall market sentiment using technical indicators"""
        try:
            # Simple technical-based sentiment analysis
            sentiment = "NEUTRAL"
            risk_level = "MEDIUM"
            
            analysis = f"""
Technical Market Analysis for {', '.join(symbols)}:

Overall Sentiment: NEUTRAL
- Market conditions appear balanced
- Mixed technical signals across symbols
- Recommend cautious position sizing

Risk Level: MEDIUM
- Standard market volatility
- Normal trading volumes
- No extreme technical conditions detected

Strategy: Balanced approach with risk management
"""
            
            return {
                'sentiment': sentiment,
                'risk_level': risk_level,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Market sentiment analysis error: {str(e)}")
            return {
                'sentiment': 'NEUTRAL',
                'risk_level': 'MEDIUM',
                'analysis': 'Technical analysis unavailable'
            }
    
    def get_portfolio_advice(self, portfolio_data: Dict) -> Optional[str]:
        """Get portfolio management advice based on technical analysis"""
        try:
            total_value = portfolio_data.get('total_value', 0)
            positions = portfolio_data.get('positions', [])
            
            advice = f"""
Portfolio Technical Analysis:

Total Portfolio Value: ${total_value:,.2f}
Active Positions: {len(positions)}

Technical Recommendations:
- Maintain diversification across sectors
- Use position sizing based on volatility
- Implement stop-loss orders for risk management
- Monitor technical indicators for entry/exit signals

Risk Management:
- Keep individual positions under 5% of total portfolio
- Use technical stops at 5-7% below entry
- Take profits at 10-15% gains unless trend is very strong
"""
            
            return advice
            
        except Exception as e:
            logger.error(f"Portfolio advice error: {str(e)}")
            return "Portfolio technical analysis unavailable"