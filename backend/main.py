from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
 
from database import get_db, init_db
from models import Signal, CorporateFiling, BacktestResult, SignalSchema, FilingSchema
from data_collector import DataCollector
from ai_analyzer import AIAnalyzer
from backtester import Backtester
 
# Initialize FastAPI app
app = FastAPI(
    title="Opportunity Radar API",
    description="AI-powered stock market signal detection system",
    version="1.0.0"
)
 
# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Opportunity Radar API Started!")
 
# Health check
@app.get("/")
async def root():
    return {
        "message": "Opportunity Radar API",
        "status": "active",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
 
# --- DATA COLLECTION ENDPOINTS ---
 
@app.post("/api/collect-data")
async def collect_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger data collection from NSE/BSE"""
    
    def run_collection():
        collector = DataCollector()
        result = collector.collect_all_data(db)
        print(f" Data collection complete: {result}")
    
    background_tasks.add_task(run_collection)
    
    return {
        "message": "Data collection started in background",
        "status": "processing"
    }
 
# --- SIGNAL ENDPOINTS ---
 
@app.get("/api/signals", response_model=List[SignalSchema])
async def get_signals(
    signal_type: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all active signals, optionally filtered by type"""
    
    query = db.query(Signal).filter(Signal.is_active == True)
    
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type.upper())
    
    signals = query.order_by(Signal.confidence_score.desc()).limit(limit).all()
    
    return signals
 
@app.get("/api/signals/{signal_id}", response_model=SignalSchema)
async def get_signal(signal_id: int, db: Session = Depends(get_db)):
    """Get specific signal details"""
    
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return signal
 
@app.post("/api/analyze")
async def run_analysis(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger AI analysis of recent filings"""
    
    def run_ai_analysis():
        analyzer = AIAnalyzer()
        result = analyzer.analyze_batch(db, limit=20)
        print(f"✅ AI analysis complete: {result}")
    
    background_tasks.add_task(run_ai_analysis)
    
    return {
        "message": "AI analysis started in background",
        "status": "processing"
    }
 
@app.get("/api/signals/summary")
async def get_signal_summary(db: Session = Depends(get_db)):
    """Get summary statistics of active signals"""
    
    analyzer = AIAnalyzer()
    summary = analyzer.get_signal_summary(db)
    
    return summary
 
# --- FILING ENDPOINTS ---
 
@app.get("/api/filings", response_model=List[FilingSchema])
async def get_filings(
    filing_type: str = None,
    days: int = 7,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent corporate filings"""
    
    cutoff_date = datetime.now() - timedelta(days=days)
    query = db.query(CorporateFiling).filter(CorporateFiling.filing_date >= cutoff_date)
    
    if filing_type:
        query = query.filter(CorporateFiling.filing_type == filing_type)
    
    filings = query.order_by(CorporateFiling.filing_date.desc()).limit(limit).all()
    
    return filings
 
# --- BACKTEST ENDPOINTS ---
 
@app.post("/api/backtest")
async def run_backtest(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Run backtests on signals"""
    
    def run_backtest_job():
        backtester = Backtester()
        result = backtester.backtest_all_signals(db)
        print(f"✅ Backtest complete: {result}")
    
    background_tasks.add_task(run_backtest_job)
    
    return {
        "message": "Backtest started in background",
        "status": "processing"
    }
 
@app.get("/api/backtest/report")
async def get_backtest_report(db: Session = Depends(get_db)):
    """Get comprehensive backtest performance report"""
    
    backtester = Backtester()
    report = backtester.generate_performance_report(db)
    
    return report
 
@app.get("/api/backtest/results")
async def get_backtest_results(limit: int = 50, db: Session = Depends(get_db)):
    """Get individual backtest results"""
    
    results = db.query(BacktestResult)\
        .order_by(BacktestResult.tested_at.desc())\
        .limit(limit)\
        .all()
    
    return [
        {
            "signal_id": r.signal_id,
            "stock_symbol": r.stock_symbol,
            "entry_price": r.entry_price,
            "exit_price": r.exit_price,
            "return_pct": r.return_pct,
            "outcome": r.outcome,
            "days_held": r.days_held,
            "tested_at": r.tested_at
        }
        for r in results
    ]
 
# --- STATS ENDPOINTS ---
 
@app.get("/api/stats/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get all dashboard statistics in one call"""
    
    # Signal summary
    analyzer = AIAnalyzer()
    signal_summary = analyzer.get_signal_summary(db)
    
    # Recent filings count
    recent_filings = db.query(CorporateFiling)\
        .filter(CorporateFiling.filing_date >= datetime.now() - timedelta(days=7))\
        .count()
    
    # Backtest summary
    backtester = Backtester()
    backtest_report = backtester.generate_performance_report(db)
    
    # Top signals
    top_signals = db.query(Signal)\
        .filter(Signal.is_active == True)\
        .order_by(Signal.confidence_score.desc())\
        .limit(5)\
        .all()
    
    return {
        "signal_summary": signal_summary,
        "recent_filings_count": recent_filings,
        "backtest_performance": backtest_report,
        "top_signals": [
            {
                "id": s.id,
                "stock_symbol": s.stock_symbol,
                "company_name": s.company_name,
                "signal_type": s.signal_type,
                "confidence_score": s.confidence_score,
                "reasoning": s.reasoning[:150] + "..." if len(s.reasoning) > 150 else s.reasoning
            }
            for s in top_signals
        ],
        "timestamp": datetime.now().isoformat()
    }
 
# --- AUTOMATED JOBS ---
 
@app.post("/api/run-full-pipeline")
async def run_full_pipeline(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Run complete pipeline: collect → analyze → backtest"""
    
    async def pipeline():
        print(" Step 1/3: Collecting data...")
        collector = DataCollector()
        collector.collect_all_data(db)
        
        print(" Step 2/3: Running AI analysis...")
        analyzer = AIAnalyzer()
        analyzer.analyze_batch(db, limit=20)
        
        print(" Step 3/3: Running backtests...")
        backtester = Backtester()
        backtester.backtest_all_signals(db)
        
        print(" Full pipeline complete!")
    
    background_tasks.add_task(pipeline)
    
    return {
        "message": "Full pipeline started: data collection → AI analysis → backtesting",
        "status": "processing"
    }
 
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)