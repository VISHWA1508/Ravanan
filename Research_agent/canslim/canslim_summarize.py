import logging
import os
import random
from datetime import datetime, timezone
import pandas as pd

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pymongo import MongoClient

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

# Get random Google API key
try:
    GOOGLE_API_KEY = get_random_api_key("GOOGLE_API_KEY")
    logging.info("✅ Successfully loaded random Google API key")
except Exception as e:
    logging.error(f"❌ Error loading Google API key: {e}")
    raise

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["ravanan"]
collection = db["raw_data"]
financial_collection = db["financial_data"]
summary_collection = db["canslim_summarization"]

# Gemini 2.0 Flash model with random API key
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY
)

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



# CANSLIM Summarization Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a professional growth stock analyst specializing in CANSLIM methodology analysis for '{company_name}'. "
    "Your analysis must provide a comprehensive CANSLIM investment evaluation using both market intelligence from news articles AND quantitative financial data. "
    "Structure your analysis according to the proven CANSLIM framework, integrating both short-term timing factors and long-term growth quality assessment. "
    "Use actual financial figures to calculate all ratios, growth rates, and performance metrics. Support every qualitative insight with concrete quantitative evidence where available. "
    "Focus exclusively on content directly related to {company_name} and ignore general market commentary unless it specifically impacts the target company.\n\n"
    "1. If financial data is available, calculate actual ratios and growth rates\n"
    "2. If some financial data is missing, clearly state what's available vs. missing\n"
    "3. Use available data to make reasonable inferences about missing data\n"
    "4. Always provide analysis based on what IS available rather than stating 'no data'\n"
    "5. When data is limited, focus on qualitative analysis from news articles\n\n"

    
    "**CANSLIM FRAMEWORK ANALYSIS:**\n\n"
    
    "## C - CURRENT QUARTERLY EARNINGS (Short-term Factor)\n"
    "**Methodology:** Analyze recent quarterly earnings performance, acceleration patterns, and earnings quality.\n"
    "**Analysis Requirements:**\n"
    "- **Earnings Growth Rate:** Calculate actual quarterly EPS growth using financial data (QoQ and YoY)\n"
    "- **Earnings Acceleration:** Compare recent quarters' growth rates to identify acceleration/deceleration\n"
    "- **Earnings Quality:** Analyze revenue growth vs. earnings growth, one-time items, margin trends\n"
    "- **Surprise History:** Document earnings beats/misses and guidance revisions\n"
    "- **Forward Guidance:** Evaluate management's earnings outlook and achievability\n"
    "**Key Metrics to Calculate:** EPS growth rates, earnings surprise percentage, revenue-to-earnings growth ratio, margin progression\n"
    "**Questions to Address:**\n"
    "- Are quarterly earnings accelerating compared to previous quarters?\n"
    "- What is the earnings growth rate versus the same quarter last year?\n"
    "- How does earnings growth compare to revenue growth (quality check)?\n"
    "- Are there any one-time items distorting core earnings?\n\n"
    
    "## A - ANNUAL EARNINGS GROWTH (Long-term Factor)\n"
    "**Methodology:** Evaluate sustained annual earnings growth trends and consistency over multiple years.\n"
    "**Analysis Requirements:**\n"
    "- **Annual Growth Trajectory:** Calculate annual EPS CAGR over 3-5 years using actual data\n"
    "- **Growth Consistency:** Analyze year-over-year growth stability and volatility\n"
    "- **ROE Progression:** Track return on equity trends as a quality indicator\n"
    "- **Earnings Predictability:** Assess consistency of earnings delivery versus expectations\n"
    "- **Cyclical vs. Secular Growth:** Distinguish between cyclical upturn and sustainable growth\n"
    "**Key Metrics to Calculate:** Annual EPS CAGR, ROE trends, earnings volatility, growth sustainability score\n"
    "**Questions to Address:**\n"
    "- What is the 3-5 year annual earnings growth rate?\n"
    "- How consistent has annual earnings growth been?\n"
    "- Are earnings growing due to business expansion or just cost cutting?\n"
    "- How does ROE trend support sustainable earnings growth?\n\n"
    
    "## N - NEW PRODUCTS, SERVICES, OR LEADERSHIP (Long-term Factor)\n"
    "**Methodology:** Identify and evaluate new business drivers, innovation pipeline, and leadership changes.\n"
    "**Analysis Requirements:**\n"
    "- **Innovation Pipeline:** Assess new product/service launches and revenue potential\n"
    "- **R&D Investment:** Calculate R&D spending trends and productivity metrics using financial data\n"
    "- **Leadership Changes:** Evaluate new management impact on strategy and execution\n"
    "- **Market Expansion:** Analyze entry into new markets or geographies\n"
    "- **Business Model Evolution:** Assess strategic pivots or business model improvements\n"
    "**Key Metrics to Calculate:** R&D-to-revenue ratio, new product revenue contribution, market expansion metrics\n"
    "**Questions to Address:**\n"
    "- What new products or services are driving growth?\n"
    "- How significant is R&D investment relative to revenue?\n"
    "- Has new leadership brought positive strategic changes?\n"
    "- What percentage of revenue comes from products launched in the last 2-3 years?\n\n"
    
    "## S - SUPPLY AND DEMAND (Short-term Factor)\n"
    "**Methodology:** Analyze business fundamentals and stock technical factors affecting supply-demand balance.\n"
    "**Analysis Requirements:**\n"
    "- **Business Supply-Demand:** Assess industry capacity, pricing power, inventory levels\n"
    "- **Stock Supply-Demand:** Analyze trading volume, institutional activity, float characteristics\n"
    "- **Pricing Power:** Evaluate ability to raise prices using margin analysis from financial data\n"
    "- **Market Share Dynamics:** Track market position and competitive intensity\n"
    "- **Capacity Utilization:** Assess operational efficiency and expansion needs\n"
    "**Key Metrics to Calculate:** Volume patterns, price/margin trends, market share changes, capacity utilization\n"
    "**Questions to Address:**\n"
    "- What do industry supply-demand dynamics suggest about pricing power?\n"
    "- Is the company gaining or losing market share?\n"
    "- What unusual trading volume or institutional ownership patterns are evident?\n"
    "- How tight is inventory throughout the value chain?\n\n"
    
    "## L - LEADER AND INDUSTRY (Long-term Factor)\n"
    "**Methodology:** Evaluate industry leadership position and overall industry attractiveness.\n"
    "**Analysis Requirements:**\n"
    "- **Market Leadership:** Assess market share rank and competitive positioning\n"
    "- **Industry Attractiveness:** Analyze industry growth, profit pools, and structure\n"
    "- **Competitive Advantages:** Evaluate moats, differentiation, and barriers to entry\n"
    "- **Relative Performance:** Compare financial metrics to industry peers using actual data\n"
    "- **Industry Life Cycle:** Determine industry maturity and growth trajectory\n"
    "**Key Metrics to Calculate:** Market share, relative P/E vs. industry, ROE vs. peers, revenue growth vs. industry average\n"
    "**Questions to Address:**\n"
    "- Is the company a leader in its industry by market share or innovation?\n"
    "- How attractive is the industry structure and growth outlook?\n"
    "- What sustainable competitive advantages support leadership position?\n"
    "- How does financial performance compare to industry peers?\n\n"
    
    "## I - INSTITUTIONAL SPONSORSHIP (Short-term Factor)\n"
    "**Methodology:** Analyze institutional ownership patterns and professional investor interest.\n"
    "**Analysis Requirements:**\n"
    "- **Institutional Ownership:** Track percentage and quality of institutional holders\n"
    "- **Ownership Changes:** Analyze new positions, increases, and decreases\n"
    "- **Analyst Coverage:** Evaluate sell-side research coverage and recommendations\n"
    "- **Block Trading:** Monitor large block transactions and institutional activity\n"
    "- **Index Inclusion:** Assess potential for index additions or weighting changes\n"
    "**Key Metrics to Calculate:** Institutional ownership percentage, ownership concentration, analyst coverage trends\n"
    "**Questions to Address:**\n"
    "- Is institutional ownership increasing, stable, or decreasing?\n"
    "- What quality of institutions are buying or selling?\n"
    "- How concentrated is institutional ownership?\n"
    "- What catalysts might drive increased institutional interest?\n\n"
    
    "## M - MARKET DIRECTION (Both Short and Long-term Factor)\n"
    "**Methodology:** Assess broad market trends, sector rotation, and technical patterns affecting stock performance.\n"
    "**Analysis Requirements:**\n"
    "- **Market Trend Analysis:** Evaluate broad market direction and momentum\n"
    "- **Sector Performance:** Analyze sector relative strength and rotation patterns\n"
    "- **Technical Patterns:** Assess stock chart patterns, support/resistance levels\n"
    "- **Relative Strength:** Calculate stock performance vs. market and sector benchmarks\n"
    "- **Risk Environment:** Evaluate market risk appetite and volatility conditions\n"
    "**Key Metrics to Calculate:** Relative strength ratios, beta, correlation with market/sector\n"
    "**Questions to Address:**\n"
    "- What is the direction and strength of the overall market trend?\n"
    "- How is the stock's sector performing relative to the broader market?\n"
    "- Is the stock showing relative strength or weakness versus its sector?\n"
    "- What market environment would be most favorable for this stock?\n\n"
    
    "## INTEGRATED CANSLIM ANALYSIS\n"
    "**Long-term Growth Quality (A, N, L, M):** Synthesize annual earnings growth, innovation pipeline, industry leadership, and long-term market positioning.\n"
    "**Short-term Timing Factors (C, S, I, M):** Integrate current earnings momentum, supply-demand dynamics, institutional interest, and market timing.\n"
    "**Conviction Framework:**\n"
    "- **High Conviction:** Strong alignment across both short and long-term factors\n"
    "- **Moderate Conviction:** Strong long-term factors with moderate short-term setup\n"
    "- **Trading Opportunity:** Strong short-term factors with moderate long-term prospects\n"
    "- **Avoid:** Weak alignment across both timeframes\n\n"
    
    "**FINAL DELIVERABLES:**\n"
    "1. **CANSLIM Scorecard:** Rate each factor (1-10) with supporting quantitative evidence\n"
    "2. **Investment Recommendation:** BUY/HOLD/SELL with specific entry/exit criteria\n"
    "3. **Position Sizing Guidelines:** Risk-adjusted position recommendations based on factor alignment\n"
    "4. **Key Catalysts:** Near-term events that could drive factor improvements\n"
    "5. **Risk Management Framework:** Stop-loss levels and monitoring metrics\n"
    "6. **Factor Monitoring System:** Specific metrics to track for each CANSLIM component\n\n"
    
    "Ensure every analysis point is supported by actual financial calculations, growth rates, and concrete data points from the provided financial statements and market intelligence."
    ),
    ("human",
    "Company Name: {company_name}\n\nNews Articles and Market Data:\n\n{articles}\n\n"
    "Financial Data:\n\n{financial_data}\n\n"
    "Using the comprehensive CANSLIM framework above, analyze {company_name} by:\n\n"
    "**For each CANSLIM factor (C, A, N, S, L, I, M):**\n"
    "- Calculate specific metrics using actual financial data (growth rates, ratios, trends)\n"
    "- Extract relevant insights from news articles and market intelligence\n"
    "- Provide a factor score (1-10) with detailed justification\n"
    "- Support qualitative analysis with quantitative evidence\n\n"
    "**Integrate both timeframes:**\n"
    "- Long-term factors (A, N, L, M-long): Focus on sustainable growth quality\n"
    "- Short-term factors (C, S, I, M-short): Focus on timing and momentum\n"
    "- Overall conviction level based on factor alignment\n\n"
    "**Conclude with:**\n"
    "1. **CANSLIM Scorecard** - Individual factor scores with total score\n"
    "2. **Investment Recommendation** - Clear position with rationale\n"
    "3. **Entry/Exit Strategy** - Specific price levels and timing criteria\n"
    "4. **Risk Management** - Stop-loss levels and position sizing guidelines\n"
    "5. **Monitoring Framework** - Key metrics to track for each factor\n\n"
    "Deliver a complete CANSLIM analysis that integrates financial data analysis with market intelligence for actionable investment decisions on {company_name}."
    )
])

