import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import yfinance as yf
import json
from typing import List, Dict
from models import CorporateFiling
from sqlalchemy.orm import Session
 
class DataCollector:
    """Collects corporate filings from NSE/BSE and other sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_nse_announcements(self, days_back: int = 7) -> List[Dict]:
        """
        Fetch recent NSE corporate announcements
        Note: NSE requires proper session handling - this is a simplified version
        """
        announcements = []
        
        try:
            # NSE announcements URL (simplified - actual implementation needs session cookies)
            url = "https://www.nseindia.com/api/corporate-announcements"
            
            # For demo purposes, we'll use mock data
            # In production, implement proper NSE API authentication
            mock_announcements = self._get_mock_nse_data()
            return mock_announcements
            
        except Exception as e:
            print(f"Error fetching NSE data: {e}")
            return self._get_mock_nse_data()
    
    def fetch_insider_trades(self) -> List[Dict]:
        """Fetch insider trading data"""
        # Mock data for demonstration
        # In production, scrape from NSE insider trading section
        return [
            {
                "stock_symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "filing_type": "insider_trade",
                "title": "Promoter Purchase - 50,000 shares",
                "description": "Mukesh D. Ambani acquired 50,000 equity shares at avg price ₹2,850",
                "filing_date": datetime.now() - timedelta(days=2),
                "source_url": "https://nseindia.com/insider-trading"
            },
            {
                "stock_symbol": "TCS",
                "company_name": "Tata Consultancy Services",
                "filing_type": "insider_trade",
                "title": "Promoter Sale - 25,000 shares",
                "description": "N. Chandrasekaran sold 25,000 equity shares at avg price ₹3,650",
                "filing_date": datetime.now() - timedelta(days=1),
                "source_url": "https://nseindia.com/insider-trading"
            }
        ]
    
    def fetch_bulk_deals(self) -> List[Dict]:
        """Fetch bulk deal data"""
        return [
            {
                "stock_symbol": "INFY",
                "company_name": "Infosys Ltd",
                "filing_type": "bulk_deal",
                "title": "Bulk Deal - FII Purchase",
                "description": "Morgan Stanley acquired 1.2% stake (bulk deal) at ₹1,450/share",
                "filing_date": datetime.now() - timedelta(days=1),
                "source_url": "https://nseindia.com/bulk-deals"
            }
        ]
    
    def fetch_quarterly_results(self) -> List[Dict]:
        """Fetch quarterly result announcements"""
        return [
            {
                "stock_symbol": "HDFC",
                "company_name": "HDFC Bank Ltd",
                "filing_type": "quarterly_result",
                "title": "Q3 FY24 Results Announced",
                "description": "Net profit up 28% YoY to ₹16,512 Cr. NII growth 24%. Asset quality improved.",
                "filing_date": datetime.now() - timedelta(days=3),
                "source_url": "https://nseindia.com/results"
            }
        ]
    
    def get_stock_price(self, symbol: str) -> float:
        """Get current stock price using yfinance"""
        try:
            # Add .NS for NSE stocks
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period="1d")
            if not data.empty:
                return round(data['Close'].iloc[-1], 2)
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
        return 0.0
    
    def save_filings_to_db(self, db: Session, filings: List[Dict]):
        """Save collected filings to database"""
        saved_count = 0
        for filing_data in filings:
            # Check if filing already exists
            existing = db.query(CorporateFiling).filter(
                CorporateFiling.stock_symbol == filing_data['stock_symbol'],
                CorporateFiling.title == filing_data['title'],
                CorporateFiling.filing_date == filing_data['filing_date']
            ).first()
            
            if not existing:
                filing = CorporateFiling(
                    stock_symbol=filing_data['stock_symbol'],
                    company_name=filing_data['company_name'],
                    filing_type=filing_data['filing_type'],
                    filing_date=filing_data['filing_date'],
                    title=filing_data['title'],
                    description=filing_data['description'],
                    source_url=filing_data.get('source_url', ''),
                    raw_data = json.dumps(filing_data, default=str)
                )
                db.add(filing)
                saved_count += 1
        
        db.commit()
        return saved_count
    
    def collect_all_data(self, db: Session) -> Dict:
        """Collect all types of corporate filings"""
        all_filings = []
        
        print("📡 Collecting NSE announcements...")
        all_filings.extend(self.fetch_nse_announcements())
        
        print("📡 Collecting insider trades...")
        all_filings.extend(self.fetch_insider_trades())
        
        print("📡 Collecting bulk deals...")
        all_filings.extend(self.fetch_bulk_deals())
        
        print("📡 Collecting quarterly results...")
        all_filings.extend(self.fetch_quarterly_results())
        
        saved = self.save_filings_to_db(db, all_filings)
        
        return {
            "total_collected": len(all_filings),
            "new_filings_saved": saved,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_mock_nse_data(self) -> List[Dict]:
        """Mock NSE announcement data for demonstration"""
        return [
            {
                "stock_symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "filing_type": "announcement",
                "title": "Related Party Transaction - Land Purchase",
                "description": "Subsidiary purchased ₹500 Cr land near Jamnagar refinery. Historically, similar acquisitions preceded capacity expansion announcements.",
                "filing_date": datetime.now() - timedelta(hours=18),
                "source_url": "https://nseindia.com/announcements/reliance"
            },
            {
                "stock_symbol": "TATAMOTORS",
                "company_name": "Tata Motors Ltd",
                "filing_type": "announcement",
                "title": "JLR Q3 Production Update",
                "description": "Jaguar Land Rover production up 15% QoQ. Chip shortage easing. Strong demand in China.",
                "filing_date": datetime.now() - timedelta(days=1),
                "source_url": "https://nseindia.com/announcements/tatamotors"
            }
        ]
 
 
# Standalone test function
if __name__ == "__main__":
    from database import SessionLocal, init_db
    
    init_db()
    db = SessionLocal()
    
    collector = DataCollector()
    result = collector.collect_all_data(db)
    
    print(f"\n✅ Data Collection Complete:")
    print(f"   Total filings collected: {result['total_collected']}")
    print(f"   New filings saved: {result['new_filings_saved']}")
    
    db.close()