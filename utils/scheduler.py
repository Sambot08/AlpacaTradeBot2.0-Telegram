"""
Task Scheduler for handling periodic trading bot tasks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import threading
import time

from nodes.report_generator_node import ReportGeneratorNode
from nodes.email_node import EmailNode
from nodes.telegram_node import TelegramNode
from utils.logger import setup_logger

logger = setup_logger()

class TaskScheduler:
    """Scheduler for periodic tasks like reports and maintenance"""
    
    def __init__(self):
        self.report_generator = ReportGeneratorNode()
        self.email_node = EmailNode()
        self.telegram_node = TelegramNode()
        
        # Task tracking
        self.last_weekly_report = None
        self.last_monthly_report = None
        self.last_daily_summary = None
        
        logger.info("Task Scheduler initialized")
    
    def run_weekly_report(self):
        """Generate and send weekly report"""
        try:
            # Check if we already sent this week's report
            if self._already_sent_weekly():
                logger.info("Weekly report already sent this week")
                return
            
            logger.info("Generating weekly report...")
            
            # Get trading data (placeholder - would get from workflow engine)
            trading_history = self._get_trading_history()
            positions = self._get_current_positions()
            
            # Generate report
            report_data = self.report_generator.generate_weekly_report(
                trading_history, positions
            )
            
            if not report_data:
                logger.error("Failed to generate weekly report")
                return
            
            # Send via email
            email_sent = self.email_node.send_weekly_report(report_data)
            
            # Send summary via Telegram
            telegram_sent = self._send_weekly_telegram_summary(report_data)
            
            if email_sent or telegram_sent:
                self.last_weekly_report = datetime.now()
                logger.info("Weekly report sent successfully")
            else:
                logger.error("Failed to send weekly report")
                
        except Exception as e:
            logger.error(f"Weekly report task error: {str(e)}")
            self.telegram_node.send_error_alert("Weekly Report", str(e))
    
    def run_monthly_report(self):
        """Generate and send monthly report"""
        try:
            # Check if we already sent this month's report
            if self._already_sent_monthly():
                logger.info("Monthly report already sent this month")
                return
            
            logger.info("Generating monthly report...")
            
            # Get trading data
            trading_history = self._get_trading_history()
            positions = self._get_current_positions()
            
            # Generate comprehensive monthly report
            report_data = self.report_generator.generate_monthly_report(
                trading_history, positions
            )
            
            if not report_data:
                logger.error("Failed to generate monthly report")
                return
            
            # Send via email
            email_sent = self.email_node.send_monthly_report(report_data)
            
            # Send summary via Telegram
            telegram_sent = self._send_monthly_telegram_summary(report_data)
            
            if email_sent or telegram_sent:
                self.last_monthly_report = datetime.now()
                logger.info("Monthly report sent successfully")
            else:
                logger.error("Failed to send monthly report")
                
        except Exception as e:
            logger.error(f"Monthly report task error: {str(e)}")
            self.telegram_node.send_error_alert("Monthly Report", str(e))
    
    def run_daily_summary(self):
        """Generate and send daily trading summary"""
        try:
            # Check if we already sent today's summary
            if self._already_sent_daily():
                logger.info("Daily summary already sent today")
                return
            
            logger.info("Generating daily summary...")
            
            # Get today's trading data
            today_trades = self._get_today_trades()
            positions = self._get_current_positions()
            
            # Calculate daily metrics
            daily_metrics = self._calculate_daily_metrics(today_trades, positions)
            
            # Send Telegram summary
            if daily_metrics['trades_count'] > 0:
                telegram_sent = self.telegram_node.send_daily_report(daily_metrics)
                
                if telegram_sent:
                    self.last_daily_summary = datetime.now()
                    logger.info("Daily summary sent successfully")
            else:
                logger.info("No trades today, skipping daily summary")
                
        except Exception as e:
            logger.error(f"Daily summary task error: {str(e)}")
    
    def _already_sent_weekly(self) -> bool:
        """Check if weekly report was already sent this week"""
        if not self.last_weekly_report:
            return False
        
        # Check if it's the same week
        now = datetime.now()
        last_week_start = now - timedelta(days=now.weekday())
        report_week_start = self.last_weekly_report - timedelta(days=self.last_weekly_report.weekday())
        
        return last_week_start == report_week_start
    
    def _already_sent_monthly(self) -> bool:
        """Check if monthly report was already sent this month"""
        if not self.last_monthly_report:
            return False
        
        now = datetime.now()
        return (now.year == self.last_monthly_report.year and 
                now.month == self.last_monthly_report.month)
    
    def _already_sent_daily(self) -> bool:
        """Check if daily summary was already sent today"""
        if not self.last_daily_summary:
            return False
        
        return self.last_daily_summary.date() == datetime.now().date()
    
    def _get_trading_history(self) -> list:
        """Get trading history (placeholder - would integrate with workflow engine)"""
        # This would normally get data from the workflow engine
        # For now, return empty list
        return []
    
    def _get_current_positions(self) -> dict:
        """Get current positions (placeholder)"""
        # This would normally get data from Alpaca
        return {}
    
    def _get_today_trades(self) -> list:
        """Get today's trades"""
        trading_history = self._get_trading_history()
        today = datetime.now().date()
        
        return [
            trade for trade in trading_history
            if isinstance(trade.get('timestamp'), datetime) and 
               trade['timestamp'].date() == today
        ]
    
    def _calculate_daily_metrics(self, trades: list, positions: dict) -> dict:
        """Calculate daily performance metrics"""
        try:
            total_trades = len(trades)
            
            if total_trades == 0:
                return {
                    'trades_count': 0,
                    'profitable_trades': 0,
                    'daily_pnl': 0,
                    'win_rate': 0
                }
            
            # Calculate basic metrics
            high_confidence_trades = [t for t in trades if t.get('confidence', 0) >= 7]
            win_rate = (len(high_confidence_trades) / total_trades) * 100
            
            # Estimate daily P&L (simplified)
            daily_pnl = 0
            for trade in trades:
                confidence = trade.get('confidence', 5)
                value = trade.get('price', 0) * trade.get('quantity', 0)
                
                if confidence >= 7:
                    daily_pnl += value * 0.02  # 2% gain estimate
                else:
                    daily_pnl -= value * 0.01  # 1% loss estimate
            
            return {
                'trades_count': total_trades,
                'profitable_trades': len(high_confidence_trades),
                'daily_pnl': round(daily_pnl, 2),
                'win_rate': round(win_rate, 1)
            }
            
        except Exception as e:
            logger.error(f"Daily metrics calculation error: {str(e)}")
            return {
                'trades_count': 0,
                'profitable_trades': 0,
                'daily_pnl': 0,
                'win_rate': 0
            }
    
    def _send_weekly_telegram_summary(self, report_data: dict) -> bool:
        """Send weekly report summary via Telegram"""
        try:
            total_trades = report_data.get('total_trades', 0)
            win_rate = report_data.get('win_rate', 0)
            total_pnl = report_data.get('total_pnl', 0)
            
            pnl_emoji = "📈" if total_pnl >= 0 else "📉"
            
            message = f"""
📊 **WEEKLY REPORT SUMMARY**

📈 Total Trades: `{total_trades}`
🎯 Win Rate: `{win_rate:.1f}%`
{pnl_emoji} Weekly P&L: `${total_pnl:+,.2f}`

📧 Detailed report sent via email.

Great week of trading! 🚀
"""
            
            return self.telegram_node.send_message(message)
            
        except Exception as e:
            logger.error(f"Weekly Telegram summary error: {str(e)}")
            return False
    
    def _send_monthly_telegram_summary(self, report_data: dict) -> bool:
        """Send monthly report summary via Telegram"""
        try:
            total_trades = report_data.get('total_trades', 0)
            win_rate = report_data.get('win_rate', 0)
            total_pnl = report_data.get('total_pnl', 0)
            sharpe_ratio = report_data.get('sharpe_ratio', 0)
            
            pnl_emoji = "📈" if total_pnl >= 0 else "📉"
            
            message = f"""
📅 **MONTHLY REPORT SUMMARY**

📊 Total Trades: `{total_trades}`
🎯 Win Rate: `{win_rate:.1f}%`
{pnl_emoji} Monthly P&L: `${total_pnl:+,.2f}`
📏 Sharpe Ratio: `{sharpe_ratio:.2f}`

📧 Comprehensive report sent via email.

Excellent month! Keep it up! 🏆
"""
            
            return self.telegram_node.send_message(message)
            
        except Exception as e:
            logger.error(f"Monthly Telegram summary error: {str(e)}")
            return False
    
    def schedule_maintenance_tasks(self):
        """Schedule periodic maintenance tasks"""
        def maintenance_worker():
            while True:
                try:
                    # Run maintenance every hour
                    now = datetime.now()
                    
                    # Daily summary at 5 PM
                    if now.hour == 17 and now.minute < 5:
                        self.run_daily_summary()
                    
                    # Weekly report on Sundays at 9 AM
                    if now.weekday() == 6 and now.hour == 9 and now.minute < 5:
                        self.run_weekly_report()
                    
                    # Monthly report on 1st at 10 AM
                    if now.day == 1 and now.hour == 10 and now.minute < 5:
                        self.run_monthly_report()
                    
                    # Sleep for 5 minutes
                    time.sleep(300)
                    
                except Exception as e:
                    logger.error(f"Maintenance worker error: {str(e)}")
                    time.sleep(60)  # Wait 1 minute on error
        
        # Start maintenance thread
        maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
        maintenance_thread.start()
        logger.info("Maintenance tasks scheduled")
