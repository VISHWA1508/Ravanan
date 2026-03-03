import logging
import asyncio
import os
import sys
import json
import time  # Added import for time.sleep
from dotenv import load_dotenv
import yfinance as yf
from pymongo import MongoClient
from datetime import datetime, timezone
import pandas as pd
import random

def display_data_summary(company_name):
    """Display a summary of all collected data."""
    try:
        
        logging.info(f"\n📋 Data Collection Summary for {company_name.upper()}")
    except Exception as e:
        logging.error(f"Error displaying data summary: {e}")

# Import the optimized crawler
from scraping.crawling.crawl import ResourceOptimizedCrawler, process_links_batch
from Research_agent.top_down.top_down_search_links import run_search as top_down_search
from Research_agent.bottom_up.bottom_up_search import run_search as bottom_up_search
from Research_agent.canslim.canslim_search import run_search as canslim_search
from Research_agent.top_down.top_down_summarize import summarize_company as top_down_summarize
from Research_agent.bottom_up.bottom_up_summarize import summarize_company as bottom_up_summarize
from Research_agent.canslim.canslim_summarize import summarize_company as canslim_summarize
from scraping.data_collect_summarize.raw_data import save_raw_data

# Setup logging with more efficient format
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables
load_dotenv()

def get_random_api_key(key_name):
    """Get a random API key from an array stored in .env file."""
    try:
        key_str = os.getenv(key_name)
        if not key_str:
            raise ValueError(f"No {key_name} found in .env file")
        
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
# [Keep all your existing revenue analysis functions unchanged]

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

def safe_extract_value(value):
    """Enhanced value extraction with better error handling."""
    if value is None:
        return None
    
    # Handle MongoDB formats
    if isinstance(value, dict):
        if '$numberDouble' in value:
            try:
                val = value['$numberDouble']
                if val == "NaN" or val == "Infinity" or val == "-Infinity":
                    return None
                return float(val)
            except (ValueError, TypeError):
                return None
        elif 'value' in value:
            return safe_extract_value(value['value'])
        elif len(value) == 1:
            return safe_extract_value(list(value.values())[0])
    
    # Handle lists - take first valid value
    if isinstance(value, list) and value:
        for v in value:
            result = safe_extract_value(v)
            if result is not None:
                return result
        return None
    
    # Handle numeric values
    if isinstance(value, (int, float)):
        if str(value).lower() in ['nan', 'inf', '-inf'] or value != value:  # NaN check
            return None
        return float(value)
    
    # Handle strings
    if isinstance(value, str):
        if value.lower() in ['nan', 'null', '', 'none', 'infinity', '-infinity']:
            return None
        try:
            # Remove commas and convert
            cleaned = value.replace(',', '').strip()
            return float(cleaned)
        except ValueError:
            return None
    
    return None



# [Keep all your existing revenue analysis functions - extract_revenue_sources, etc.]
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

