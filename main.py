def display_data_summary(company_name):
    """Display a summary of all collected data."""
    try:
        logging.info(f"\n📋 Data Collection Summary for {company_name.upper()}")
    except Exception as e:
        logging.error(f"Error displaying data summary: {e}")
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
import random
 
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

def get_random_api_key(key_name):
    """Get a random API key from an array stored in .env file."""
    try:
        key_str = os.getenv(key_name)
        if not key_str:
            raise ValueError(f"No {key_name} found in .env file")
        
        # Remove brackets and split by comma
        key_str = key_str.strip('[]')
        keys = [k.strip() for k in key_str.split(',') if k.strip()]
        
        if not keys:
            raise ValueError(f"No valid {key_name} keys found in .env file")
        
        return random.choice(keys)
    except Exception as e:
        logging.error(f"❌ Error getting random API key for {key_name}: {e}")
        raise

# Get random API keys
try:
    SERP_API_KEY = get_random_api_key("SERPAPI_API_KEY")
    GOOGLE_API_KEY = get_random_api_key("GOOGLE_API_KEY")
    logging.info("✅ Successfully loaded random API keys")
except Exception as e:
    logging.error(f"❌ Error loading API keys: {e}")
    sys.exit(1)

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
                
                # *ADD COMPREHENSIVE REVENUE SOURCE ANALYSIS*
                financial_data['quarterly_revenue_sources'] = extract_revenue_sources(
                    quarterly_financials, stock.info
                )
                financial_data['quarterly_revenue_metrics'] = calculate_revenue_metrics(
                    financial_data['quarterly_revenue_sources']
                )
                
                logging.info("✅ Quarterly financials with revenue source analysis fetched successfully")
            else:
                logging.warning("⚠ No quarterly financials data available")
        except Exception as e:
            logging.error(f"❌ Error fetching quarterly financials: {e}")
        
        # Try to fetch annual financials WITH REVENUE SOURCE ANALYSIS
        try:
            annual_financials = stock.financials
            if not annual_financials.empty:
                annual_financials.columns = annual_financials.columns.strftime("%Y-%m-%d")
                financial_data['annual_financials'] = annual_financials.to_dict()
                
                # *ADD ANNUAL REVENUE SOURCE ANALYSIS*
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
        
        # *ADD REVENUE DIVERSIFICATION ANALYSIS*
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
    

async def parallel_search(company_name, ticker=None):
    """Run both top-down and bottom-up searches concurrently and fetch comprehensive financial data."""
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
            logging.warning("⚠️  No links found to process")

        # Fetch and save comprehensive financial data using yfinance
        if ticker:
            logging.info("\n💼 Starting comprehensive financial data extraction...")
            success = fetch_and_save_financial_data(company_name, ticker)
            if success:
                logging.info("🎯 Comprehensive financial data extraction completed successfully!")
            else:
                logging.warning("⚠️  Comprehensive financial data fetching failed, but continuing with summarization")
        else:
            logging.info("ℹ️  No ticker provided, skipping financial data fetch")
            
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
            financial_data = financial_collection.find_one({"company": company_name.lower()})
            
            if top_summary:
                logging.info(f"📈 Top-Down Summary Preview: {top_summary['summary'][:200]}...")
            if bottom_summary:
                logging.info(f"📊 Bottom-Up Summary Preview: {bottom_summary['summary'][:200]}...")
            if financial_data and financial_data.get('status') == 'success':
                logging.info(f"💰 Financial Data Status: Successfully stored comprehensive data")
                # Show some key metrics if available
                try:
                    info = financial_data.get('comprehensive_financial_data', {}).get('info', {})
                    if info:
                        market_cap = info.get('marketCap', 'N/A')
                        pe_ratio = info.get('trailingPE', 'N/A')
                        logging.info(f"   Market Cap: {market_cap}, P/E Ratio: {pe_ratio}")
                except:
                    pass
        except Exception as e:
            logging.error(f"❌ Error previewing summaries: {e}")
            
    except Exception as e:
        logging.error(f"❌ Error in parallel_summarize: {e}")

def display_data_summary(company_name):
    """Display a summary of all collected data."""
    try:
        logging.info(f"\n📋 Data Collection Summary for {company_name.upper()}")
        logging.info("=" * 50)
        
        # Check financial data
        financial_data = financial_collection.find_one({"company": company_name.lower()})
        if financial_data:
            status = financial_data.get('status', 'unknown')
            logging.info(f"💼 Financial Data: {status.upper()}")
            if status == 'success':
                # Updated to check the correct key name
                financial_data_content = financial_data.get('financial_data', {})
                data_keys = list(financial_data_content.keys()) if financial_data_content else []
                logging.info(f"   Data categories: {len(data_keys)}")
                if data_keys:
                    logging.info(f"   Categories: {', '.join(data_keys[:5])}{'...' if len(data_keys) > 5 else ''}")
                else:
                    logging.info("   Categories: No financial data structure found")
        else:
            logging.info("💼 Financial Data: NOT FOUND")
        
        # Check summaries
        top_summary = db["top_down_summarization"].find_one({"company": company_name.lower()})
        bottom_summary = db["bottom_up_summarization"].find_one({"company": company_name.lower()})
        
        logging.info(f"📈 Top-Down Summary: {'✅ Available' if top_summary else '❌ Not available'}")
        logging.info(f"📊 Bottom-Up Summary: {'✅ Available' if bottom_summary else '❌ Not available'}")
        
        # Check raw data
        raw_data_count = db["raw_data"].count_documents({"company": company_name.lower()})
        logging.info(f"🗃️  Raw Data Entries: {raw_data_count}")
        
        logging.info("=" * 50)
        
    except Exception as e:
        logging.error(f"❌ Error displaying data summary: {e}")

if __name__ == "__main__":
    # Validate env vars
    if not SERP_API_KEY or not GOOGLE_API_KEY:
        logging.error("Missing API keys in .env file.")
        sys.exit(1)
    
    # Company and ticker configuration
    company = "Inox Wind"
    ticker = "INOXWIND.NS"  # NSE ticker for Inox Wind

    # Alternative examples for different companies:
    # company = "infosys"
    # ticker = "INFY.NS"
    
    # company = "hcl technologies"
    # ticker = "HCLTECH.NS"
    
    try:
        logging.info(f"🚀 Starting comprehensive research pipeline for {company.upper()}")
        logging.info(f"🎯 Target ticker: {ticker}")
        
        # Run the full pipeline
        asyncio.run(parallel_search(company, ticker))
        parallel_summarize(company)
        
        # Display final summary
        display_data_summary(company)

        
        
        logging.info("🎉 Pipeline completed successfully!")
        
    except KeyboardInterrupt:
        logging.info("⏹️  Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ Critical error in main pipeline: {e}")
        sys.exit(1)