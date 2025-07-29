"""
Workflow Engine - Orchestrates the trading workflow like n8n
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

from nodes.alpaca_node import AlpacaNode
from nodes.chatgpt_node import ChatGPTNode
from nodes.telegram_node import TelegramNode
from nodes.email_node import EmailNode
from nodes.price_data_node import PriceDataNode
from nodes.report_generator_node import ReportGeneratorNode
from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class WorkflowEngine:
    """Main workflow engine that orchestrates trading operations"""
    
    def __init__(self):
        self.config = Config()
        self.is_trading = False
        self.last_trading_cycle = None
        
        # Initialize nodes
        self.alpaca_node = AlpacaNode()
        self.chatgpt_node = ChatGPTNode()
        self.telegram_node = TelegramNode()
        self.email_node = EmailNode()
        self.price_data_node = PriceDataNode()
        self.report_generator_node = ReportGeneratorNode()
        
        # Trading state
        self.positions = {}
        self.trading_history = []
        
        logger.info("Workflow Engine initialized")
    
    def start_trading(self):
        """Start the trading workflow"""
        try:
            # Validate configuration
            Config.validate_config()
            
            # Check market hours
            if not self._is_market_hours():
                logger.warning("Market is closed, trading will start when market opens")
            
            self.is_trading = True
            logger.info("Trading workflow started")
            
            # Send startup notification
            self.telegram_node.send_message("🚀 AI Trading Bot started successfully!")
            
        except Exception as e:
            logger.error(f"Failed to start trading: {str(e)}")
            raise
    
    def stop_trading(self):
        """Stop the trading workflow"""
        self.is_trading = False
        logger.info("Trading workflow stopped")
        
        # Send stop notification
        self.telegram_node.send_message("🛑 AI Trading Bot stopped")
    
    def run_trading_cycle(self):
        """Main trading cycle - equivalent to n8n workflow execution"""
        if not self.is_trading:
            return
        
        if not self._is_market_hours():
            return
        
        try:
            logger.info("Starting trading cycle")
            
            # Get symbols to trade
            symbols = self.config.TRADING_CONFIG['symbols_to_trade']
            
            for symbol in symbols:
                self._process_symbol(symbol)
            
            self.last_trading_cycle = datetime.now()
            logger.info("Trading cycle completed")
            
        except Exception as e:
            logger.error(f"Trading cycle error: {str(e)}")
            self.telegram_node.send_message(f"⚠️ Trading cycle error: {str(e)}")
    
    def _process_symbol(self, symbol: str):
        """Process a single symbol through the trading workflow"""
        try:
            logger.info(f"Processing symbol: {symbol}")
            
            # Step 1: Get price data (Price Data Node)
            price_data = self.price_data_node.get_price_data(symbol)
            if not price_data:
                logger.warning(f"No price data available for {symbol}")
                return
            
            # Step 2: Get current position (Alpaca Node)
            current_position = self.alpaca_node.get_position(symbol)
            
            # Step 3: Analyze with ChatGPT (ChatGPT Node)
            trading_decision = self.chatgpt_node.get_trading_decision(
                symbol, price_data, current_position
            )
            
            if not trading_decision:
                logger.warning(f"No trading decision received for {symbol}")
                return
            
            # Step 4: Execute trade if needed (Alpaca Node)
            if trading_decision['action'] in ['BUY', 'SELL']:
                trade_result = self._execute_trade(symbol, trading_decision, price_data)
                
                if trade_result:
                    # Step 5: Send notification (Telegram Node)
                    self._send_trade_notification(symbol, trading_decision, trade_result)
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")
            self.telegram_node.send_message(f"⚠️ Error processing {symbol}: {str(e)}")
    
    def _execute_trade(self, symbol: str, decision: Dict, price_data: Dict) -> Dict:
        """Execute the trading decision"""
        try:
            action = decision['action']
            confidence = decision.get('confidence', 5)
            quantity = decision.get('quantity', 1)
            
            # Risk management - adjust quantity based on confidence
            if confidence < 7:
                quantity = max(1, quantity // 2)  # Reduce quantity for low confidence
            
            # Check position limits
            max_position = self.config.TRADING_CONFIG['max_position_size']
            current_value = price_data['current_price'] * quantity
            
            if current_value > max_position:
                quantity = int(max_position / price_data['current_price'])
            
            if quantity <= 0:
                logger.warning(f"Calculated quantity is 0 for {symbol}")
                return None
            
            # Execute the trade
            if action == 'BUY':
                result = self.alpaca_node.place_buy_order(symbol, quantity)
            elif action == 'SELL':
                result = self.alpaca_node.place_sell_order(symbol, quantity)
            else:
                return None
            
            # Record trade
            trade_record = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price_data['current_price'],
                'confidence': confidence,
                'reasoning': decision.get('reasoning', ''),
                'result': result
            }
            
            self.trading_history.append(trade_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Trade execution error for {symbol}: {str(e)}")
            return None
    
    def _send_trade_notification(self, symbol: str, decision: Dict, trade_result: Dict):
        """Send trade notification via Telegram"""
        try:
            action = decision['action']
            confidence = decision.get('confidence', 'N/A')
            reasoning = decision.get('reasoning', 'No reasoning provided')
            
            message = f"""