# Create chain
chain = prompt_template | model | StrOutputParser()

def clean_company_name(name):
    return name.lower().replace(" full search", "").strip()

def chunk_text(text, max_length=3000):
    words = text.split()
    return [" ".join(words[i:i + max_length]) for i in range(0, len(words), max_length)]

def format_financial_data_for_canslim(financial_doc):
    """Format financial data specifically for CANSLIM analysis with focus on growth metrics."""
    if not financial_doc or 'financial_data_normalized' not in financial_doc:
        return "No financial data available."
    
    financial_data = financial_doc['financial_data_normalized']
    formatted_sections = []
    
    try:
        # Format Company Info with CANSLIM focus - corrected to use 'ratios' section
        if 'ratios' in financial_data and financial_data['ratios']:
            formatted_sections.append("## CANSLIM KEY METRICS")
            info = financial_data['ratios']  # Changed from 'company_info' to 'ratios'
            
            # Earnings and growth metrics (C & A factors)
            earnings_metrics = [
                ('Trailing P/E Ratio', 'pe_trailing'),     # Changed key names to match data structure
                ('Forward P/E Ratio', 'pe_forward'),
                ('PEG Ratio', 'peg_ratio'),
                ('EPS (TTM)', 'eps_ttm'),                  # Changed from 'trailingEps'
                ('Forward EPS', 'eps_forward'),
                ('Earnings Growth', 'earnings_growth'),    # Changed from 'earningsGrowth'
                ('Revenue Growth', 'revenue_growth')       # Changed from 'revenueGrowth'
            ]
            
            formatted_sections.append("\n### EARNINGS & GROWTH METRICS (C & A Factors)")
            for label, key in earnings_metrics:
                if key in info:
                    value = safe_extract_value(info[key])
                    if value is not None and value != 0:
                        if 'Growth' in label:
                            formatted_sections.append(f"**{label}**: {value:.2%}")
                        elif key in ['eps_ttm', 'eps_forward']:  # Updated key names
                            formatted_sections.append(f"**{label}**: ₹{value:.2f}")
                        else:
                            formatted_sections.append(f"**{label}**: {value:.2f}")
            
            # Profitability and quality metrics (L factor)
            quality_metrics = [
                ('Return on Equity', 'roe'),               # Changed from 'returnOnEquity'
                ('Return on Assets', 'roa'),               # Changed from 'returnOnAssets'
                ('Gross Margins', 'gross_margin'),         # Changed from 'grossMargins'
                ('Operating Margins', 'operating_margin'), # Changed from 'operatingMargins'
                ('Profit Margins', 'profit_margin'),       # Changed from 'profitMargins'
                ('EBITDA Margins', 'ebitda_margin')        # Changed from 'ebitdaMargins'
            ]
            
            formatted_sections.append("\n### PROFITABILITY & QUALITY METRICS (L Factor)")
            for label, key in quality_metrics:
                if key in info:
                    value = safe_extract_value(info[key])
                    if value is not None:
                        formatted_sections.append(f"**{label}**: {value:.2%}")
            
            # Innovation and investment metrics (N factor)
            innovation_metrics = [
                ('Market Cap', 'marketCap'),
                ('Enterprise Value', 'enterpriseValue'),
                ('Total Revenue (TTM)', 'totalRevenue'),
                ('Revenue Per Share', 'revenuePerShare'),
                ('Book Value Per Share', 'bookValue')
            ]
            
            formatted_sections.append("\n### MARKET & INNOVATION METRICS (N Factor)")
            for label, key in innovation_metrics:
                if key in info:
                    value = safe_extract_value(info[key])
                    if value is not None and value != 0:
                        if key in ['marketCap', 'enterpriseValue', 'totalRevenue']:
                            formatted_sections.append(f"**{label}**: ₹{value:,.0f}")
                        else:
                            formatted_sections.append(f"**{label}**: ₹{value:.2f}")
            
            # Financial strength metrics (S factor)
            strength_metrics = [
                ('Current Ratio', 'currentRatio'),
                ('Quick Ratio', 'quickRatio'),
                ('Debt-to-Equity', 'debt_to_equity'),      # Changed from 'debtToEquity'
                ('Total Cash', 'totalCash'),
                ('Total Debt', 'totalDebt'),
                ('Free Cash Flow', 'freeCashflow'),
                ('Operating Cash Flow', 'operatingCashflow')
            ]
            
            formatted_sections.append("\n### FINANCIAL STRENGTH METRICS (S Factor)")
            for label, key in strength_metrics:
                if key in info:
                    value = safe_extract_value(info[key])
                    if value is not None and value != 0:
                        if key in ['totalCash', 'totalDebt', 'freeCashflow', 'operatingCashflow']:
                            formatted_sections.append(f"**{label}**: ₹{value:,.0f}")
                        else:
                            formatted_sections.append(f"**{label}**: {value:.2f}")
        
        # Format Quarterly Financials with CANSLIM Growth Focus - corrected section name
        if 'quarterly' in financial_data and financial_data['quarterly']:  # Changed from 'quarterly_financials'
            formatted_sections.append("\n\n## QUARTERLY EARNINGS PROGRESSION (C Factor)")
            qf = financial_data['quarterly']  # Updated variable reference
            quarters = sorted(list(qf.keys()), reverse=True)
            
            if len(quarters) >= 2:
                formatted_sections.append(f"**Quarters Available**: {' → '.join(reversed(quarters))}")
                
                # Focus on key CANSLIM earnings metrics - using correct field names
                canslim_metrics = [
                    'revenue',           # Changed from 'Total Revenue'
                    'gross_profit',      # This might not exist, will handle gracefully
                    'operating_income',  # Changed from 'Operating Income'  
                    'net_income',        # Changed from 'Net Income'
                    'eps_basic',         # Changed from 'Basic EPS'
                    'eps_diluted',       # Changed from 'Diluted EPS'
                    'ebitda'             # This might not exist in quarterly, will handle gracefully
                ]
                
                for metric in canslim_metrics:
                    if quarters and quarters[0] in qf and metric in qf[quarters[0]]:
                        latest_value = safe_extract_value(qf[quarters[0]][metric])
                        if latest_value is not None:
                            formatted_sections.append(f"\n**{metric.replace('_', ' ').title()} Quarterly Trend:**")
                            
                            # Show quarterly progression
                            values_with_quarters = []
                            for quarter in reversed(quarters[-4:]):  # Last 4 quarters
                                if quarter in qf and metric in qf[quarter]:
                                    value = safe_extract_value(qf[quarter][metric])
                                    if value is not None:
                                        values_with_quarters.append((quarter, value))
                                        if metric in ['eps_basic', 'eps_diluted']:  # Updated field names
                                            formatted_sections.append(f"  - {quarter}: ₹{value:.2f}")
                                        else:
                                            formatted_sections.append(f"  - {quarter}: ₹{value:,.0f}")
                            
                            # Calculate CANSLIM-specific growth rates
                            if len(values_with_quarters) >= 2:
                                # Quarter-over-quarter growth (most recent)
                                current = values_with_quarters[-1][1]
                                previous = values_with_quarters[-2][1]
                                if previous != 0:
                                    qoq_growth = ((current - previous) / abs(previous)) * 100
                                    formatted_sections.append(f"  - **QoQ Growth**: {qoq_growth:.1f}%")
                                
                                # Year-over-year growth if available
                                if len(values_with_quarters) >= 4:
                                    year_ago = values_with_quarters[0][1]
                                    if year_ago != 0:
                                        yoy_growth = ((current - year_ago) / abs(year_ago)) * 100
                                        formatted_sections.append(f"  - **YoY Growth**: {yoy_growth:.1f}%")
                                        
                                        # Earnings acceleration check
                                        if len(values_with_quarters) >= 4:
                                            prev_yoy_current = values_with_quarters[-2][1]
                                            prev_yoy_year_ago = values_with_quarters[1][1] if len(values_with_quarters) > 1 else year_ago
                                            if prev_yoy_year_ago != 0:
                                                prev_yoy_growth = ((prev_yoy_current - prev_yoy_year_ago) / abs(prev_yoy_year_ago)) * 100
                                                acceleration = yoy_growth - prev_yoy_growth
                                                formatted_sections.append(f"  - **Growth Acceleration**: {acceleration:+.1f}% points")
                
                # Calculate key CANSLIM ratios
                formatted_sections.append("\n## CALCULATED CANSLIM RATIOS")
                if quarters:
                    latest_quarter = quarters[0]
                    latest_data = qf[latest_quarter]
                    
                    # Revenue quality check (revenue growth vs earnings growth)
                    revenue = safe_extract_value(latest_data.get('revenue'))      # Updated field name
                    net_income = safe_extract_value(latest_data.get('net_income')) # Updated field name
                    
                    if revenue and net_income and revenue != 0:
                        net_margin = (net_income / revenue) * 100
                        formatted_sections.append(f"**Current Net Margin**: {net_margin:.1f}%")
                        
                        # Compare margins across quarters for trend
                        if len(quarters) >= 2:
                            prev_revenue = safe_extract_value(qf[quarters[1]].get('revenue', 0))      # Updated field name
                            prev_net_income = safe_extract_value(qf[quarters[1]].get('net_income', 0)) # Updated field name
                            if prev_revenue and prev_net_income and prev_revenue != 0:
                                prev_margin = (prev_net_income / prev_revenue) * 100
                                margin_change = net_margin - prev_margin
                                formatted_sections.append(f"**Margin Change (QoQ)**: {margin_change:+.1f}% points")
        
        # Add summary sections for other data
        if 'balance_sheet' in financial_data and financial_data['balance_sheet']:
            formatted_sections.append("\n\n## BALANCE SHEET STRENGTH (S Factor)")
            formatted_sections.append("Quarterly balance sheet data available for debt analysis and financial strength assessment.")
        
        if 'cashflow' in financial_data and financial_data['cashflow']:
            formatted_sections.append("\n\n## CASH FLOW QUALITY (A & S Factors)")
            formatted_sections.append("Cash flow statements available for earnings quality and financial strength analysis.")
        
        if 'market_data' in financial_data and financial_data['market_data']:  # Updated section name
            formatted_sections.append("\n\n## PRICE PERFORMANCE DATA (M Factor)")
            formatted_sections.append("Historical price data available for relative strength and market direction analysis.")
    
    except Exception as e:
        logging.error(f"Error formatting financial data for CANSLIM analysis: {e}")
        formatted_sections.append(f"Error processing financial data: {str(e)}")
    
    return "\n".join(formatted_sections) if formatted_sections else "Financial data structure not recognized for CANSLIM analysis."

