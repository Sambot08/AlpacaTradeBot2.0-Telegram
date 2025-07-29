"""
Logging utility for the trading bot
"""

import logging
import os
from datetime import datetime

def setup_logger(name: str = 'trading_bot', level: str = 'INFO') -> logging.Logger:
    """Setup and configure logger"""
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for detailed logs
    log_file = os.path.join(log_dir, f'trading_bot_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Error file handler
    error_file = os.path.join(log_dir, f'trading_bot_errors_{datetime.now().strftime("%Y%m%d")}.log')
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    return logger

def log_trade(logger: logging.Logger, symbol: str, action: str, quantity: int, 
              price: float, confidence: int, reasoning: str = ""):
    """Log trading activity"""
    logger.info(
        f"TRADE: {action} {quantity} {symbol} @ ${price:.2f} "
        f"(confidence: {confidence}/10) - {reasoning[:100]}..."
    )

def log_error(logger: logging.Logger, error_type: str, error_message: str, 
              context: str = ""):
    """Log error with context"""
    logger.error(f"{error_type}: {error_message} | Context: {context}")

def log_performance(logger: logging.Logger, metrics: dict):
    """Log performance metrics"""
    logger.info(
        f"PERFORMANCE: Trades: {metrics.get('total_trades', 0)}, "
        f"Win Rate: {metrics.get('win_rate', 0):.1f}%, "
        f"P&L: ${metrics.get('total_pnl', 0):+,.2f}"
    )
