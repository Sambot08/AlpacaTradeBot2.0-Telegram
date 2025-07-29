# AI Trading Bot

## Overview

This is an AI-powered trading bot built with a Flask web framework that implements an N8N-style workflow engine for automated trading operations. The system integrates multiple services including Alpaca for trading, OpenAI's ChatGPT for decision-making, Telegram for notifications, and email for reporting.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular node-based architecture similar to N8N, where each service is encapsulated in its own node. The system is built around a central workflow engine that orchestrates trading operations by coordinating between different specialized nodes.

### Core Architecture Components:
- **Flask Web Application**: Serves as the main entry point with a dashboard interface
- **Workflow Engine**: Central orchestrator that manages trading cycles and node interactions
- **Node-Based Services**: Modular components handling specific functionalities
- **Configuration Management**: Environment-based configuration system
- **Logging System**: Comprehensive logging with file and console outputs
- **Task Scheduler**: Handles periodic operations like reports and maintenance

## Key Components

### Frontend Architecture
- **Dashboard Interface**: HTML/CSS dashboard showing trading metrics and controls
- **Real-time Status**: Market hours, bot status, and trading performance display
- **Email Templates**: HTML email templates for automated reporting

### Backend Architecture
- **Workflow Engine** (`workflow_engine.py`): Main orchestrator managing trading cycles
- **Node System**: Individual service nodes for different functionalities:
  - **AlpacaNode**: Handles all trading operations via Alpaca API
  - **ChatGPTNode**: AI decision-making for buy/sell signals and market sentiment analysis
  - **StockSelectorNode**: AI-powered intelligent stock selection system
  - **TelegramNode**: Real-time notifications via Telegram bot
  - **EmailNode**: Email notifications and reports
  - **PriceDataNode**: Multi-source price data fetching with fallbacks
  - **ReportGeneratorNode**: Analytics and report generation

### Configuration System
- Environment variable-based configuration
- Trading parameters (risk management, position sizing)
- API keys and credentials management
- Trading hours and symbol configuration

## Data Flow

1. **Stock Selection**: StockSelectorNode uses AI to intelligently choose stocks to trade every 30 minutes
2. **Market Data Collection**: PriceDataNode fetches data from Alpaca (primary) with Alpha Vantage fallback
3. **AI Analysis**: ChatGPTNode analyzes market data and current positions to make trading decisions
4. **Market Sentiment**: ChatGPTNode provides overall market sentiment analysis for selected stocks
5. **Trade Execution**: AlpacaNode executes buy/sell orders based on AI recommendations
6. **Notifications**: TelegramNode sends real-time alerts for trades, stock selections, and system status
7. **Reporting**: ReportGeneratorNode creates periodic reports sent via EmailNode
8. **Monitoring**: Dashboard displays real-time status, selected stocks, and trading metrics

## External Dependencies

### Trading & Market Data
- **Alpaca Markets API**: Primary trading execution and market data
- **Alpha Vantage API**: Fallback market data source

### AI & Decision Making
- **OpenAI GPT API**: AI-powered trading decision making

### Communication & Notifications
- **Telegram Bot API**: Real-time notifications
- **SMTP Email**: Automated reporting and alerts

### Infrastructure
- **Flask**: Web framework for dashboard and webhooks
- **Python Standard Library**: Core functionality and utilities

## Deployment Strategy

The application is designed for deployment as a single Python application with the following characteristics:

### Environment Configuration
- All sensitive data managed via environment variables
- Paper trading mode enabled by default for safety
- Configurable trading parameters and risk management

### Operational Features
- **Paper Trading Mode**: Safe testing environment using Alpaca's paper trading
- **Risk Management**: Built-in position sizing and stop-loss mechanisms
- **Market Hours Checking**: Automatic trading schedule management
- **Error Handling**: Comprehensive logging and fallback mechanisms
- **Webhook Support**: External signal integration capability

### Monitoring & Maintenance
- **Dashboard Interface**: Web-based monitoring and control
- **Automated Reporting**: Weekly and monthly performance reports
- **Real-time Notifications**: Immediate alerts via Telegram
- **Comprehensive Logging**: Detailed logs for debugging and audit trails

The system prioritizes safety through paper trading defaults, comprehensive error handling, and multiple fallback mechanisms for critical services like market data fetching.

## Recent Changes: Latest modifications with dates

### July 29, 2025 - Advanced Stock Selection Enhancement
- ✓ Dynamic Sector Weighting: Bot now analyzes sector ETF performance (XLK, XLF, XLV, etc.) to favor outperforming sectors
- ✓ Time-of-Day Awareness: Selection adjusts based on market hours (30% boost at open, 20% at close, reduction during lunch)
- ✓ Signal Confirmation Layer: Requires multiple confirmations (volume spikes, price momentum, technical breakouts) before selection
- ✓ LLM Sentiment Integration: Uses ChatGPT to analyze sentiment for top candidates, combining 70% technical + 30% sentiment scores
- ✓ Trade History Learning: Framework added for adaptive scoring based on historical performance
- ✓ Enhanced Logging: Detailed reasoning for each stock selection with sector analysis and scoring breakdown

### Previous Updates
- Initial AI trading bot architecture completed
- Modular n8n-style workflow system implemented
- All core trading nodes functional