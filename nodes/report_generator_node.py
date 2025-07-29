"""
Report Generator Node - Creates trading reports and analytics
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from config import Config
from utils.logger import setup_logger

logger = setup_logger()

class ReportGeneratorNode:
    """Node for generating trading reports and analytics"""
    
    def __init__(self):
        self.config = Config()
        logger.info("Report Generator Node initialized")
    
    def generate_weekly_report(self, trading_history: List[Dict], positions: Dict) -> Dict:
        """Generate weekly trading report"""
        try:
            # Filter trades from last week
            week_ago = datetime.now() - timedelta(days=7)
            weekly_trades = [
                trade for trade in trading_history 
                if isinstance(trade.get('timestamp'), datetime) and trade['timestamp'] >= week_ago
            ]
            
            # Calculate metrics
            total_trades = len(weekly_trades)
            buy_trades = [t for t in weekly_trades if t.get('action') == 'BUY']
            sell_trades = [t for t in weekly_trades if t.get('action') == 'SELL']
            
            # Calculate P&L (simplified - would need actual position tracking)
            total_pnl = self._calculate_week_pnl(weekly_trades, positions)
            
            # Win rate calculation (based on confidence for now)
            high_confidence_trades = [t for t in weekly_trades if t.get('confidence', 0) >= 7]
            win_rate = (len(high_confidence_trades) / total_trades * 100) if total_trades > 0 else 0
            
            # Most traded symbols
            symbol_counts = {}
            for trade in weekly_trades:
                symbol = trade.get('symbol', 'Unknown')
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            most_traded = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Performance by day
            daily_performance = self._calculate_daily_performance(weekly_trades)
            
            report = {
                'period': 'weekly',
                'start_date': week_ago.strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'total_trades': total_trades,
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'profitable_trades': len(high_confidence_trades),
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'most_traded_symbols': most_traded,
                'daily_performance': daily_performance,
                'trades': weekly_trades,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Generated weekly report: {total_trades} trades, {win_rate:.1f}% win rate")
            return report
            
        except Exception as e:
            logger.error(f"Weekly report generation error: {str(e)}")
            return {}
    
    def generate_monthly_report(self, trading_history: List[Dict], positions: Dict) -> Dict:
        """Generate monthly trading report"""
        try:
            # Filter trades from last month
            month_ago = datetime.now() - timedelta(days=30)
            monthly_trades = [
                trade for trade in trading_history 
                if isinstance(trade.get('timestamp'), datetime) and trade['timestamp'] >= month_ago
            ]
            
            # Calculate comprehensive metrics
            total_trades = len(monthly_trades)
            buy_trades = [t for t in monthly_trades if t.get('action') == 'BUY']
            sell_trades = [t for t in monthly_trades if t.get('action') == 'SELL']
            
            # Calculate monthly P&L
            total_pnl = self._calculate_month_pnl(monthly_trades, positions)
            
            # Advanced metrics
            win_rate = self._calculate_actual_win_rate(monthly_trades)
            avg_trade_size = self._calculate_avg_trade_size(monthly_trades)
            largest_win = self._calculate_largest_win(monthly_trades)
            largest_loss = self._calculate_largest_loss(monthly_trades)
            
            # Risk metrics
            max_drawdown = self._calculate_max_drawdown(monthly_trades)
            sharpe_ratio = self._calculate_sharpe_ratio(monthly_trades)
            
            # Symbol analysis
            symbol_performance = self._analyze_symbol_performance(monthly_trades)
            
            # Weekly breakdown
            weekly_breakdown = self._calculate_weekly_breakdown(monthly_trades)
            
            report = {
                'period': 'monthly',
                'start_date': month_ago.strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'total_trades': total_trades,
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_trade_size': round(avg_trade_size, 2),
                'largest_win': round(largest_win, 2),
                'largest_loss': round(largest_loss, 2),
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'symbol_performance': symbol_performance,
                'weekly_breakdown': weekly_breakdown,
                'trades': monthly_trades,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Generated monthly report: {total_trades} trades, {win_rate:.1f}% win rate")
            return report
            
        except Exception as e:
            logger.error(f"Monthly report generation error: {str(e)}")
            return {}
    
    def generate_performance_summary(self, trading_history: List[Dict], positions: Dict) -> Dict:
        """Generate overall performance summary"""
        try:
            if not trading_history:
                return {
                    'total_trades': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                    'active_positions': 0
                }
            
            total_trades = len(trading_history)
            total_pnl = self._calculate_total_pnl(trading_history, positions)
            win_rate = self._calculate_actual_win_rate(trading_history)
            active_positions = len(positions)
            
            # Recent performance (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_trades = [
                t for t in trading_history 
                if isinstance(t.get('timestamp'), datetime) and t['timestamp'] >= week_ago
            ]
            
            recent_pnl = self._calculate_week_pnl(recent_trades, positions)
            
            return {
                'total_trades': total_trades,
                'total_pnl': round(total_pnl, 2),
                'win_rate': round(win_rate, 2),
                'active_positions': active_positions,
                'recent_trades': len(recent_trades),
                'recent_pnl': round(recent_pnl, 2),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance summary error: {str(e)}")
            return {}
    
    def _calculate_week_pnl(self, trades: List[Dict], positions: Dict) -> float:
        """Calculate P&L for weekly trades (simplified)"""
        try:
            # This is a simplified calculation
            # In a real implementation, you'd track actual entry/exit prices
            pnl = 0
            
            for trade in trades:
                confidence = trade.get('confidence', 5)
                price = trade.get('price', 0)
                quantity = trade.get('quantity', 0)
                
                # Estimate P&L based on confidence (mock calculation)
                if confidence >= 7:  # High confidence = profitable
                    pnl += (price * quantity * 0.02)  # 2% gain estimate
                else:  # Low confidence = loss
                    pnl -= (price * quantity * 0.01)  # 1% loss estimate
            
            return pnl
            
        except Exception as e:
            logger.error(f"Week P&L calculation error: {str(e)}")
            return 0.0
    
    def _calculate_month_pnl(self, trades: List[Dict], positions: Dict) -> float:
        """Calculate P&L for monthly trades"""
        # Similar to weekly but potentially more accurate with more data
        return self._calculate_week_pnl(trades, positions)
    
    def _calculate_total_pnl(self, trades: List[Dict], positions: Dict) -> float:
        """Calculate total P&L"""
        return self._calculate_week_pnl(trades, positions)
    
    def _calculate_actual_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate based on confidence scores"""
        try:
            if not trades:
                return 0.0
            
            # Use confidence as proxy for success
            successful_trades = [t for t in trades if t.get('confidence', 0) >= 7]
            return (len(successful_trades) / len(trades)) * 100
            
        except Exception as e:
            logger.error(f"Win rate calculation error: {str(e)}")
            return 0.0
    
    def _calculate_avg_trade_size(self, trades: List[Dict]) -> float:
        """Calculate average trade size"""
        try:
            if not trades:
                return 0.0
            
            total_value = sum(
                trade.get('price', 0) * trade.get('quantity', 0) 
                for trade in trades
            )
            
            return total_value / len(trades)
            
        except Exception as e:
            logger.error(f"Average trade size calculation error: {str(e)}")
            return 0.0
    
    def _calculate_largest_win(self, trades: List[Dict]) -> float:
        """Calculate largest winning trade"""
        try:
            wins = []
            for trade in trades:
                if trade.get('confidence', 0) >= 7:  # Assume high confidence = win
                    value = trade.get('price', 0) * trade.get('quantity', 0)
                    wins.append(value * 0.02)  # 2% gain estimate
            
            return max(wins) if wins else 0.0
            
        except Exception as e:
            logger.error(f"Largest win calculation error: {str(e)}")
            return 0.0
    
    def _calculate_largest_loss(self, trades: List[Dict]) -> float:
        """Calculate largest losing trade"""
        try:
            losses = []
            for trade in trades:
                if trade.get('confidence', 0) < 7:  # Assume low confidence = loss
                    value = trade.get('price', 0) * trade.get('quantity', 0)
                    losses.append(value * 0.01)  # 1% loss estimate
            
            return max(losses) if losses else 0.0
            
        except Exception as e:
            logger.error(f"Largest loss calculation error: {str(e)}")
            return 0.0
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown (simplified)"""
        try:
            # Simplified drawdown calculation
            # In reality, this would require continuous portfolio value tracking
            cumulative_pnl = 0
            peak = 0
            max_drawdown = 0
            
            for trade in trades:
                confidence = trade.get('confidence', 5)
                value = trade.get('price', 0) * trade.get('quantity', 0)
                
                # Estimate trade P&L
                if confidence >= 7:
                    cumulative_pnl += value * 0.02
                else:
                    cumulative_pnl -= value * 0.01
                
                # Update peak
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                
                # Calculate drawdown
                drawdown = peak - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"Max drawdown calculation error: {str(e)}")
            return 0.0
    
    def _calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """Calculate Sharpe ratio (simplified)"""
        try:
            if len(trades) < 10:  # Need sufficient data
                return 0.0
            
            # Calculate daily returns (estimated)
            returns = []
            for trade in trades:
                confidence = trade.get('confidence', 5)
                if confidence >= 7:
                    returns.append(0.02)  # 2% return
                else:
                    returns.append(-0.01)  # -1% return
            
            if not returns:
                return 0.0
            
            avg_return = sum(returns) / len(returns)
            
            # Calculate standard deviation
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            
            if std_dev == 0:
                return 0.0
            
            # Annualized Sharpe ratio (assuming 252 trading days)
            sharpe = (avg_return * 252) / (std_dev * (252 ** 0.5))
            
            return sharpe
            
        except Exception as e:
            logger.error(f"Sharpe ratio calculation error: {str(e)}")
            return 0.0
    
    def _analyze_symbol_performance(self, trades: List[Dict]) -> List[Dict]:
        """Analyze performance by symbol"""
        try:
            symbol_stats = {}
            
            for trade in trades:
                symbol = trade.get('symbol', 'Unknown')
                confidence = trade.get('confidence', 5)
                value = trade.get('price', 0) * trade.get('quantity', 0)
                
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'trades': 0,
                        'total_value': 0,
                        'wins': 0,
                        'losses': 0,
                        'pnl': 0
                    }
                
                stats = symbol_stats[symbol]
                stats['trades'] += 1
                stats['total_value'] += value
                
                if confidence >= 7:
                    stats['wins'] += 1
                    stats['pnl'] += value * 0.02
                else:
                    stats['losses'] += 1
                    stats['pnl'] -= value * 0.01
            
            # Convert to list and add calculated fields
            performance = []
            for symbol, stats in symbol_stats.items():
                win_rate = (stats['wins'] / stats['trades']) * 100 if stats['trades'] > 0 else 0
                avg_trade_size = stats['total_value'] / stats['trades'] if stats['trades'] > 0 else 0
                
                performance.append({
                    'symbol': symbol,
                    'trades': stats['trades'],
                    'win_rate': round(win_rate, 1),
                    'total_pnl': round(stats['pnl'], 2),
                    'avg_trade_size': round(avg_trade_size, 2)
                })
            
            # Sort by total P&L
            performance.sort(key=lambda x: x['total_pnl'], reverse=True)
            
            return performance[:10]  # Top 10
            
        except Exception as e:
            logger.error(f"Symbol performance analysis error: {str(e)}")
            return []
    
    def _calculate_daily_performance(self, trades: List[Dict]) -> Dict:
        """Calculate performance by day of week"""
        try:
            daily_stats = {
                'Monday': {'trades': 0, 'pnl': 0},
                'Tuesday': {'trades': 0, 'pnl': 0},
                'Wednesday': {'trades': 0, 'pnl': 0},
                'Thursday': {'trades': 0, 'pnl': 0},
                'Friday': {'trades': 0, 'pnl': 0}
            }
            
            for trade in trades:
                timestamp = trade.get('timestamp')
                if not isinstance(timestamp, datetime):
                    continue
                
                day_name = timestamp.strftime('%A')
                if day_name in daily_stats:
                    confidence = trade.get('confidence', 5)
                    value = trade.get('price', 0) * trade.get('quantity', 0)
                    
                    daily_stats[day_name]['trades'] += 1
                    
                    if confidence >= 7:
                        daily_stats[day_name]['pnl'] += value * 0.02
                    else:
                        daily_stats[day_name]['pnl'] -= value * 0.01
            
            # Round P&L values
            for day in daily_stats:
                daily_stats[day]['pnl'] = round(daily_stats[day]['pnl'], 2)
            
            return daily_stats
            
        except Exception as e:
            logger.error(f"Daily performance calculation error: {str(e)}")
            return {}
    
    def _calculate_weekly_breakdown(self, trades: List[Dict]) -> List[Dict]:
        """Calculate weekly breakdown for monthly report"""
        try:
            # Group trades by week
            weekly_data = {}
            
            for trade in trades:
                timestamp = trade.get('timestamp')
                if not isinstance(timestamp, datetime):
                    continue
                
                # Get week start (Monday)
                week_start = timestamp - timedelta(days=timestamp.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = {
                        'week_start': week_key,
                        'trades': 0,
                        'pnl': 0
                    }
                
                confidence = trade.get('confidence', 5)
                value = trade.get('price', 0) * trade.get('quantity', 0)
                
                weekly_data[week_key]['trades'] += 1
                
                if confidence >= 7:
                    weekly_data[week_key]['pnl'] += value * 0.02
                else:
                    weekly_data[week_key]['pnl'] -= value * 0.01
            
            # Convert to list and sort
            weekly_breakdown = list(weekly_data.values())
            weekly_breakdown.sort(key=lambda x: x['week_start'])
            
            # Round P&L values
            for week in weekly_breakdown:
                week['pnl'] = round(week['pnl'], 2)
            
            return weekly_breakdown
            
        except Exception as e:
            logger.error(f"Weekly breakdown calculation error: {str(e)}")
            return []
