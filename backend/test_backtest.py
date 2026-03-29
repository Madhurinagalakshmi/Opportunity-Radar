from database import SessionLocal
from backtester import Backtester

db = SessionLocal()
backtester = Backtester()

result = backtester.backtest_all_signals(db)
print(f"Backtested {result['successful_tests']} signals")

report = backtester.generate_performance_report(db)
print(f"Win Rate: {report['win_rate']}%")
print(f"Avg Return: {report['avg_return_pct']}%")

db.close()