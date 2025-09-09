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

def fetch_and_save_financial_data(company_name, ticker):
    """Fetch and save financial data with proper error handling."""
    try:
        logging.info(f"📈 Fetching financial data for ticker: {ticker}")
        
        # Create ticker object
        stock = yf.Ticker(ticker)
        
        # Fetch various financial data with error handling
        financial_data = {}
        
        # Try to fetch quarterly financials
        try:
            quarterly_financials = stock.quarterly_financials
            if not quarterly_financials.empty:
                # Convert Timestamp columns to strings
                quarterly_financials.columns = quarterly_financials.columns.strftime("%Y-%m-%d")
                financial_data['quarterly_financials'] = quarterly_financials.to_dict()
                logging.info("✅ Quarterly financials fetched successfully")
            else:
                logging.warning("⚠️  No quarterly financials data available")
        except Exception as e:
            logging.error(f"❌ Error fetching quarterly financials: {e}")
        
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
            logging.info("✅ Financial data saved to MongoDB")
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
            logging.warning("⚠️  No links found to process")

        # Fetch and save financial data using yfinance
        if ticker:
            success = fetch_and_save_financial_data(company_name, ticker)
            if not success:
                logging.warning("⚠️  Financial data fetching failed, but continuing with summarization")
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