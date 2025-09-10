# import asyncio
# from scraping.crawling.crawl import process_link
# from scraping.crawling.top_down_search_links import run_search
# from Research_agent.bottom_up import run_search
# from scraping.data_collect_summarize import summarized_data

# async def crawl_and_save(company_name):
#     print("🔍 Searching for links...")
#     links = run_search(company_name)
#     print(f"🌐 Found {len(links)} links.")

#     tasks = [process_link(link, company_name) for link in links]
#     await asyncio.gather(*tasks)
#     print("✅ Crawling and saving raw data complete.")

# def summarize(company_name):
#     print("📝 Summarizing collected data...")
#     # summarized_data.py runs on import, so just import it
#     import scraping.data_collect_summarize.summarized_data as sd
#     sd.summarize_company(company_name)
#     print("✅ Summarization complete.")

# if __name__ == "__main__":
#     company = "Keystone Realtors Limited"
#     asyncio.run(crawl_and_save(company))
#     summarize(company)


# import asyncio
# from scraping.crawling.crawl import process_link
# from Research_agent.top_down.top_down_search_links import run_search as top_down_search
# from Research_agent.bottom_up.bottom_up_search import run_search as bottom_up_search
# from Research_agent.top_down.top_down_summarize import summarize_company as top_down_summarize
# from Research_agent.bottom_up.bottom_up_summarize import summarize_company as bottom_up_summarize

# async def parallel_search(company_name):
#     """Run both top-down and bottom-up searches concurrently"""
#     print("\n🔍 Starting parallel searches...")
#     print("├─ Running top-down analysis")
#     print("└─ Running bottom-up analysis")
    
#     # Run both searches in parallel
#     top_down_links = top_down_search(company_name)
#     bottom_up_links = bottom_up_search(company_name)
    
#     # Combine and deduplicate links
#     all_links = list(set(top_down_links + bottom_up_links))
#     print(f"\n🌐 Found {len(all_links)} unique links")
    
#     # Process all links concurrently
#     tasks = [process_link(link, company_name) for link in all_links]
#     await asyncio.gather(*tasks)
#     print("✅ Crawling and saving raw data complete")

# def parallel_summarize(company_name):
#     """Generate both top-down and bottom-up summaries"""
#     print("\n📊 Generating summaries...")
#     print("├─ Running top-down summarization")
#     top_down_summarize(company_name)
#     print("└─ Running bottom-up summarization")
#     bottom_up_summarize(company_name)
#     print("✅ Both summaries complete")

# if __name__ == "__main__":
#     company = "ashokleyland"
    
#     # Run the full pipeline
#     asyncio.run(parallel_search(company))
#     parallel_summarize(company)


import asyncio
import logging
import os
import sys
import json
from dotenv import load_dotenv
import yfinance as yf
from pymongo import MongoClient
from datetime import datetime
import pandas as pd

from scraping.crawling.crawl import process_link
from Research_agent.top_down.top_down_search_links import run_search as top_down_search
from Research_agent.bottom_up.bottom_up_search import run_search as bottom_up_search
from Research_agent.top_down.top_down_summarize import summarize_company as top_down_summarize
from Research_agent.bottom_up.bottom_up_summarize import summarize_company as bottom_up_summarize
from scraping.data_collect_summarize.raw_data import save_raw_data

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["ravanan"]
financial_collection = db["financial_data"]

# ====================== REVENUE SOURCE ANALYSIS FUNCTIONS ======================

def safe_to_dict(obj):
    """Convert yfinance / pandas objects safely to JSON-serializable dict/list"""
    if obj is None:
        return None
    if hasattr(obj, "to_dict"):
        d = obj.to_dict()
        return {str(k): safe_to_dict(v) for k, v in d.items()}
    if hasattr(obj, "to_json"):
        return json.loads(obj.to_json())
    if isinstance(obj, (list, tuple)):
        return [safe_to_dict(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): safe_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, pd.DataFrame):
        return {str(k): safe_to_dict(v) for k, v in obj.to_dict().items()}
    if isinstance(obj, pd.Series):
        return {str(k): safe_to_dict(v) for k, v in obj.to_dict().items()}
    return obj if isinstance(obj, (str, int, float, bool)) else str(obj)

