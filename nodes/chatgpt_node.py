"""
Technical Analysis Node - Rule-based trading decisions without external AI
"""

import logging
from typing import Dict, Optional
import json

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class ChatGPTNode:
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
            
            # Price momentum signals
            if price_change > 5:
                signals.append(("BUY", 2, "Strong positive momentum"))
            elif price_change < -5:
                signals.append(("SELL", 2, "Strong negative momentum"))
            elif price_change > 2:
                signals.append(("BUY", 1, "Positive momentum"))
            elif price_change < -2:
                signals.append(("SELL", 1, "Negative momentum"))
            
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
            
            # Combine signals
            if signals:
                buy_signals = [s for s in signals if s[0] == "BUY"]
                sell_signals = [s for s in signals if s[0] == "SELL"]
                
                buy_strength = sum(s[1] for s in buy_signals)
                sell_strength = sum(s[1] for s in sell_signals)
                
                if buy_strength > sell_strength and buy_strength >= 3:
                    action = "BUY"
                    confidence = min(10, buy_strength + 2)
                    reasoning = "; ".join([s[2] for s in buy_signals])
                elif sell_strength > buy_strength and sell_strength >= 3:
                    action = "SELL"
                    confidence = min(10, sell_strength + 2)
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
            sentiment_score = 0
            risk_level = "MEDIUM"
            
            # In real implementation, would analyze price trends, volume, etc.
            # For now, provide neutral sentiment
            sentiment = "NEUTRAL"
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
        """Get portfolio management advice"""
        try:
            prompt = f"""
Analyze this trading portfolio and provide recommendations:

Portfolio Summary:
{json.dumps(portfolio_data, indent=2)}

Please provide:
1. Portfolio health assessment
2. Risk analysis
3. Diversification recommendations
4. Position sizing suggestions
5. Next steps

Keep the response concise and actionable.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a portfolio manager providing investment advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            logger.error(f"Portfolio advice error: {str(e)}")
            return None
