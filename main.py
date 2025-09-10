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

# # Load environment variables
# load_dotenv()
# SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # MongoDB connection
# client = MongoClient("mongodb://localhost:27017/")
# db = client["ravanan"]
# financial_collection = db["financial_data"]

# def fetch_and_save_financial_data(company_name, ticker):
#     """Fetch and save financial data with proper error handling."""
#     try:
#         logging.info(f"📈 Fetching financial data for ticker: {ticker}")
        
#         # Create ticker object
#         stock = yf.Ticker(ticker)
        
#         # Fetch various financial data with error handling
#         financial_data = {}
        
#         # Try to fetch quarterly financials
#         try:
#             quarterly_financials = stock.quarterly_financials
#             if not quarterly_financials.empty:
#                 # Convert Timestamp columns to strings
#                 quarterly_financials.columns = quarterly_financials.columns.strftime("%Y-%m-%d")
#                 financial_data['quarterly_financials'] = quarterly_financials.to_dict()
#                 logging.info("✅ Quarterly financials fetched successfully")
#             else:
#                 logging.warning("⚠️  No quarterly financials data available")
#         except Exception as e:
#             logging.error(f"❌ Error fetching quarterly financials: {e}")
        
#         # Try to fetch balance sheet
#         try:
#             balance_sheet = stock.quarterly_balance_sheet
#             if not balance_sheet.empty:
#                 balance_sheet.columns = balance_sheet.columns.strftime("%Y-%m-%d")
#                 financial_data['balance_sheet'] = balance_sheet.to_dict()
#                 logging.info("✅ Balance sheet fetched successfully")
#         except Exception as e:
#             logging.error(f"❌ Error fetching balance sheet: {e}")
        
#         # Try to fetch cash flow
#         try:
#             cash_flow = stock.quarterly_cashflow
#             if not cash_flow.empty:
#                 cash_flow.columns = cash_flow.columns.strftime("%Y-%m-%d")
#                 financial_data['cash_flow'] = cash_flow.to_dict()
#                 logging.info("✅ Cash flow fetched successfully")
#         except Exception as e:
#             logging.error(f"❌ Error fetching cash flow: {e}")
        
#         # Try to fetch basic info
#         try:
#             info = stock.info
#             if info:
#                 financial_data['company_info'] = info
#                 logging.info("✅ Company info fetched successfully")
#         except Exception as e:
#             logging.error(f"❌ Error fetching company info: {e}")
        
#         # Try to fetch historical data (last 1 year)
#         try:
#             hist_data = stock.history(period="1y")
#             if not hist_data.empty:
#                 # Convert index to string
#                 hist_data.index = hist_data.index.strftime("%Y-%m-%d")
#                 financial_data['historical_prices'] = hist_data.to_dict()
#                 logging.info("✅ Historical data fetched successfully")
#         except Exception as e:
#             logging.error(f"❌ Error fetching historical data: {e}")
        
#         # Save to MongoDB only if we have some data
#         if financial_data:
#             doc = {
#                 "company": company_name.lower(),
#                 "ticker": ticker,
#                 "financial_data": financial_data,
#                 "fetched_at": datetime.utcnow(),
#                 "status": "success"
#             }
            
#             # Update or insert
#             financial_collection.update_one(
#                 {"company": company_name.lower(), "ticker": ticker},
#                 {"$set": doc},
#                 upsert=True
#             )
#             logging.info("✅ Financial data saved to MongoDB")
#             return True
#         else:
#             logging.error("❌ No financial data could be fetched")
#             # Save error status
#             error_doc = {
#                 "company": company_name.lower(),
#                 "ticker": ticker,
#                 "error": "No financial data available",
#                 "fetched_at": datetime.utcnow(),
#                 "status": "failed"
#             }
#             financial_collection.update_one(
#                 {"company": company_name.lower(), "ticker": ticker},
#                 {"$set": error_doc},
#                 upsert=True
#             )
#             return False
            
#     except Exception as e:
#         logging.error(f"❌ Critical error in financial data fetching: {e}")
#         # Save error to database
#         error_doc = {
#             "company": company_name.lower(),
#             "ticker": ticker,
#             "error": str(e),
#             "fetched_at": datetime.utcnow(),
#             "status": "error"
#         }
#         financial_collection.update_one(
#             {"company": company_name.lower(), "ticker": ticker},
#             {"$set": error_doc},
#             upsert=True
#         )
#         return False

# async def parallel_search(company_name, ticker=None):
#     """Run both top-down and bottom-up searches concurrently and fetch financial data."""
#     try:
#         logging.info("\n🔍 Starting parallel searches...")
#         logging.info("├─ Running top-down analysis")
#         logging.info("└─ Running bottom-up analysis")

#         # Run both searches in parallel
#         top_down_links = top_down_search(company_name)
#         bottom_up_links = bottom_up_search(company_name)

#         # Combine and deduplicate links
#         all_links = list(set(top_down_links + bottom_up_links))
#         logging.info(f"\n🌐 Found {len(all_links)} unique links")

