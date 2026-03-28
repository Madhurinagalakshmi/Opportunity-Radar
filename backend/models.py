from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
 
Base = declarative_base()
 
# Database Models
class CorporateFiling(Base):
    __tablename__ = "corporate_filings"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String, index=True)
    company_name = Column(String)
    filing_type = Column(String)  # "insider_trade", "bulk_deal", "quarterly_result", "announcement"
    filing_date = Column(DateTime, index=True)
    title = Column(String)
    description = Column(Text)
    source_url = Column(String)
    raw_data = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
 
class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String, index=True)
    company_name = Column(String)
    signal_type = Column(String)  # "BUY", "SELL", "WATCH"
    confidence_score = Column(Float)  # 0-100
    reasoning = Column(Text)
    source_filing_ids = Column(String)  # Comma-separated filing IDs
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True)
    price_at_signal = Column(Float, nullable=True)
    
class BacktestResult(Base):
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, index=True)
    stock_symbol = Column(String)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    return_pct = Column(Float, nullable=True)
    days_held = Column(Integer, nullable=True)
    outcome = Column(String)  # "profit", "loss", "pending"
    tested_at = Column(DateTime, default=datetime.utcnow)
 
# Pydantic Schemas for API
class FilingSchema(BaseModel):
    stock_symbol: str
    company_name: str
    filing_type: str
    filing_date: datetime
    title: str
    description: str
    source_url: Optional[str] = None
    
    class Config:
        from_attributes = True
 
class SignalSchema(BaseModel):
    id: int
    stock_symbol: str
    company_name: str
    signal_type: str
    confidence_score: float
    reasoning: str
    generated_at: datetime
    price_at_signal: Optional[float] = None
    
    class Config:
        from_attributes = True
 
class SignalCreateSchema(BaseModel):
    stock_symbol: str
    company_name: str
    signal_type: str
    confidence_score: float
    reasoning: str
    source_filing_ids: str
    price_at_signal: Optional[float] = None
 