def summarize_company(company_name):
    company_key = clean_company_name(company_name)
    logging.info(f"\n🎯 Starting CANSLIM summarization for: {company_key}")

    # Fetch scraped articles
    company_articles = [doc.get("raw_content", "").strip() for doc in collection.find({"company": {"$regex": f"^{company_key}", "$options": "i"}}) if doc.get("raw_content")]

    # Fetch and format financial data for CANSLIM
    financial_doc = financial_collection.find_one({"company": company_key})
    financial_text = format_financial_data_for_canslim(financial_doc)
    
    if financial_doc:
        logging.info("✅ Successfully incorporated and formatted financial data for CANSLIM analysis")
    else:
        logging.warning("⚠️  No financial data found")

    if not company_articles:
        logging.warning(f"No articles found for {company_name}")
        if not financial_doc:
            logging.error("No data available for analysis")
            return
        # If we have financial data but no articles, we can still proceed
        company_articles = ["No news articles available for analysis."]

    articles_text = "\n\n---\n\n".join(company_articles)

    try:
        # Combine articles and financial data
        chunks = chunk_text(articles_text + "\n\n" + financial_text)
        if len(chunks) > 1:
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                logging.info(f"🧩 Processing CANSLIM chunk {idx + 1} of {len(chunks)}")
                
                # Split chunk back for proper formatting
                if "## CANSLIM KEY METRICS" in chunk:
                    # This chunk contains financial data
                    chunk_articles = articles_text
                    chunk_financial = financial_text
                else:
                    # This chunk is primarily articles
                    chunk_articles = chunk
                    chunk_financial = "See other chunks for detailed financial analysis."
                
                summary = chain.invoke({
                    "articles": chunk_articles, 
                    "financial_data": chunk_financial,
                    "company_name": company_key
                }).strip()
                chunk_summaries.append(summary)
            
            # Final CANSLIM synthesis
            final_summary = chain.invoke({
                "articles": "\n\n".join(chunk_summaries), 
                "financial_data": "See individual analyses above for integrated financial insights.",
                "company_name": company_key
            }).strip()
        else:
            final_summary = chain.invoke({
                "articles": articles_text, 
                "financial_data": financial_text,
                "company_name": company_key
            }).strip()

        # Save with CANSLIM-specific metadata
        summary_doc = {
            "company": company_key,
            "summary": final_summary,
            "analysis_type": "canslim",
            "has_financial_data": financial_doc is not None,
            "financial_data_status": "included" if financial_doc else "not_available",
            "articles_count": len([a for a in company_articles if a.strip()]),
            "canslim_factors": {
                "current_earnings": "analyzed" if financial_doc else "limited",
                "annual_earnings": "analyzed" if financial_doc else "limited", 
                "new_products": "analyzed",
                "supply_demand": "analyzed",
                "leader_industry": "analyzed",
                "institutional": "analyzed",
                "market_direction": "analyzed"
            },
            "summarized_at": datetime.now(timezone.utc)
        }
        
        summary_collection.update_one(
            {"company": company_key},
            {"$set": summary_doc},
            upsert=True
        )
        
        logging.info(f"✅ CANSLIM summary saved for {company_key}")
        logging.info(f"📈 Financial data included: {financial_doc is not None}")
        logging.info(f"🎯 CANSLIM factors analyzed: {list(summary_doc['canslim_factors'].keys())}")
        
    except Exception as e:
        logging.error(f"❌ Error in CANSLIM summarization for {company_key}: {e}")
        raise  # Re-raise to help with debugging