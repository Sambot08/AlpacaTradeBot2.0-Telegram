"""
Email Node - Handles email notifications and reports
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime
import json

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class EmailNode:
    """Node for email notifications and reports"""
    
    def __init__(self):
        self.config = Config()
        self.smtp_server = self.config.SMTP_SERVER
        self.smtp_port = self.config.SMTP_PORT
        self.username = self.config.EMAIL_USERNAME
        self.password = self.config.EMAIL_PASSWORD
        self.recipients = [email.strip() for email in self.config.EMAIL_RECIPIENTS if email.strip()]
        
        if not all([self.username, self.password, self.recipients]):
            logger.warning("Email configuration incomplete")
        else:
            logger.info(f"Email Node initialized with {len(self.recipients)} recipients")
    
    def send_email(self, subject: str, body: str, html_body: Optional[str] = None, 
                   recipients: Optional[List[str]] = None) -> bool:
        """Send email notification"""
        if not self.username or not self.password:
            logger.warning("Email not configured, skipping send")
            return False
        
        try:
            # Use provided recipients or default ones
            to_emails = recipients or self.recipients
            if not to_emails:
                logger.warning("No email recipients configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = ', '.join(to_emails)
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            return False
    
    def send_weekly_report(self, report_data: Dict) -> bool:
        """Send weekly trading report"""
        try:
            subject = f"Weekly Trading Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Generate HTML report
            html_body = self._generate_weekly_report_html(report_data)
            
            # Generate text version
            text_body = self._generate_weekly_report_text(report_data)
            
            return self.send_email(subject, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Weekly report error: {str(e)}")
            return False
    
    def send_monthly_report(self, report_data: Dict) -> bool:
        """Send monthly trading report"""
        try:
            subject = f"Monthly Trading Report - {datetime.now().strftime('%B %Y')}"
            
            # Generate HTML report
            html_body = self._generate_monthly_report_html(report_data)
            
            # Generate text version
            text_body = self._generate_monthly_report_text(report_data)
            
            return self.send_email(subject, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Monthly report error: {str(e)}")
            return False
    
    def send_error_notification(self, error_type: str, error_details: str) -> bool:
        """Send error notification email"""
        try:
            subject = f"Trading Bot Error Alert - {error_type}"
            
            body = f"""
Trading Bot Error Alert

Error Type: {error_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Error Details:
{error_details}

Please check the logs and take appropriate action.

Best regards,
AI Trading Bot
"""
            
            return self.send_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error notification error: {str(e)}")
            return False
    
    def _generate_weekly_report_html(self, data: Dict) -> str:
        """Generate HTML weekly report"""
        try:
            trades = data.get('trades', [])
            total_trades = len(trades)
            profitable_trades = data.get('profitable_trades', 0)
            total_pnl = data.get('total_pnl', 0)
            win_rate = data.get('win_rate', 0)
            
            # Generate trades table
            trades_html = ""
            for trade in trades[-10:]:  # Last 10 trades
                symbol = trade.get('symbol', 'N/A')
                action = trade.get('action', 'N/A')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                timestamp = trade.get('timestamp', 'N/A')
                
                trades_html += f"""
                <tr>
                    <td>{timestamp}</td>
                    <td>{symbol}</td>
                    <td>{action}</td>
                    <td>{quantity}</td>
                    <td>${price:.2f}</td>
                </tr>
                """
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                    .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                    .metric {{ text-align: center; padding: 15px; background-color: #e9ecef; border-radius: 5px; }}
                    .metric h3 {{ margin: 0; color: #333; }}
                    .metric p {{ margin: 5px 0 0 0; font-size: 24px; font-weight: bold; }}
                    .positive {{ color: #28a745; }}
                    .negative {{ color: #dc3545; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f8f9fa; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Weekly Trading Report</h1>
                    <p>Report Period: {datetime.now().strftime('%Y-%m-%d')}</p>
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <h3>Total Trades</h3>
                        <p>{total_trades}</p>
                    </div>
                    <div class="metric">
                        <h3>Win Rate</h3>
                        <p>{win_rate:.1f}%</p>
                    </div>
                    <div class="metric">
                        <h3>P&L</h3>
                        <p class="{'positive' if total_pnl >= 0 else 'negative'}">${total_pnl:+,.2f}</p>
                    </div>
                </div>
                
                <h2>Recent Trades</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Action</th>
                            <th>Quantity</th>
                            <th>Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trades_html or '<tr><td colspan="5">No trades this week</td></tr>'}
                    </tbody>
                </table>
                
                <p style="margin-top: 30px; color: #666;">
                    Generated by AI Trading Bot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"HTML report generation error: {str(e)}")
            return "<html><body><h1>Error generating report</h1></body></html>"
    
    def _generate_weekly_report_text(self, data: Dict) -> str:
        """Generate text weekly report"""
        try:
            trades = data.get('trades', [])
            total_trades = len(trades)
            profitable_trades = data.get('profitable_trades', 0)
            total_pnl = data.get('total_pnl', 0)
            win_rate = data.get('win_rate', 0)
            
            report = f"""
Weekly Trading Report
Date: {datetime.now().strftime('%Y-%m-%d')}

PERFORMANCE SUMMARY
==================
Total Trades: {total_trades}
Profitable Trades: {profitable_trades}
Win Rate: {win_rate:.1f}%
Total P&L: ${total_pnl:+,.2f}

RECENT TRADES
=============
"""
            
            if trades:
                for trade in trades[-10:]:
                    symbol = trade.get('symbol', 'N/A')
                    action = trade.get('action', 'N/A')
                    quantity = trade.get('quantity', 0)
                    price = trade.get('price', 0)
                    timestamp = trade.get('timestamp', 'N/A')
                    
                    report += f"- {timestamp}: {action} {quantity} {symbol} @ ${price:.2f}\n"
            else:
                report += "No trades executed this week.\n"
            
            report += f"""

Report generated by AI Trading Bot
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Text report generation error: {str(e)}")
            return "Error generating report"
    
    def _generate_monthly_report_html(self, data: Dict) -> str:
        """Generate HTML monthly report (more detailed)"""
        # Similar to weekly but more comprehensive
        return self._generate_weekly_report_html(data)
    
    def _generate_monthly_report_text(self, data: Dict) -> str:
        """Generate text monthly report (more detailed)"""
        # Similar to weekly but more comprehensive
        return self._generate_weekly_report_text(data)