#         # Process all links concurrently
#         if all_links:
#             tasks = [process_link(link, company_name) for link in all_links]
#             await asyncio.gather(*tasks)
#             logging.info("✅ Crawling and saving raw data complete")
#         else:
#             logging.warning("⚠️  No links found to process")

#         # Fetch and save financial data using yfinance
#         if ticker:
#             success = fetch_and_save_financial_data(company_name, ticker)
#             if not success:
#                 logging.warning("⚠️  Financial data fetching failed, but continuing with summarization")
#         else:
#             logging.info("ℹ️  No ticker provided, skipping financial data fetch")
            
#     except Exception as e:
#         logging.error(f"❌ Error in parallel_search: {e}")
#         # Don't stop the program, just log the error

# def parallel_summarize(company_name):
#     """Generate both top-down and bottom-up summaries."""
#     try:
#         logging.info("\n📊 Generating summaries...")
#         logging.info("├─ Running top-down summarization")
#         top_down_summarize(company_name)
#         logging.info("└─ Running bottom-up summarization")
#         bottom_up_summarize(company_name)
#         logging.info("✅ Both summaries complete")

#         # Optional: Preview summaries from DB
#         try:
#             top_summary = db["top_down_summarization"].find_one({"company": company_name.lower()})
#             bottom_summary = db["bottom_up_summarization"].find_one({"company": company_name.lower()})
#             if top_summary:
#                 logging.info(f"Top-Down Summary Preview: {top_summary['summary'][:200]}...")
#             if bottom_summary:
#                 logging.info(f"Bottom-Up Summary Preview: {bottom_summary['summary'][:200]}...")
#         except Exception as e:
#             logging.error(f"❌ Error previewing summaries: {e}")
            
#     except Exception as e:
#         logging.error(f"❌ Error in parallel_summarize: {e}")

# if __name__ == "__main__":
#     # Validate env vars
#     if not SERP_API_KEY or not GOOGLE_API_KEY:
#         logging.error("Missing API keys in .env file.")
#         sys.exit(1)
    
#     company = "ashokleyland"
#     ticker = "ASHOKLEY.NS"
    
#     try:
#         # Run the full pipeline
#         asyncio.run(parallel_search(company, ticker))
#         parallel_summarize(company)
#         logging.info("🎉 Pipeline completed successfully!")
        
#     except Exception as e:
#         logging.error(f"❌ Critical error in main pipeline: {e}")
#         sys.exit(1)


def display_data_summary(company_name):
    """Display a summary of all collected data."""
    try:
        logging.info(f"\n📋 Data Collection Summary for {company_name.upper()}")
    except Exception as e:
        logging.error(f"Error displaying data summary: {e}")
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

