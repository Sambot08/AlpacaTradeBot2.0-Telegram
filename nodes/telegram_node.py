"""
Telegram Node - Handles Telegram bot notifications
"""

import logging
import requests
from typing import Optional, Dict
import json

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class TelegramNode:
    """Node for Telegram notifications"""
    
    def __init__(self):
        self.config = Config()
        self.bot_token = self.config.TELEGRAM_BOT_TOKEN
        self.chat_id = self.config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot token or chat ID not configured")
        else:
            logger.info("Telegram Node initialized")
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured, skipping message")
            return False
        
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(
                f"{self.base_url}/sendMessage",
                data=payload
            )
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram send error: {str(e)}")
            return False
    
    def send_trade_alert(self, symbol: str, action: str, quantity: int, price: float, 
                        confidence: int, reasoning: str) -> bool:
        """Send formatted trade alert"""
        try:
            emoji = "📈" if action == "BUY" else "📉" if action == "SELL" else "⏸️"
            
            message = f"""
{emoji} **TRADE ALERT**

🏷️ Symbol: `{symbol}`
🎯 Action: `{action}`
📊 Quantity: `{quantity}` shares
💰 Price: `${price:.2f}`
🎚️ Confidence: `{confidence}/10`

💭 **Reasoning:**
{reasoning[:300]}{"..." if len(reasoning) > 300 else ""}

⏰ {self._get_timestamp()}
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Trade alert error: {str(e)}")
            return False
    
    def send_portfolio_update(self, portfolio_data: Dict) -> bool:
        """Send portfolio performance update"""
        try:
            total_value = portfolio_data.get('total_value', 0)
            daily_pnl = portfolio_data.get('daily_pnl', 0)
            total_pnl = portfolio_data.get('total_pnl', 0)
            positions_count = portfolio_data.get('positions_count', 0)
            
            pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
            
            message = f"""
📊 **PORTFOLIO UPDATE**

💼 Total Value: `${total_value:,.2f}`
{pnl_emoji} Daily P&L: `${daily_pnl:+,.2f}`
📈 Total P&L: `${total_pnl:+,.2f}`
🏢 Active Positions: `{positions_count}`

⏰ {self._get_timestamp()}
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Portfolio update error: {str(e)}")
            return False
    
    def send_error_alert(self, error_type: str, error_message: str) -> bool:
        """Send error alert"""
        try:
            message = f"""
🚨 **ERROR ALERT**

🔍 Type: `{error_type}`
💬 Message: `{error_message[:200]}...`

⏰ {self._get_timestamp()}

Please check the logs for more details.
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error alert error: {str(e)}")
            return False
    
    def send_market_analysis(self, analysis: Dict) -> bool:
        """Send market analysis summary"""
        try:
            sentiment = analysis.get('sentiment', 'NEUTRAL')
            risk_level = analysis.get('risk_level', 'MEDIUM')
            analysis_text = analysis.get('analysis', '')
            
            sentiment_emoji = {
                'BULLISH': '🐂',
                'BEARISH': '🐻',
                'NEUTRAL': '😐'
            }.get(sentiment, '😐')
            
            risk_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🔴'
            }.get(risk_level, '🟡')
            
            message = f"""
🔍 **MARKET ANALYSIS**

{sentiment_emoji} Sentiment: `{sentiment}`
{risk_emoji} Risk Level: `{risk_level}`

📝 **Analysis:**
{analysis_text[:500]}{"..." if len(analysis_text) > 500 else ""}

⏰ {self._get_timestamp()}
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Market analysis error: {str(e)}")
            return False
    
    def send_daily_report(self, report_data: Dict) -> bool:
        """Send daily trading report"""
        try:
            trades_count = report_data.get('trades_count', 0)
            profitable_trades = report_data.get('profitable_trades', 0)
            daily_pnl = report_data.get('daily_pnl', 0)
            win_rate = report_data.get('win_rate', 0)
            
            pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
            
            message = f"""
📅 **DAILY REPORT**

📊 Trades Executed: `{trades_count}`
✅ Profitable Trades: `{profitable_trades}`
📈 Win Rate: `{win_rate:.1f}%`
{pnl_emoji} Daily P&L: `${daily_pnl:+,.2f}`

⏰ {self._get_timestamp()}

Great job today! 🚀
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Daily report error: {str(e)}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            response = requests.get(f"{self.base_url}/getMe")
            
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Telegram bot connected: {bot_info.get('result', {}).get('username', 'Unknown')}")
                return True
            else:
                logger.error(f"Telegram connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram test error: {str(e)}")
            return False