def perform_comprehensive_revenue_analysis(yfinance_data, financial_data):
    """Perform comprehensive revenue analysis on all available data."""
    analysis = {
        "revenue_streams": {},
        "financial_metrics": {},
        "growth_analysis": {},
        "profitability_analysis": {},
        "segment_analysis": {}
    }
    
    try:
        # Analyze quarterly financials if available
        if yfinance_data.get("quarterly_financials"):
            qf = yfinance_data["quarterly_financials"]
            if qf:
                analysis["revenue_streams"] = extract_revenue_sources(None, yfinance_data.get("info"))
                analysis["financial_metrics"] = calculate_revenue_metrics(analysis["revenue_streams"])
        
        # Analyze company info for business segments
        if yfinance_data.get("info"):
            info = yfinance_data["info"]
            analysis["segment_analysis"] = {
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "business_summary": info.get("longBusinessSummary"),
                "full_time_employees": info.get("fullTimeEmployees"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "revenue_per_employee": info.get("revenuePerShare") if info.get("fullTimeEmployees") else None
            }
        
        # Growth analysis from earnings data
        if yfinance_data.get("quarterly_earnings"):
            earnings = yfinance_data["quarterly_earnings"]
            analysis["growth_analysis"] = {
                "earnings_available": bool(earnings),
                "earnings_trend": "analyzing" if earnings else "no_data"
            }
        
        # Profitability metrics
        if yfinance_data.get("info"):
            info = yfinance_data["info"]
            analysis["profitability_analysis"] = {
                "profit_margins": info.get("profitMargins"),
                "operating_margins": info.get("operatingMargins"),
                "return_on_assets": info.get("returnOnAssets"),
                "return_on_equity": info.get("returnOnEquity"),
                "gross_margins": info.get("grossMargins"),
                "ebitda_margins": info.get("ebitdaMargins")
            }
    
    except Exception as e:
        analysis["error"] = str(e)
        logging.warning(f"⚠️ Revenue analysis error: {e}")
    
    return analysis

# ====================== Normalized Financial Data Function ======================
# [Keep all the raw financial data unchange just normalized for easy access for all summarizers]

def normalize_financial_data(raw_data: dict) -> dict:
    """
    Normalize yfinance raw financial data into a clean schema 
    while keeping ALL raw fields available.
    """
    normalized = {
        "annual": {},
        "quarterly": {},
        "ratios": {},
        "cashflow": {},
        "balance_sheet": {},
        "earnings": {},
        "market_data": {},
        "analyst": {},
        "holders": {},
        "esg": {},
        "other": {}
    }

    try:
        # --- Annual Income Statement ---
        if raw_data.get("income_statement"):
            for period, metrics in raw_data["income_statement"].items():
                normalized["annual"][period] = {
                    "revenue": safe_extract_value(metrics.get("Total Revenue")),
                    "net_income": safe_extract_value(metrics.get("Net Income")),
                    "operating_income": safe_extract_value(metrics.get("Operating Income")),
                    "eps_basic": safe_extract_value(metrics.get("Basic EPS")),
                    "eps_diluted": safe_extract_value(metrics.get("Diluted EPS")),
                    **{k: safe_extract_value(v) for k, v in metrics.items()}  # keep everything
                }

        # --- Quarterly Income Statement ---
        if raw_data.get("quarterly_income_statement"):
            for period, metrics in raw_data["quarterly_income_statement"].items():
                normalized["quarterly"][period] = {
                    "revenue": safe_extract_value(metrics.get("Total Revenue")),
                    "net_income": safe_extract_value(metrics.get("Net Income")),
                    "operating_income": safe_extract_value(metrics.get("Operating Income")),
                    "eps_basic": safe_extract_value(metrics.get("Basic EPS")),
                    "eps_diluted": safe_extract_value(metrics.get("Diluted EPS")),
                    **{k: safe_extract_value(v) for k, v in metrics.items()}
                }

        # --- Ratios from info ---
        if raw_data.get("info"):
            info = raw_data["info"]
            normalized["ratios"] = {
                "pe_trailing": safe_extract_value(info.get("trailingPE")),
                "pe_forward": safe_extract_value(info.get("forwardPE")),
                "peg_ratio": safe_extract_value(info.get("pegRatio")),
                "roe": safe_extract_value(info.get("returnOnEquity")),
                "roa": safe_extract_value(info.get("returnOnAssets")),
                "debt_to_equity": safe_extract_value(info.get("debtToEquity")),
                "profit_margin": safe_extract_value(info.get("profitMargins")),
                "operating_margin": safe_extract_value(info.get("operatingMargins")),
                "gross_margin": safe_extract_value(info.get("grossMargins")),
                "ebitda_margin": safe_extract_value(info.get("ebitdaMargins")),
                "eps_ttm": safe_extract_value(info.get("trailingEps")),
                "eps_forward": safe_extract_value(info.get("forwardEps")),
                "revenue_growth": safe_extract_value(info.get("revenueGrowth")),
                "earnings_growth": safe_extract_value(info.get("earningsGrowth")),
                **{k: safe_extract_value(v) for k, v in info.items()}
            }

        # --- Balance Sheet ---
        if raw_data.get("quarterly_balance_sheet"):
            for period, metrics in raw_data["quarterly_balance_sheet"].items():
                normalized["balance_sheet"][period] = {
                    "total_assets": safe_extract_value(metrics.get("Total Assets")),
                    "total_liabilities": safe_extract_value(metrics.get("Total Liabilities Net Minority Interest")),
                    "total_equity": safe_extract_value(metrics.get("Ordinary Shares Number")),
                    "cash": safe_extract_value(metrics.get("Cash And Cash Equivalents")),
                    "debt": safe_extract_value(metrics.get("Total Debt")),
                    **{k: safe_extract_value(v) for k, v in metrics.items()}
                }

        # --- Cash Flow ---
        if raw_data.get("quarterly_cashflow"):
            for period, metrics in raw_data["quarterly_cashflow"].items():
                normalized["cashflow"][period] = {
                    "operating_cashflow": safe_extract_value(metrics.get("Operating Cash Flow")),
                    "free_cashflow": safe_extract_value(metrics.get("Free Cash Flow")),
                    "capex": safe_extract_value(metrics.get("Capital Expenditure")),
                    **{k: safe_extract_value(v) for k, v in metrics.items()}
                }

        # --- Earnings Dates & Estimates ---
        normalized["earnings"] = {
            "earnings_dates": raw_data.get("earnings_dates"),
            "earnings_estimates": raw_data.get("earnings_estimates"),
            "revenue_estimates": raw_data.get("revenue_estimates"),
            "eps_trend": raw_data.get("eps_trend"),
            "eps_revisions": raw_data.get("eps_revisions"),
            "growth_estimates": raw_data.get("growth_estimates"),
        }

        # --- Market Data ---
        normalized["market_data"] = {
            "dividends": raw_data.get("dividends"),
            "splits": raw_data.get("splits"),
            "actions": raw_data.get("actions"),
            "history_1y": raw_data.get("history_1y"),
        }

        # --- Analyst Data ---
        normalized["analyst"] = {
            "price_targets": raw_data.get("analyst_price_targets"),
            "recommendations": raw_data.get("recommendations"),
            "recommendations_summary": raw_data.get("recommendations_summary"),
            "upgrades_downgrades": raw_data.get("upgrades_downgrades"),
        }

        # --- Holders ---
        normalized["holders"] = {
            "major_holders": raw_data.get("major_holders"),
            "institutional_holders": raw_data.get("institutional_holders"),
            "mutualfund_holders": raw_data.get("mutualfund_holders"),
            "insider_transactions": raw_data.get("insider_transactions"),
            "insider_purchases": raw_data.get("insider_purchases"),
            "insider_roster_holders": raw_data.get("insider_roster_holders"),
        }

        # --- ESG ---
        normalized["esg"] = raw_data.get("sustainability")

        # --- Everything else ---
        normalized["other"] = {
            k: v for k, v in raw_data.items()
            if k not in normalized
        }

    except Exception as e:
        logging.error(f"❌ Error normalizing financial data: {e}")
        normalized["error"] = str(e)

    return normalized


# ====================== ENHANCED FINANCIAL DATA FUNCTION ======================
# [Keep your existing fetch_and_save_financial_data function unchanged]

def fetch_and_save_financial_data(company_name, ticker):
    """Fetch and save financial data with comprehensive revenue source analysis."""
    try:
        logging.info(f"📈 Fetching financial data for ticker: {ticker}")
        
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
            # Annual income statement
            income_stmt = getattr(stock, "income_stmt", None)
            if income_stmt is not None:
                data["income_statement"] = safe_to_dict(income_stmt)
                # Optional: extract Net Income separately
                if "Net Income" in income_stmt.index:
                    data["net_income"] = safe_to_dict(income_stmt.loc["Net Income"])
            else:
                logging.warning("⚠️ Income statement not available")

            # Quarterly income statement
            quarterly_income = getattr(stock, "quarterly_income_stmt", None)
            if quarterly_income is not None:
                data["quarterly_income_statement"] = safe_to_dict(quarterly_income)
                # Optional: extract quarterly Net Income
                if "Net Income" in quarterly_income.index:
                    data["quarterly_net_income"] = safe_to_dict(quarterly_income.loc["Net Income"])
            else:
                logging.warning("⚠️ Quarterly income statement not available")

            # Earnings dates can still be stored if available
            data["earnings_dates"] = safe_to_dict(getattr(stock, "earnings_dates", None))

            logging.info("✅ Earnings data fetched successfully")
        except Exception as e:
            logging.error(f"❌ Error fetching earnings / income statement: {e}")

        
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
            logging.error(f"❌ Error fetching annual financials: {e}")
            
        # After you populate `data` with all yfinance info
        financial_data = data  # <-- merge everything

        # Build normalized version
        normalized_data = normalize_financial_data(financial_data)

        
        # Save to MongoDB only if we have some data
        if financial_data:
            doc = {
                "company": company_name.lower(),
                "ticker": ticker,
                "financial_data_raw": financial_data,
                "financial_data_normalized": normalized_data,
                "fetched_at": datetime.now(timezone.utc),
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

# ====================== OPTIMIZED PIPELINE FUNCTIONS ======================

async def optimized_search_and_crawl(company_name, ticker=None, max_concurrent_crawls=2):
    """
    Optimized version that runs searches sequentially but crawls with controlled concurrency.
    This reduces system load significantly.
    """
    try:
        logging.info(f"\n🔍 Starting optimized search pipeline for {company_name}...")
        
        # Step 1: Run searches sequentially (not parallel) to reduce API load
        logging.info("├─ Running top-down search...")
        top_down_links = top_down_search(company_name)
        await asyncio.sleep(1)  # Brief pause between searches
        
        logging.info("├─ Running bottom-up search...")
        bottom_up_links = bottom_up_search(company_name)
        await asyncio.sleep(1)
        
        logging.info("└─ Running CANSLIM search...")
        canslim_links = canslim_search(company_name)
        
        # Step 2: Combine and deduplicate links
        all_links = list(set(top_down_links + bottom_up_links + canslim_links))
        logging.info(f"\n🌐 Found {len(all_links)} unique links to process")
        
        # Step 3: Process links with optimized crawler (controlled concurrency)
        if all_links:
            url_company_pairs = [(link, company_name) for link in all_links]
            
            # Use optimized batch processing with low concurrency
            results = await process_links_batch(
                url_company_pairs, 
                max_concurrent=max_concurrent_crawls
            )
            
            logging.info(f"✅ Crawling Results:")
            logging.info(f"   📊 Successful: {results['successful']}")
            logging.info(f"   ❌ Failed: {results['failed']}")
            logging.info(f"   📈 Success Rate: {results['success_rate']:.1%}")
            logging.info(f"   ⏱️ Total Time: {results['elapsed_time']:.1f}s")
        else:
            logging.warning("⚠️ No links found to process")
        
        # Step 4: Fetch financial data (run separately to avoid resource conflicts)
        if ticker:
            logging.info(f"\n💼 Fetching financial data for {ticker}...")
            await asyncio.sleep(2)  # Give system time to cool down
            
            # Run financial data fetch in executor to prevent blocking
            success = await asyncio.get_event_loop().run_in_executor(
                None, fetch_and_save_financial_data, company_name, ticker
            )
            
            if success:
                logging.info("🎯 Financial data extraction completed successfully!")
            else:
                logging.warning("⚠️ Financial data fetching failed, but continuing...")
        else:
            logging.info("ℹ️ No ticker provided, skipping financial data fetch")
            
    except Exception as e:
        logging.error(f"❌ Error in optimized search and crawl: {e}")
        # Don't stop the program, just log the error

def sequential_summarize(company_name):
    """
    Sequential summarization to prevent resource conflicts.
    Runs one summarization at a time with pauses.
    """
    try:
        logging.info(f"\n📊 Starting sequential summarization for {company_name}...")
        
        # Run summarizations one by one with breaks
        logging.info("├─ Running top-down summarization...")
        top_down_summarize(company_name)
        time.sleep(2)  # Give system time between operations (using time.sleep instead of await)
        
        logging.info("├─ Running bottom-up summarization...")
        bottom_up_summarize(company_name)
        time.sleep(2)  # Using time.sleep for synchronous delay
        
        logging.info("└─ Running CANSLIM summarization...")
        canslim_summarize(company_name)
        
        logging.info("✅ All summarizations completed successfully")
        
        # Preview results
        try:
            collections = [
                ("top_down_summarization", "Top-Down"),
                ("bottom_up_summarization", "Bottom-Up"),
                ("canslim_summarization", "CANSLIM")
            ]
            
            for collection_name, analysis_type in collections:
                summary = db[collection_name].find_one({"company": company_name.lower()})
                if summary:
                    logging.info(f"✅ {analysis_type} Summary: Generated successfully")
                else:
                    logging.warning(f"⚠️ {analysis_type} Summary: Not found in database")
                    
        except Exception as e:
            logging.error(f"❌ Error checking summary results: {e}")
            
    except Exception as e:
        logging.error(f"❌ Error in sequential summarization: {e}")

# ====================== RESOURCE MONITORING ======================

def check_system_resources():
    """Basic resource monitoring (optional - requires psutil)"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        logging.info(f"🖥️ System Status:")
        logging.info(f"   CPU: {cpu_percent:.1f}%")
        logging.info(f"   Memory: {memory.percent:.1f}% used")
        
        # Warn if resources are high
        if cpu_percent > 80:
            logging.warning("⚠️ High CPU usage detected - consider reducing concurrency")
        if memory.percent > 85:
            logging.warning("⚠️ High memory usage detected - system may be under stress")
            
    except ImportError:
        logging.info("💡 Install psutil for system resource monitoring: pip install psutil")
    except Exception as e:
        logging.error(f"❌ Error checking system resources: {e}")

# ====================== MAIN EXECUTION ======================

if __name__ == "__main__":
    # Validate env vars
    if not SERP_API_KEY or not GOOGLE_API_KEY:
        logging.error("Missing API keys in .env file.")
        sys.exit(1)
    
    # Company and ticker configuration
    company = "TCS"
    ticker = "TCS.NS"

    # Resource-friendly settings
    MAX_CONCURRENT_CRAWLS = 2  # Very conservative - adjust based on your system
    
    try:
        logging.info("🚀 Starting optimized research pipeline...")
        
        # Optional: Check system resources
        check_system_resources()
        
        # Step 1: Optimized search and crawl
        asyncio.run(optimized_search_and_crawl(
            company, 
            ticker, 
            max_concurrent_crawls=MAX_CONCURRENT_CRAWLS
        ))
        
        # Step 2: Wait a bit before summarization
        logging.info("⏸️ Pausing briefly before summarization...")
        time.sleep(3)  # Using time.sleep instead of asyncio.sleep
        
        # Step 3: Sequential summarization
        sequential_summarize(company)
        
        # Step 4: Display final summary
        display_data_summary(company)
        
        logging.info("🎉 Optimized pipeline completed successfully!")
        
        # Final resource check
        check_system_resources()
        
    except KeyboardInterrupt:
        logging.info("🛑 Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ Critical error in main pipeline: {e}")
        sys.exit(1)