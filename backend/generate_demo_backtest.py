"""
Mock Backtest Data Generator
For hackathon demo purposes - generates realistic backtest results
"""
 
from database import SessionLocal
from models import Signal, BacktestResult
import random
from datetime import datetime
 
def generate_demo_backtest_data():
    """Generate realistic backtest results for demo"""
    
    db = SessionLocal()
    
    # Get all signals
    signals = db.query(Signal).all()
    
    if not signals:
        print("❌ No signals found. Run data collection first.")
        return
    
    print(f"📊 Generating demo backtest data for {len(signals)} signals...")
    
    # Clear existing backtest results
    db.query(BacktestResult).delete()
    db.commit()
    
    successful_backtests = 0
    
    for signal in signals:
        # Generate realistic backtest data
        
        # Win rate should be around 70-75%
        is_winner = random.random() < 0.72
        
        if is_winner:
            # Profitable trade
            return_pct = random.uniform(3.5, 15.0)  # 3.5% to 15% profit
            outcome = "profit"
        else:
            # Loss trade
            return_pct = random.uniform(-8.0, -2.0)  # -2% to -8% loss
            outcome = "loss"
        
        # Generate realistic entry/exit prices
        entry_price = signal.price_at_signal or random.uniform(500, 3000)
        exit_price = entry_price * (1 + return_pct / 100)
        
        # Days held (usually 10-30 days)
        days_held = random.randint(12, 28)
        
        # Create backtest result
        result = BacktestResult(
            signal_id=signal.id,
            stock_symbol=signal.stock_symbol,
            entry_price=round(entry_price, 2),
            exit_price=round(exit_price, 2),
            return_pct=round(return_pct, 2),
            days_held=days_held,
            outcome=outcome,
            tested_at=datetime.now()
        )
        
        db.add(result)
        successful_backtests += 1
    
    db.commit()
    
    # Generate performance report
    all_results = db.query(BacktestResult).all()
    
    total_signals = len(all_results)
    profitable = [r for r in all_results if r.outcome == "profit"]
    losses = [r for r in all_results if r.outcome == "loss"]
    
    win_rate = (len(profitable) / total_signals) * 100 if total_signals > 0 else 0
    avg_return = sum(r.return_pct for r in all_results) / total_signals if total_signals > 0 else 0
    avg_profit = sum(r.return_pct for r in profitable) / len(profitable) if profitable else 0
    avg_loss = sum(r.return_pct for r in losses) / len(losses) if losses else 0
    
    # Portfolio simulation
    portfolio_value = 100000  # ₹1 lakh
    total_return_pct = avg_return
    estimated_profit = (portfolio_value * total_return_pct) / 100
    final_value = portfolio_value + estimated_profit
    
    print("\n" + "="*60)
    print("✅ DEMO BACKTEST DATA GENERATED!")
    print("="*60)
    print(f"\n📊 Performance Metrics:")
    print(f"   Total Signals: {total_signals}")
    print(f"   Win Rate: {win_rate:.1f}%")
    print(f"   Winners: {len(profitable)}")
    print(f"   Losers: {len(losses)}")
    print(f"   Avg Return: {avg_return:.2f}%")
    print(f"   Avg Profit (winners): {avg_profit:.2f}%")
    print(f"   Avg Loss (losers): {avg_loss:.2f}%")
    print(f"\n💰 Portfolio Simulation (₹1L invested):")
    print(f"   Initial Value: ₹{portfolio_value:,}")
    print(f"   Estimated Profit: ₹{estimated_profit:,.2f}")
    print(f"   Final Value: ₹{final_value:,.2f}")
    print(f"   Total Return: {total_return_pct:.2f}%")
    print("\n" + "="*60)
    print("🎯 Now refresh your dashboard to see the stats!")
    print("="*60 + "\n")
    
    db.close()
 
if __name__ == "__main__":
    generate_demo_backtest_data()