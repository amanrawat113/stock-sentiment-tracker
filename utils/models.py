from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from utils.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(String(100), unique=True, nullable=False, index=True) 
    scrip_code = Column(Integer, nullable=False, index=True)               
    company_name = Column(String(255), nullable=False)           
    headline = Column(String(1000), nullable=False)                       
    category = Column(String(100), nullable=True)                        
    subcategory = Column(String(100), nullable=True)
    announced_at = Column(DateTime, nullable=False, index=True)  
    fetched_at = Column(DateTime, default=datetime.utcnow)
    full_text = Column(Text, nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_scored_at = Column(DateTime, nullable=True)


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True) 
    price = Column(Float, nullable=False)
    change_percent = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)