def fetch_comprehensive_financial_data(company_name, ticker):
    """Fetch comprehensive financial data using all yfinance capabilities."""
    try:
        logging.info(f"📈 Fetching comprehensive financial data for ticker: {ticker}")
        
        # Create ticker object
        stock = yf.Ticker(ticker)
        data = {}
        
        # --- Core info ---
        logging.info("├─ Fetching core company info...")
        try:
            data["info"] = safe_to_dict(getattr(stock, "info", None))
            data["fast_info"] = safe_to_dict(getattr(stock, "fast_info", None))
            logging.info("✅ Core info fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching core info: {e}")
        
        # --- Market Data ---
        logging.info("├─ Fetching market data...")
        try:
            data["history_1y"] = safe_to_dict(stock.history(period="1y"))
            data["dividends"] = safe_to_dict(getattr(stock, "dividends", None))
            data["splits"] = safe_to_dict(getattr(stock, "splits", None))
            data["capital_gains"] = safe_to_dict(getattr(stock, "capital_gains", None))
            data["actions"] = safe_to_dict(getattr(stock, "actions", None))
            logging.info("✅ Market data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching market data: {e}")
        
        # --- Financial Statements ---
        logging.info("├─ Fetching financial statements...")
        try:
            data["balance_sheet"] = safe_to_dict(getattr(stock, "balance_sheet", None))
            data["quarterly_balance_sheet"] = safe_to_dict(getattr(stock, "quarterly_balance_sheet", None))
            data["cashflow"] = safe_to_dict(getattr(stock, "cashflow", None))
            data["quarterly_cashflow"] = safe_to_dict(getattr(stock, "quarterly_cashflow", None))
            data["financials"] = safe_to_dict(getattr(stock, "financials", None))
            data["quarterly_financials"] = safe_to_dict(getattr(stock, "quarterly_financials", None))
            logging.info("✅ Financial statements fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching financial statements: {e}")
        
        # --- Earnings ---
        logging.info("├─ Fetching earnings data...")
        try:
            data["earnings"] = safe_to_dict(getattr(stock, "earnings", None))
            data["quarterly_earnings"] = safe_to_dict(getattr(stock, "quarterly_earnings", None))
            data["earnings_dates"] = safe_to_dict(getattr(stock, "earnings_dates", None))
            logging.info("✅ Earnings data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching earnings data: {e}")
        
        # --- Analyst Data ---
        logging.info("├─ Fetching analyst data...")
        try:
            data["analyst_price_targets"] = safe_to_dict(getattr(stock, "analyst_price_targets", None))
            data["recommendations"] = safe_to_dict(getattr(stock, "recommendations", None))
            data["recommendations_summary"] = safe_to_dict(getattr(stock, "recommendations_summary", None))
            data["upgrades_downgrades"] = safe_to_dict(getattr(stock, "upgrades_downgrades", None))
            data["revenue_estimates"] = safe_to_dict(getattr(stock, "revenue_estimates", None))
            data["earnings_estimates"] = safe_to_dict(getattr(stock, "earnings_estimates", None))
            data["eps_trend"] = safe_to_dict(getattr(stock, "eps_trend", None))
            data["eps_revisions"] = safe_to_dict(getattr(stock, "eps_revisions", None))
            data["growth_estimates"] = safe_to_dict(getattr(stock, "growth_estimates", None))
            logging.info("✅ Analyst data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching analyst data: {e}")
        
        # --- Holders ---
        logging.info("├─ Fetching holder information...")
        try:
            data["major_holders"] = safe_to_dict(getattr(stock, "major_holders", None))
            data["institutional_holders"] = safe_to_dict(getattr(stock, "institutional_holders", None))
            data["mutualfund_holders"] = safe_to_dict(getattr(stock, "mutualfund_holders", None))
            data["insider_transactions"] = safe_to_dict(getattr(stock, "insider_transactions", None))
            data["insider_purchases"] = safe_to_dict(getattr(stock, "insider_purchases", None))
            data["insider_roster_holders"] = safe_to_dict(getattr(stock, "insider_roster_holders", None))
            logging.info("✅ Holder information fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching holder information: {e}")
        
        # --- ESG / Sustainability ---
        logging.info("├─ Fetching ESG/sustainability data...")
        try:
            data["sustainability"] = safe_to_dict(getattr(stock, "sustainability", None))
            logging.info("✅ ESG data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching ESG data: {e}")
        
        # --- Options ---
        logging.info("├─ Fetching options data...")
        try:
            data["options_dates"] = safe_to_dict(getattr(stock, "options", None))
            if getattr(stock, "options", None):
                option_chains = {}
                for expiry in stock.options:
                    try:
                        opt = stock.option_chain(expiry)
                        option_chains[expiry] = {
                            "calls": safe_to_dict(opt.calls),
                            "puts": safe_to_dict(opt.puts)
                        }
                    except Exception as e:
                        option_chains[expiry] = str(e)
                data["option_chains"] = option_chains
            logging.info("✅ Options data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching options data: {e}")
        
        # --- Corporate Calendar ---
        logging.info("├─ Fetching corporate calendar...")
        try:
            data["calendar"] = safe_to_dict(getattr(stock, "calendar", None))
            logging.info("✅ Corporate calendar fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching corporate calendar: {e}")
        
        # --- News ---
        logging.info("├─ Fetching news data...")
        try:
            data["news"] = safe_to_dict(getattr(stock, "news", None))
            logging.info("✅ News data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching news data: {e}")
        
        # --- ISIN / CUSIP ---
        logging.info("└─ Fetching ISIN/CUSIP...")
        try:
            data["isin"] = stock.isin
        except Exception as e:
            data["isin"] = str(e)
        
        try:
            data["cusip"] = stock.cusip
        except Exception as e:
            data["cusip"] = str(e)
        
        # Save to MongoDB with structure matching summarization expectations
        if data:
            doc = {
                "company": company_name.lower(),
                "ticker": ticker,
                "financial_data": data,  # Changed key structure to match summarization files
                "fetched_at": datetime.utcnow(),
                "status": "success",
                "data_version": "comprehensive_v2"
            }
            
            # Update or insert
            financial_collection.update_one(
                {"company": company_name.lower(), "ticker": ticker},
                {"$set": doc},
                upsert=True
            )
            
            # Also save as JSON file for backup
            filename = f"{company_name.lower()}_{ticker.replace('.', '_')}_comprehensive.json"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                logging.info(f"✅ Comprehensive financial data saved to MongoDB and {filename}")
            except Exception as e:
                logging.error(f"❌ Error saving JSON file: {e}")
                logging.info("✅ Comprehensive financial data saved to MongoDB only")
            
            return True
        else:
            logging.error("❌ No comprehensive financial data could be fetched")
            return False
            
    except Exception as e:
        logging.error(f"❌ Critical error in comprehensive financial data fetching: {e}")
        # Save error to database
        error_doc = {
            "company": company_name.lower(),
            "ticker": ticker,
            "error": str(e),
            "fetched_at": datetime.utcnow(),
            "status": "error",
            "data_version": "comprehensive_v2"
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
            success = fetch_comprehensive_financial_data(company_name, ticker)
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
    company = "Kotak Mahindra Bank"
    ticker = "KOTAKBANK.NS"  # NSE ticker for Kotak Mahindra Bank

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