"""
AI-Powered Trading Bot with N8N-style Workflow Engine
Main application entry point
"""

import os
import logging
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import threading
import time

from workflow_engine import WorkflowEngine
from utils.logger import setup_logger
from utils.scheduler import TaskScheduler
from config import Config

# Setup logging
logger = setup_logger()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize workflow engine
workflow_engine = WorkflowEngine()
scheduler = TaskScheduler()

@app.route('/')
def dashboard():
    """Dashboard view"""
    try:
        # Get recent trades and performance metrics
        recent_trades = workflow_engine.get_recent_trades()
        performance = workflow_engine.get_performance_metrics()
        
        return render_template('dashboard.html', 
                             trades=recent_trades, 
                             performance=performance)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return render_template('dashboard.html', 
                             trades=[], 
                             performance={})

@app.route('/webhook/signal', methods=['POST'])
def webhook_signal():
    """Webhook endpoint for receiving external trading signals"""
    try:
        data = request.get_json()
        logger.info(f"Received webhook signal: {data}")
        
        # Validate required fields
        required_fields = ['symbol', 'action', 'confidence']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Process the signal through workflow engine
        result = workflow_engine.process_external_signal(data)
        
        return jsonify({'status': 'success', 'result': result})
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_trading', methods=['POST'])
def start_trading():
    """Start the trading workflow"""
    try:
        workflow_engine.start_trading()
        return jsonify({'status': 'Trading started'})
    except Exception as e:
        logger.error(f"Start trading error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_trading', methods=['POST'])
def stop_trading():
    """Stop the trading workflow"""
    try:
        workflow_engine.stop_trading()
        return jsonify({'status': 'Trading stopped'})
    except Exception as e:
        logger.error(f"Stop trading error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get current trading status"""
    try:
        status = workflow_engine.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock_selection')
def get_stock_selection():
    """Get current stock selection info"""
    try:
        selection_info = workflow_engine.get_current_stock_selection()
        return jsonify(selection_info)
    except Exception as e:
        logger.error(f"Stock selection error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_stock_selection', methods=['POST'])
def update_stock_selection():
    """Manually trigger stock selection update"""
    try:
        workflow_engine._update_selected_stocks()
        selection_info = workflow_engine.get_current_stock_selection()
        return jsonify({
            'status': 'Stock selection updated',
            'selection_info': selection_info
        })
    except Exception as e:
        logger.error(f"Manual stock selection update error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_telegram', methods=['POST'])
def test_telegram():
    """Test Telegram bot connectivity"""
    try:
        telegram_node = workflow_engine.telegram_node
        success = telegram_node.send_message("🤖 Telegram Bot Test: Connection successful! Your trading bot notifications are now active.")
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Telegram test message sent successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send Telegram message'
            }), 500
            
    except Exception as e:
        logger.error(f"Telegram test error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_trade', methods=['POST'])
def test_trade():
    """Test trade execution with one of the selected stocks"""
    try:
        # Get current selected stocks
        selection_info = workflow_engine.get_current_stock_selection()
        selected_stocks = selection_info.get('selected_stocks', [])
        
        if not selected_stocks:
            return jsonify({'error': 'No stocks selected for trading'}), 400
        
        # Use the first selected stock for test trade
        test_symbol = selected_stocks[0]
        
        # Create a test buy signal
        test_signal = {
            'symbol': test_symbol,
            'action': 'BUY',
            'confidence': 7,
            'quantity': 1
        }
        
        # Process the test signal
        result = workflow_engine.process_external_signal(test_signal)
        
        return jsonify({
            'status': 'Test trade executed',
            'symbol': test_symbol,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Test trade error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_scheduled_tasks():
    """Background thread for scheduled tasks"""
    while True:
        try:
            # Check for weekly reports (Sundays at 9 AM)
            if datetime.now().weekday() == 6 and datetime.now().hour == 9:
                scheduler.run_weekly_report()
            
            # Check for monthly reports (1st of month at 10 AM)
            if datetime.now().day == 1 and datetime.now().hour == 10:
                scheduler.run_monthly_report()
            
            # Run main trading loop every 5 minutes
            workflow_engine.run_trading_cycle()
            
            time.sleep(300)  # 5 minutes
            
        except Exception as e:
            logger.error(f"Scheduled task error: {str(e)}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == '__main__':
    try:
        logger.info("Starting AI Trading Bot...")
        
        # Start background scheduler thread
        scheduler_thread = threading.Thread(target=run_scheduled_tasks, daemon=True)
        scheduler_thread.start()
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
        raise