📊 **Trade Executed**

Symbol: {symbol}
Action: {action}
Confidence: {confidence}/10
Price: ${trade_result.get('filled_avg_price', 'Pending')}
Quantity: {trade_result.get('qty', 'N/A')}

Reasoning: {reasoning[:200]}...
"""
            
            self.telegram_node.send_message(message)
            
        except Exception as e:
            logger.error(f"Notification error: {str(e)}")
    
    def process_external_signal(self, signal_data: Dict) -> Dict:
        """Process external trading signal from webhook"""
        try:
            symbol = signal_data['symbol']
            action = signal_data['action'].upper()
            confidence = signal_data.get('confidence', 5)
            
            logger.info(f"Processing external signal: {symbol} {action}")
            
            # Get current price data
            price_data = self.price_data_node.get_price_data(symbol)
            if not price_data:
                return {'error': 'Unable to get price data'}
            
            # Build decision object
            decision = {
                'action': action,
                'confidence': confidence,
                'quantity': signal_data.get('quantity', 1),
                'reasoning': f"External signal with confidence {confidence}"
            }
            
            # Execute trade
            if action in ['BUY', 'SELL']:
                trade_result = self._execute_trade(symbol, decision, price_data)
                
                if trade_result:
                    self._send_trade_notification(symbol, decision, trade_result)
                    return {'status': 'success', 'trade_result': trade_result}
                else:
                    return {'error': 'Trade execution failed'}
            
            return {'status': 'processed', 'action': 'hold'}
            
        except Exception as e:
            logger.error(f"External signal processing error: {str(e)}")
            return {'error': str(e)}
    
    def _is_market_hours(self) -> bool:
        """Check if current time is within trading hours"""
        now = datetime.now()
        
        # Skip weekends
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check trading hours
        start_hour = int(self.config.TRADING_CONFIG['trading_hours']['start'])
        end_hour = int(self.config.TRADING_CONFIG['trading_hours']['end'])
        
        return start_hour <= now.hour < end_hour
    
    def get_status(self) -> Dict:
        """Get current trading status"""
        return {
            'is_trading': self.is_trading,
            'last_cycle': self.last_trading_cycle.isoformat() if self.last_trading_cycle else None,
            'market_hours': self._is_market_hours(),
            'positions_count': len(self.positions),
            'trades_today': len([t for t in self.trading_history if t['timestamp'].date() == datetime.now().date()])
        }
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trading history"""
        return sorted(self.trading_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_performance_metrics(self) -> Dict:
        """Get basic performance metrics"""
        try:
            if not self.trading_history:
                return {
                    'total_trades': 0,
                    'profitable_trades': 0,
                    'win_rate': 0,
                    'total_return': 0
                }
            
            total_trades = len(self.trading_history)
            
            # This is a simplified calculation - in a real implementation,
            # you'd track actual P&L from position closing
            profitable_trades = len([t for t in self.trading_history if t.get('confidence', 0) >= 7])
            win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': round(win_rate, 2),
                'total_return': 0  # Would need actual position tracking
            }
            
        except Exception as e:
            logger.error(f"Performance metrics error: {str(e)}")
            return {}
