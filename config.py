"""
Configuration management for the trading bot
"""

import os
import json

class Config:
    """Configuration class with environment variable support"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    
    # API Keys - Retrieved from environment variables
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    
    # Email configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')
    
    # Alpaca configuration
    ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')  # Paper trading by default
    ALPACA_DATA_URL = os.getenv('ALPACA_DATA_URL', 'https://data.alpaca.markets')
    
    # Trading parameters
    TRADING_CONFIG = {
        'paper_trading': os.getenv('PAPER_TRADING', 'true').lower() == 'true',
        'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '1000.0')),
        'risk_percentage': float(os.getenv('RISK_PERCENTAGE', '2.0')),
        'stop_loss_percentage': float(os.getenv('STOP_LOSS_PERCENTAGE', '5.0')),
        'take_profit_percentage': float(os.getenv('TAKE_PROFIT_PERCENTAGE', '10.0')),
        'symbols_to_trade': os.getenv('SYMBOLS_TO_TRADE', 'AAPL,MSFT,GOOGL,TSLA,AMZN').split(','),
        'max_stocks_to_trade': int(os.getenv('MAX_STOCKS_TO_TRADE', '5')),
        'use_ai_stock_selection': os.getenv('USE_AI_STOCK_SELECTION', 'true').lower() == 'true',
        'stock_selection_interval': int(os.getenv('STOCK_SELECTION_INTERVAL', '30')),  # minutes
        'trading_hours': {
            'start': os.getenv('TRADING_START_HOUR', '9'),
            'end': os.getenv('TRADING_END_HOUR', '16')
        }
    }
    
    # Technical Analysis configuration
    TECHNICAL_CONFIG = {
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'ma_period_short': 20,
        'ma_period_long': 50,
        'momentum_threshold': 2.0,
        'volume_threshold': 1.5,
        'stop_loss_percent': 5.0,
        'take_profit_percent': 10.0
    }
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        required_vars = [
            'ALPACA_API_KEY',
            'ALPACA_SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
