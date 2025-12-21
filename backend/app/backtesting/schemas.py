"""
Backtesting Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime


class BacktestConfig(BaseModel):
    """Configuration for a backtest run"""
    symbol: str
    timeframe: Literal["swing", "positional"]
    start_date: datetime
    end_date: datetime
    
    # Position sizing
    initial_capital: float = 100000.0
    position_size_percent: float = Field(default=10.0, ge=1.0, le=100.0)
    
    # Risk management
    use_stop_loss: bool = True
    stop_loss_multiplier: float = 1.0  # Multiplier for ATR-based stop
    
    # Execution
    slippage_percent: float = 0.1  # Assumed slippage on entry/exit


class TradeResult(BaseModel):
    """Result of a single trade"""
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    
    direction: Literal["long", "short"]
    shares: int
    position_value: float
    
    pnl: float
    pnl_percent: float
    
    exit_reason: Literal["target_hit", "stop_hit", "time_exit", "signal_reversal"]
    
    # Signal that triggered this trade
    signal_id: str
    confidence: float
    risk_score: int


class BacktestResult(BaseModel):
    """Complete backtest results"""
    config: BacktestConfig
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    
    # Performance metrics
    win_rate: float = Field(ge=0.0, le=1.0)
    avg_win_percent: float
    avg_loss_percent: float
    profit_factor: float
    
    # Risk metrics
    max_drawdown_percent: float
    sharpe_ratio: float
    
    # Returns
    total_return_percent: float
    annualized_return_percent: float
    
    # Capital progression
    initial_capital: float
    final_capital: float
    
    # All trades
    trades: List[TradeResult]
    
    # Time period
    backtest_start: datetime
    backtest_end: datetime
    trading_days: int