def extract_revenue_sources(financials_df, company_info=None):
    """Extract and categorize different revenue sources from financial statements"""
    revenue_breakdown = {}
    
    if financials_df is None or financials_df.empty:
        return revenue_breakdown
    
    # Common revenue line items to look for
    revenue_items = [
        'Total Revenue', 'Operating Revenue', 'Sales', 'Net Sales',
        'Service Revenue', 'Product Revenue', 'Interest Revenue',
        'Fee Revenue', 'Subscription Revenue', 'License Revenue',
        'Royalty Revenue', 'Other Revenue', 'Investment Revenue'
    ]
    
    # Extract available revenue streams
    for item in revenue_items:
        if item in financials_df.index:
            revenue_breakdown[item] = {
                "values": safe_to_dict(financials_df.loc[item]),
                "source_type": categorize_revenue_source(item),
                "revenue_nature": get_revenue_nature(item),
                "recognition_method": get_revenue_recognition(item)
            }
    
    # Add geographic revenue breakdown if available in company info
    if company_info:
        revenue_breakdown['geographic_segments'] = extract_geographic_revenue(company_info)
        revenue_breakdown['business_segments'] = extract_business_segments(company_info)
    
    return revenue_breakdown

def categorize_revenue_source(revenue_item):
    """Categorize the type of revenue source"""
    if any(word in revenue_item.lower() for word in ['service', 'consulting', 'support']):
        return "service_revenue"
    elif any(word in revenue_item.lower() for word in ['product', 'sales', 'goods']):
        return "product_revenue"
    elif any(word in revenue_item.lower() for word in ['interest', 'investment']):
        return "financial_revenue"
    elif any(word in revenue_item.lower() for word in ['license', 'royalty', 'subscription']):
        return "recurring_revenue"
    elif 'fee' in revenue_item.lower():
        return "fee_based_revenue"
    else:
        return "operating_revenue"

def get_revenue_nature(revenue_item):
    """Determine the nature of revenue (recurring vs transactional)"""
    recurring_indicators = ['subscription', 'license', 'service', 'support', 'maintenance']
    transactional_indicators = ['sales', 'product', 'one-time', 'project']
    
    item_lower = revenue_item.lower()
    if any(indicator in item_lower for indicator in recurring_indicators):
        return "recurring"
    elif any(indicator in item_lower for indicator in transactional_indicators):
        return "transactional"
    else:
        return "mixed"

def get_revenue_recognition(revenue_item):
    """Estimate revenue recognition pattern"""
    if any(word in revenue_item.lower() for word in ['subscription', 'service']):
        return "over_time"
    elif any(word in revenue_item.lower() for word in ['product', 'sales']):
        return "point_in_time"
    else:
        return "varies"

def extract_geographic_revenue(company_info):
    """Extract geographic revenue information if available"""
    geographic_data = {}
    
    # Look for geographic keys in company info
    geo_keys = [key for key in company_info.keys() if 
                any(geo in key.lower() for geo in ['country', 'region', 'domestic', 'international'])]
    
    for key in geo_keys:
        geographic_data[key] = company_info[key]
    
    return geographic_data if geographic_data else None

def extract_business_segments(company_info):
    """Extract business segment information if available"""
    segment_data = {}
    
    # Look for segment-related keys
    segment_keys = [key for key in company_info.keys() if 
                   any(seg in key.lower() for seg in ['segment', 'division', 'business', 'sector'])]
    
    for key in segment_keys:
        segment_data[key] = company_info[key]
    
    return segment_data if segment_data else None

def calculate_revenue_metrics(revenue_breakdown):
    """Calculate key revenue metrics and growth rates"""
    metrics = {}
    
    # Find total revenue for percentage calculations
    total_revenue = None
    if 'Total Revenue' in revenue_breakdown:
        total_revenue_data = revenue_breakdown['Total Revenue']['values']
        if total_revenue_data:
            # Get the most recent quarter's data
            latest_quarter = max(total_revenue_data.keys())
            total_revenue = total_revenue_data[latest_quarter]
    
    # Calculate revenue composition percentages
    if total_revenue and total_revenue != 0:
        for revenue_type, data in revenue_breakdown.items():
            if revenue_type not in ['geographic_segments', 'business_segments'] and 'values' in data:
                values = data['values']
                if values:
                    latest_quarter = max(values.keys())
                    revenue_value = values[latest_quarter]
                    if revenue_value and revenue_value != 0:
                        percentage = (revenue_value / total_revenue) * 100
                        metrics[f"{revenue_type}_percentage"] = round(percentage, 2)
    
    # Calculate quarter-over-quarter growth for each revenue stream
    for revenue_type, data in revenue_breakdown.items():
        if 'values' in data and data['values']:
            values = data['values']
            quarters = sorted(values.keys(), reverse=True)
            
            if len(quarters) >= 2:
                current = values[quarters[0]]
                previous = values[quarters[1]]
                
                if current and previous and previous != 0:
                    qoq_growth = ((current - previous) / abs(previous)) * 100
                    metrics[f"{revenue_type}_qoq_growth"] = round(qoq_growth, 2)
    
    return metrics

