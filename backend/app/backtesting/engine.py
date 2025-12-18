"""
Backtesting Engine (Simplified)
This is a BASIC implementation for proof-of-concept
For production, consider using backtesting.py library or zipline
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd

from app.services.stock_api_service import stock_api_service
from app.signal_history import SignalHistoryService, get_signal_history_service, SignalRecord
from .schemas import BacktestConfig, BacktestResult, TradeResult

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Simple backtesting engine
    
    NOTE: This is a SIMPLIFIED implementation
    - Uses historical signals from signal_history
    - Simulates trades based on signal directional bias
    - Calculates basic performance metrics
    """
    
    def __init__(self, signal_history: Optional[SignalHistoryService] = None):
        self.signal_history = signal_history or get_signal_history_service()
    
    def run(self, config: BacktestConfig) -> Optional[BacktestResult]:
        """
        Run backtest for given configuration
        
        NOTE: Requires existing signals in signal_history
        """
        
        try:
            # Get all signals for this symbol/timeframe in the date range
            days_back = (config.end_date - config.start_date).days
            
            signals = self.signal_history.get_signals(
                symbol=config.symbol,
                timeframe=config.timeframe,
                days_back=days_back + 30,  # Extra buffer
                limit=1000
            )
            
            # Filter to date range
            signals = [
                s for s in signals
                if config.start_date <= s.timestamp <= config.end_date
            ]
            
            if not signals:
                logger.warning(f"No signals found for {config.symbol} in date range")
                return None
            
            logger.info(f"Found {len(signals)} signals for backtest")
            
            # Simulate trades
            trades: List[TradeResult] = []
            capital = config.initial_capital
            
            for signal in signals:
                # Determine trade direction from signal
                if signal.directional_bias == "neutral":
                    continue  # Skip neutral signals
                
                direction = "long" if signal.directional_bias == "bullish" else "short"
                
                # Calculate position size
                position_value = capital * (config.position_size_percent / 100.0)
                shares = int(position_value / signal.entry_price)
                
                if shares == 0:
                    continue
                
                # Simplified exit simulation
                # For PoC, assume we hold for timeframe duration
                holding_days = 7 if config.timeframe == "swing" else 21
                
                exit_date = signal.timestamp + timedelta(days=holding_days)
                
                # Simulate price movement (simplified - uses scenario midpoint)
                if direction == "long":
                    # If bullish, assume we hit somewhere in base-bull range
                    exit_price = (signal.base_case_high + signal.bull_case_low) / 2
                else:
                    # If bearish, assume we hit somewhere in bear-base range
                    exit_price = (signal.bear_case_high + signal.base_case_low) / 2
                
                # Apply slippage
                entry_price_actual = signal.entry_price * (1 + config.slippage_percent / 100)
                exit_price_actual = exit_price * (1 - config.slippage_percent / 100)
                
               # Calculate P&L
                if direction == "long":
                    pnl = (exit_price_actual - entry_price_actual) * shares
                else:  # short
                    pnl = (entry_price_actual - exit_price_actual) * shares
                
                pnl_percent = (pnl / position_value) * 100
                
                # Determine exit reason (simplified)
                if pnl > 0:
                    exit_reason = "target_hit"
                elif pnl < -(position_value * 0.05):  # 5% stop
                    exit_reason = "stop_hit"
                else:
                    exit_reason = "time_exit"
                
                # Update capital
                capital += pnl
                
                # Record trade
                trade = TradeResult(
                    entry_date=signal.timestamp,
                    entry_price=entry_price_actual,
                    exit_date=exit_date,
                    exit_price=exit_price_actual,
                    direction=direction,
                    shares=shares,
                    position_value=position_value,
                    pnl=round(pnl, 2),
                    pnl_percent=round(pnl_percent, 2),
                    exit_reason=exit_reason,
                    signal_id=signal.signal_id,
                    confidence=signal.confidence_score,
                    risk_score=signal.risk_score
                )
                
                trades.append(trade)
            
            if not trades:
                logger.warning("No trades executed in backtest")
                return None
            
            # Calculate statistics
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            breakeven_trades = [t for t in trades if t.pnl == 0]
            
            win_rate = len(winning_trades) / len(trades)
            
            avg_win = sum(t.pnl_percent for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = abs(sum(t.pnl_percent for t in losing_trades) / len(losing_trades)) if losing_trades else 0
            
            total_wins = sum(t.pnl for t in winning_trades)
            total_losses = abs(sum(t.pnl for t in losing_trades))
            
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            # Calculate drawdown (simplified)
            capital_curve = [config.initial_capital]
            for trade in trades:
                capital_curve.append(capital_curve[-1] + trade.pnl)
            
            peak = capital_curve[0]
            max_dd = 0
            for val in capital_curve:
                if val > peak:
                    peak = val
                dd = ((peak - val) / peak) * 100
                if dd > max_dd:
                    max_dd = dd
            
            # Calculate returns
            total_return = ((capital - config.initial_capital) / config.initial_capital) * 100
            
            trading_days = (config.end_date - config.start_date).days
            years = trading_days / 252  # Assuming 252 trading days per year
            annualized_return = ((capital / config.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
            
            # Sharpe ratio (simplified - assumes risk-free rate = 0)
            returns = [t.pnl_percent for t in trades]
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe_ratio = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
            
            result = BacktestResult(
                config=config,
                total_trades=len(trades),
                winning_trades=len(winning_trades),
                losing_trades=len(losing_trades),
                breakeven_trades=len(breakeven_trades),
                win_rate=round(win_rate, 3),
                avg_win_percent=round(avg_win, 2),
                avg_loss_percent=round(avg_loss, 2),
                profit_factor=round(profit_factor, 2),
                max_drawdown_percent=round(max_dd, 2),
                sharpe_ratio=round(sharpe_ratio, 2),
                total_return_percent=round(total_return, 2),
                annualized_return_percent=round(annualized_return, 2),
                initial_capital=config.initial_capital,
                final_capital=round(capital, 2),
                trades=trades,
                backtest_start=config.start_date,
                backtest_end=config.end_date,
                trading_days=trading_days
            )
            
            logger.info(f"✅ Backtest complete: {len(trades)} trades, {win_rate:.1%} win rate, {total_return:.2f}% return")
            return result
            
        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            import traceback
            traceback.print_exc()
            return None


def run_backtest(config: BacktestConfig) -> Optional[BacktestResult]:
    """Convenience function to run a backtest"""
    engine = BacktestEngine()
    return engine.run(config)
