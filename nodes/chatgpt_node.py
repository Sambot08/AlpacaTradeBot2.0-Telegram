"""
ChatGPT Node - AI decision making for trading
"""

import logging
import openai
from typing import Dict, Optional
import json
import re

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class ChatGPTNode:
    """Node for ChatGPT-powered trading decisions"""
    
    def __init__(self):
        self.config = Config()
        self.client = openai.OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.model = self.config.CHATGPT_CONFIG['model']
        self.temperature = self.config.CHATGPT_CONFIG['temperature']
        self.max_tokens = self.config.CHATGPT_CONFIG['max_tokens']
        
        logger.info("ChatGPT Node initialized")
    
    def get_trading_decision(self, symbol: str, price_data: Dict, current_position: Optional[Dict]) -> Optional[Dict]:
        """Get AI trading decision for a symbol"""
        try:
            # Prepare the prompt with market data
            prompt = self._build_trading_prompt(symbol, price_data, current_position)
            
            # Get AI response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional trading assistant with expertise in technical analysis and risk management."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            if not ai_response:
                return None
            ai_response = ai_response.strip()
            decision = self._parse_trading_response(ai_response)
            
            if decision:
                logger.info(f"ChatGPT decision for {symbol}: {decision['action']} (confidence: {decision['confidence']})")
                return decision
            else:
                logger.warning(f"Could not parse ChatGPT response for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"ChatGPT decision error for {symbol}: {str(e)}")
            return None
    
    def _build_trading_prompt(self, symbol: str, price_data: Dict, current_position: Optional[Dict]) -> str:
        """Build the trading analysis prompt"""
        try:
            # Calculate additional indicators
            current_price = price_data.get('current_price', 0)
            price_change = price_data.get('price_change_percent', 0)
            volume = price_data.get('volume', 0)
            
            # Technical indicators (simplified)
            ma_20 = price_data.get('ma_20', current_price)
            ma_50 = price_data.get('ma_50', current_price)
            rsi = price_data.get('rsi', 50)
            
            # Position context
            position_context = ""
            if current_position:
                qty = current_position.get('qty', 0)
                avg_entry_price = float(current_position.get('avg_entry_price', 0))
                unrealized_pl = current_position.get('unrealized_pl', 0)
                
                position_context = f"""
Current Position:
- Quantity: {qty} shares
- Average Entry Price: ${avg_entry_price}
- Unrealized P&L: ${unrealized_pl}
- Current Value: ${float(qty) * current_price if qty else 0}
"""
            else:
                position_context = "No current position in this symbol."
            
            # Build the complete prompt
            prompt = self.config.CHATGPT_CONFIG['trading_prompt_template'].format(
                symbol=symbol,
                current_price=current_price,
                price_change=price_change,
                volume=volume,
                rsi=rsi,
                ma_20=ma_20,
                ma_50=ma_50,
                additional_context=position_context
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Prompt building error: {str(e)}")
            return ""
    
    def _parse_trading_response(self, response: str) -> Optional[Dict]:
        """Parse ChatGPT response into structured decision"""
        try:
            # Extract action
            action_match = re.search(r'ACTION:\s*(BUY|SELL|HOLD)', response, re.IGNORECASE)
            if not action_match:
                return None
            
            action = action_match.group(1).upper()
            
            # Extract confidence
            confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', response)
            confidence = int(confidence_match.group(1)) if confidence_match else 5
            
            # Extract reasoning  
            reasoning_match = re.search(r'REASONING:\s*(.+?)(?=QUANTITY:|$)', response, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
            
            # Extract quantity
            quantity_match = re.search(r'QUANTITY:\s*(\d+)', response)
            quantity = int(quantity_match.group(1)) if quantity_match else 1
            
            decision = {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
                'quantity': quantity,
                'raw_response': response
            }
            
            return decision
            
        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            return None
    
    def analyze_market_sentiment(self, symbols: list) -> Optional[Dict]:
        """Analyze overall market sentiment for multiple symbols"""
        try:
            prompt = f"""
Analyze the current market sentiment for the following stocks: {', '.join(symbols)}

Consider:
1. Overall market trends
2. Sector performance
3. Economic indicators
4. Recent news impact

Provide a market sentiment analysis with:
- Overall sentiment (BULLISH/BEARISH/NEUTRAL)
- Risk level (LOW/MEDIUM/HIGH)
- Recommended strategy
- Key factors to watch

Format your response clearly with these sections.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a market analyst providing sentiment analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            analysis = response.choices[0].message.content
            if not analysis:
                return None
            analysis = analysis.strip()
            
            # Parse sentiment
            sentiment_match = re.search(r'sentiment[:\s]*(BULLISH|BEARISH|NEUTRAL)', analysis, re.IGNORECASE)
            sentiment = sentiment_match.group(1).upper() if sentiment_match else 'NEUTRAL'
            
            # Parse risk level
            risk_match = re.search(r'risk[:\s]*(LOW|MEDIUM|HIGH)', analysis, re.IGNORECASE)
            risk_level = risk_match.group(1).upper() if risk_match else 'MEDIUM'
            
            return {
                'sentiment': sentiment,
                'risk_level': risk_level,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Market sentiment analysis error: {str(e)}")
            return None
    
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
