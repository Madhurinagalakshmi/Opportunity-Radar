import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from models import Signal, BacktestResult
import pandas as pd
 
class Backtester:
    """Validates signals against historical stock price movements"""
    
    def __init__(self):
        self.holding_period_days = 30  # Default holding period
    
    def backtest_signal(self, signal: Signal, db: Session) -> Dict:
        """
        Backtest a single signal
        Returns profit/loss data
        """
        try:
            # Get historical price data
            ticker = yf.Ticker(f"{signal.stock_symbol}.NS")
            
            # Get data from signal date to 30 days later
            start_date = signal.generated_at.date()
            end_date = start_date + timedelta(days=self.holding_period_days)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty or len(hist) < 2:
                return {"error": "Insufficient price data"}
            
            entry_price = signal.price_at_signal or hist['Close'].iloc[0]
            
            # For BUY signals: check if price went up
            # For SELL signals: check if price went down
            if signal.signal_type == "BUY":
                # Find highest price during holding period
                exit_price = hist['Close'].max()
                peak_date = hist['Close'].idxmax()
            else:  # SELL
                # Find lowest price during holding period
                exit_price = hist['Close'].min()
                peak_date = hist['Close'].idxmin()
            
            # Calculate return
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            # Adjust for signal type (SELL signals profit when price drops)
            if signal.signal_type == "SELL":
                return_pct = -return_pct
            
            # Determine outcome
            if return_pct > 5:
                outcome = "profit"
            elif return_pct < -5:
                outcome = "loss"
            else:
                outcome = "neutral"
            
            # Calculate days held
            days_held = (peak_date - start_date).days
            
            # Save backtest result
            result = BacktestResult(
                signal_id=signal.id,
                stock_symbol=signal.stock_symbol,
                entry_price=entry_price,
                exit_price=exit_price,
                return_pct=round(return_pct, 2),
                days_held=days_held,
                outcome=outcome
            )
            
            db.add(result)
            db.commit()
            
            return {
                "signal_id": signal.id,
                "stock_symbol": signal.stock_symbol,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "return_pct": round(return_pct, 2),
                "days_held": days_held,
                "outcome": outcome
            }
            
        except Exception as e:
            print(f"❌ Error backtesting signal {signal.id}: {e}")
            return {"error": str(e)}
    
    def backtest_all_signals(self, db: Session) -> Dict:
        """Run backtests on all signals that haven't been tested"""
        
        # Get signals without backtest results
        signals = db.query(Signal)\
            .outerjoin(BacktestResult, Signal.id == BacktestResult.signal_id)\
            .filter(BacktestResult.id == None)\
            .all()
        
        results = []
        successful_tests = 0
        
        for signal in signals:
            print(f"🧪 Backtesting: {signal.stock_symbol} {signal.signal_type} signal...")
            result = self.backtest_signal(signal, db)
            
            if "error" not in result:
                results.append(result)
                successful_tests += 1
        
        return {
            "total_signals_tested": len(signals),
            "successful_tests": successful_tests,
            "failed_tests": len(signals) - successful_tests,
            "results": results
        }
    
    def generate_performance_report(self, db: Session) -> Dict:
        """Generate comprehensive performance metrics"""
        
        all_results = db.query(BacktestResult).all()
        
        if not all_results:
            return {"message": "No backtest results available yet"}
        
        # Calculate metrics
        total_signals = len(all_results)
        profitable = [r for r in all_results if r.outcome == "profit"]
        losses = [r for r in all_results if r.outcome == "loss"]
        
        win_rate = (len(profitable) / total_signals) * 100 if total_signals > 0 else 0
       
        avg_return = sum(r.return_pct for r in all_results) / total_signals
        avg_profit = sum(r.return_pct for r in profitable) / len(profitable) if profitable else 0
        avg_loss = sum(r.return_pct for r in losses) / len(losses) if losses else 0
        
        # Best and worst signals
        best_signal = max(all_results, key=lambda x: x.return_pct)
        worst_signal = min(all_results, key=lambda x: x.return_pct)
        
        # Calculate profit on hypothetical ₹1L portfolio
        portfolio_value = 100000  # ₹1 lakh
        total_return_pct = sum(r.return_pct for r in all_results) / total_signals
        estimated_profit = (portfolio_value * total_return_pct) / 100
        
        return {
            "total_signals_tested": total_signals,
            "win_rate": round(win_rate, 2),
            "total_winners": len(profitable),
            "total_losers": len(losses),
            "avg_return_pct": round(avg_return, 2),
            "avg_profit_pct": round(avg_profit, 2),
            "avg_loss_pct": round(avg_loss, 2),
            "best_signal": {
                "stock": best_signal.stock_symbol,
                "return": round(best_signal.return_pct, 2)
            },
            "worst_signal": {
                "stock": worst_signal.stock_symbol,
                "return": round(worst_signal.return_pct, 2)
            },
            "portfolio_simulation": {
                "initial_value": portfolio_value,
                "estimated_profit": round(estimated_profit, 2),
                "final_value": round(portfolio_value + estimated_profit, 2),
                "total_return_pct": round(total_return_pct, 2)
            }
        }
 
 
# Standalone test
if __name__ == "__main__":
    from database import SessionLocal, init_db
    
    init_db()
    db = SessionLocal()
    
    backtester = Backtester()
    
    print("🧪 Running backtests...")
    results = backtester.backtest_all_signals(db)
    
    print(f"\n✅ Backtest Complete:")
    print(f"   Signals tested: {results['successful_tests']}/{results['total_signals_tested']}")
    
    print("\n📊 Generating performance report...")
    report = backtester.generate_performance_report(db)
    
    if "message" not in report:
        print(f"\n💰 Performance Metrics:")
        print(f"   Win Rate: {report['win_rate']}%")
        print(f"   Avg Return: {report['avg_return_pct']}%")
        print(f"   Best Signal: {report['best_signal']['stock']} (+{report['best_signal']['return']}%)")
        print(f"\n   Portfolio Simulation (₹1L invested):")
        print(f"   Estimated Profit: ₹{report['portfolio_simulation']['estimated_profit']:,.2f}")
        print(f"   Final Value: ₹{report['portfolio_simulation']['final_value']:,.2f}")
    
    db.close()