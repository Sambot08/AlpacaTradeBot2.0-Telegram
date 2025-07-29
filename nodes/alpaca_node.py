"""
Alpaca Node - Handles all Alpaca API trading operations
"""

import logging
import requests
from typing import Dict, Optional, List
from datetime import datetime
import json

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class AlpacaNode:
    """Node for Alpaca trading operations"""
    
    def __init__(self):
        self.config = Config()
        self.base_url = self.config.ALPACA_BASE_URL
        self.data_url = self.config.ALPACA_DATA_URL
        
        self.headers = {
            'APCA-API-KEY-ID': self.config.ALPACA_API_KEY,
            'APCA-API-SECRET-KEY': self.config.ALPACA_SECRET_KEY,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Alpaca Node initialized (Paper Trading: {self.config.TRADING_CONFIG['paper_trading']})")
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        try:
            response = requests.get(
                f"{self.base_url}/v2/account",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get account info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Account info error: {str(e)}")
            return None
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol"""
        try:
            response = requests.get(
                f"{self.base_url}/v2/positions/{symbol}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # No position exists
                return None
            else:
                logger.error(f"Failed to get position for {symbol}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Position error for {symbol}: {str(e)}")
            return None
    
    def get_all_positions(self) -> List[Dict]:
        """Get all current positions"""
        try:
            response = requests.get(
                f"{self.base_url}/v2/positions",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get positions: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Positions error: {str(e)}")
            return []
    
    def place_buy_order(self, symbol: str, quantity: int, order_type: str = 'market') -> Optional[Dict]:
        """Place a buy order"""
        try:
            order_data = {
                'symbol': symbol,
                'qty': str(quantity),
                'side': 'buy',
                'type': order_type,
                'time_in_force': 'day'
            }
            
            # Add stop loss and take profit if configured
            if order_type == 'market':
                stop_loss_pct = self.config.TRADING_CONFIG['stop_loss_percentage']
                take_profit_pct = self.config.TRADING_CONFIG['take_profit_percentage']
                
                # Get current price for stop loss calculation
                current_price = self._get_current_price(symbol)
                if current_price:
                    order_data['order_class'] = 'bracket'
                    order_data['stop_loss'] = {
                        'stop_price': str(round(current_price * (1 - stop_loss_pct / 100), 2))
                    }
                    order_data['take_profit'] = {
                        'limit_price': str(round(current_price * (1 + take_profit_pct / 100), 2))
                    }
            
            response = requests.post(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                data=json.dumps(order_data)
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Buy order placed for {symbol}: {quantity} shares - Order ID: {result.get('id', 'N/A')}")
                return result
            else:
                logger.error(f"Failed to place buy order for {symbol}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Buy order error for {symbol}: {str(e)}")
            return None
    
    def place_sell_order(self, symbol: str, quantity: int, order_type: str = 'market') -> Optional[Dict]:
        """Place a sell order"""
        try:
            # Check if we have position to sell
            position = self.get_position(symbol)
            if not position:
                logger.warning(f"No position to sell for {symbol}")
                return None
            
            # Determine quantity to sell
            available_qty = int(position['qty'])
            if quantity > available_qty:
                quantity = available_qty
                logger.info(f"Adjusted sell quantity to {quantity} for {symbol}")
            
            order_data = {
                'symbol': symbol,
                'qty': str(quantity),
                'side': 'sell',
                'type': order_type,
                'time_in_force': 'day'
            }
            
            response = requests.post(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                data=json.dumps(order_data)
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Sell order placed for {symbol}: {quantity} shares - Order ID: {result.get('id', 'N/A')}")
                return result
            else:
                logger.error(f"Failed to place sell order for {symbol}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Sell order error for {symbol}: {str(e)}")
            return None
    
    def get_orders(self, status: str = 'all', limit: int = 50) -> List[Dict]:
        """Get orders"""
        try:
            params = {
                'status': status,
                'limit': limit,
                'direction': 'desc'
            }
            
            response = requests.get(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get orders: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Orders error: {str(e)}")
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            response = requests.delete(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=self.headers
            )
            
            if response.status_code == 204:
                logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logger.error(f"Failed to cancel order {order_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Cancel order error: {str(e)}")
            return False
    
    def get_portfolio_history(self, period: str = '1M') -> Optional[Dict]:
        """Get portfolio history"""
        try:
            params = {
                'period': period,
                'timeframe': '1Day'
            }
            
            response = requests.get(
                f"{self.base_url}/v2/account/portfolio/history",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get portfolio history: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Portfolio history error: {str(e)}")
            return None
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            response = requests.get(
                f"{self.data_url}/v2/stocks/{symbol}/quotes/latest",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('quote', {})
                bid = float(quote.get('bid_price', 0))
                ask = float(quote.get('ask_price', 0))
                
                if bid > 0 and ask > 0:
                    return (bid + ask) / 2
                
            return None
            
        except Exception as e:
            logger.error(f"Current price error for {symbol}: {str(e)}")
            return None
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            response = requests.get(
                f"{self.base_url}/v2/clock",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('is_open', False)
            
            return False
            
        except Exception as e:
            logger.error(f"Market status error: {str(e)}")
            return False