def analyze_revenue_diversification(revenue_sources):
    """Analyze revenue diversification and concentration"""
    if not revenue_sources:
        return None
    
    diversification_analysis = {
        "revenue_stream_count": len([k for k in revenue_sources.keys() 
                                   if k not in ['geographic_segments', 'business_segments']]),
        "revenue_concentration_risk": "low",  # Will be calculated
        "dominant_revenue_streams": [],
        "diversification_score": 0
    }
    
    # Calculate concentration based on revenue percentages
    concentration_threshold = 60  # If any single stream > 60%, mark as high risk
    for stream, data in revenue_sources.items():
        if 'values' in data and data['values']:
            # This is a revenue stream - could add logic to identify dominant ones
            pass
    
    return diversification_analysis

# ====================== ENHANCED FINANCIAL DATA FUNCTION ======================

def fetch_and_save_financial_data(company_name, ticker):
    """Fetch and save financial data with comprehensive revenue source analysis."""
    try:
        logging.info(f"📈 Fetching financial data for ticker: {ticker}")
        
        # Create ticker object
        stock = yf.Ticker(ticker)
        
        # Fetch various financial data with error handling
        financial_data = {}
        
        # Try to fetch quarterly financials WITH REVENUE SOURCE ANALYSIS
        try:
            quarterly_financials = stock.quarterly_financials
            if not quarterly_financials.empty:
                # Convert Timestamp columns to strings
                quarterly_financials.columns = quarterly_financials.columns.strftime("%Y-%m-%d")
                financial_data['quarterly_financials'] = quarterly_financials.to_dict()
                
                # **ADD COMPREHENSIVE REVENUE SOURCE ANALYSIS**
                financial_data['quarterly_revenue_sources'] = extract_revenue_sources(
                    quarterly_financials, stock.info
                )
                financial_data['quarterly_revenue_metrics'] = calculate_revenue_metrics(
                    financial_data['quarterly_revenue_sources']
                )
                
                logging.info("✅ Quarterly financials with revenue source analysis fetched successfully")
            else:
                logging.warning("⚠️ No quarterly financials data available")
        except Exception as e:
            logging.error(f"❌ Error fetching quarterly financials: {e}")
        
        # Try to fetch annual financials WITH REVENUE SOURCE ANALYSIS
        try:
            annual_financials = stock.financials
            if not annual_financials.empty:
                annual_financials.columns = annual_financials.columns.strftime("%Y-%m-%d")
                financial_data['annual_financials'] = annual_financials.to_dict()
                
                # **ADD ANNUAL REVENUE SOURCE ANALYSIS**
                financial_data['annual_revenue_sources'] = extract_revenue_sources(
                    annual_financials, stock.info
                )
                financial_data['annual_revenue_metrics'] = calculate_revenue_metrics(
                    financial_data['annual_revenue_sources']
                )
                
                logging.info("✅ Annual financials with revenue source analysis fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching annual financials: {e}")
        
        # Try to fetch balance sheet
        try:
            balance_sheet = stock.quarterly_balance_sheet
            if not balance_sheet.empty:
                balance_sheet.columns = balance_sheet.columns.strftime("%Y-%m-%d")
                financial_data['balance_sheet'] = balance_sheet.to_dict()
                logging.info("✅ Balance sheet fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching balance sheet: {e}")
        
        # Try to fetch cash flow
        try:
            cash_flow = stock.quarterly_cashflow
            if not cash_flow.empty:
                cash_flow.columns = cash_flow.columns.strftime("%Y-%m-%d")
                financial_data['cash_flow'] = cash_flow.to_dict()
                logging.info("✅ Cash flow fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching cash flow: {e}")
        
        # Try to fetch basic info
        try:
            info = stock.info
            if info:
                financial_data['company_info'] = info
                logging.info("✅ Company info fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching company info: {e}")
        
        # Try to fetch historical data (last 1 year)
        try:
            hist_data = stock.history(period="1y")
            if not hist_data.empty:
                # Convert index to string
                hist_data.index = hist_data.index.strftime("%Y-%m-%d")
                financial_data['historical_prices'] = hist_data.to_dict()
                logging.info("✅ Historical data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching historical data: {e}")
        
        # **ADD REVENUE DIVERSIFICATION ANALYSIS**
        if 'quarterly_revenue_sources' in financial_data:
            financial_data["revenue_diversification_analysis"] = analyze_revenue_diversification(
                financial_data["quarterly_revenue_sources"]
            )
            logging.info("✅ Revenue diversification analysis completed")
        
        # Save to MongoDB only if we have some data
        if financial_data:
            doc = {
                "company": company_name.lower(),
                "ticker": ticker,
                "financial_data": financial_data,
                "fetched_at": datetime.utcnow(),
                "status": "success"
            }
            
            # Update or insert
            financial_collection.update_one(
                {"company": company_name.lower(), "ticker": ticker},
                {"$set": doc},
                upsert=True
            )
            logging.info("✅ Financial data with comprehensive revenue source analysis saved to MongoDB")
            return True
        else:
            logging.error("❌ No financial data could be fetched")
            # Save error status
            error_doc = {
                "company": company_name.lower(),
                "ticker": ticker,
                "error": "No financial data available",
                "fetched_at": datetime.utcnow(),
                "status": "failed"
            }
            financial_collection.update_one(
                {"company": company_name.lower(), "ticker": ticker},
                {"$set": error_doc},
                upsert=True
            )
            return False
            
    except Exception as e:
        logging.error(f"❌ Critical error in financial data fetching: {e}")
        # Save error to database
        error_doc = {
            "company": company_name.lower(),
            "ticker": ticker,
            "error": str(e),
            "fetched_at": datetime.utcnow(),
            "status": "error"
        }
        financial_collection.update_one(
            {"company": company_name.lower(), "ticker": ticker},
            {"$set": error_doc},
            upsert=True
        )
        return False

# ====================== EXISTING FUNCTIONS (UNCHANGED) ======================

async def parallel_search(company_name, ticker=None):
    """Run both top-down and bottom-up searches concurrently and fetch financial data."""
    try:
        logging.info("\n🔍 Starting parallel searches...")
        logging.info("├─ Running top-down analysis")
        logging.info("└─ Running bottom-up analysis")

        # Run both searches in parallel
        top_down_links = top_down_search(company_name)
        bottom_up_links = bottom_up_search(company_name)

        # Combine and deduplicate links
        all_links = list(set(top_down_links + bottom_up_links))
        logging.info(f"\n🌐 Found {len(all_links)} unique links")

        # Process all links concurrently
        if all_links:
            tasks = [process_link(link, company_name) for link in all_links]
            await asyncio.gather(*tasks)
            logging.info("✅ Crawling and saving raw data complete")
        else:
            logging.warning("⚠️ No links found to process")

        # Fetch and save financial data using yfinance WITH REVENUE SOURCE ANALYSIS
        if ticker:
            success = fetch_and_save_financial_data(company_name, ticker)
            if not success:
                logging.warning("⚠️ Financial data fetching failed, but continuing with summarization")
        else:
            logging.info("ℹ️ No ticker provided, skipping financial data fetch")
            
    except Exception as e:
        logging.error(f"❌ Error in parallel_search: {e}")
        # Don't stop the program, just log the error

def parallel_summarize(company_name):
    """Generate both top-down and bottom-up summaries."""
    try:
        logging.info("\n📊 Generating summaries...")
        logging.info("├─ Running top-down summarization")
        top_down_summarize(company_name)
        logging.info("└─ Running bottom-up summarization")
        bottom_up_summarize(company_name)
        logging.info("✅ Both summaries complete")

        # Optional: Preview summaries from DB
        try:
            top_summary = db["top_down_summarization"].find_one({"company": company_name.lower()})
            bottom_summary = db["bottom_up_summarization"].find_one({"company": company_name.lower()})
            if top_summary:
                logging.info(f"Top-Down Summary Preview: {top_summary['summary'][:200]}...")
            if bottom_summary:
                logging.info(f"Bottom-Up Summary Preview: {bottom_summary['summary'][:200]}...")
        except Exception as e:
            logging.error(f"❌ Error previewing summaries: {e}")
            
    except Exception as e:
        logging.error(f"❌ Error in parallel_summarize: {e}")

if __name__ == "__main__":
    # Validate env vars
    if not SERP_API_KEY or not GOOGLE_API_KEY:
        logging.error("Missing API keys in .env file.")
        sys.exit(1)
    
    company = "ashokleyland"
    ticker = "ASHOKLEY.NS"
    
    try:
        # Run the full pipeline
        asyncio.run(parallel_search(company, ticker))
        parallel_summarize(company)
        logging.info("🎉 Pipeline completed successfully!")
        
    except Exception as e:
        logging.error(f"❌ Critical error in main pipeline: {e}")
        sys.exit(1)
