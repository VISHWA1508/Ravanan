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
summary_collection = db["top_down_summarization"]

# Gemini 2.0 Flash model with random API key
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY
)

def safe_extract_value(value):
    """Safely extract numerical values from various MongoDB formats."""
    if value is None:
        return None
    
    # Handle MongoDB's $numberDouble format
    if isinstance(value, dict):
        if '$numberDouble' in value:
            try:
                return float(value['$numberDouble'])
            except (ValueError, TypeError):
                return None
        # Handle other potential MongoDB formats
        elif 'value' in value:
            return safe_extract_value(value['value'])
    
    # Handle direct numerical values
    if isinstance(value, (int, float)):
        if str(value).lower() in ['nan', 'inf', '-inf']:
            return None
        return float(value)
    
    # Handle string representations
    if isinstance(value, str):
        if value.lower() in ['nan', 'null', '', 'none']:
            return None
        try:
            return float(value)
        except ValueError:
            return None
    
    return None


# Top-Down Summarization Prompt Template (enhanced for financial data)
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a senior financial analyst providing a comprehensive investment analysis summary for '{company_name}' based on extensive news data, market intelligence, and financial data. "
    "Your analysis must follow a rigorous top-down investment framework that addresses critical investment questions across 10 key analytical dimensions. "
    "Structure your response as a professional investment research report with clear sections, actionable insights, and evidence-based conclusions. "
    "Use the provided articles AND financial data to extract relevant data points, calculate key ratios and metrics, quote specific information where valuable, and focus exclusively on content directly related to {company_name}. "
    "When financial data is available, use actual numbers to calculate ratios, growth rates, and valuation metrics to support your analysis. "
    "Ignore general market commentary unless it specifically impacts the target company. Present findings in clear, analytical language suitable for institutional investors and portfolio managers.\n\n"
    
    "**ANALYTICAL FRAMEWORK - 10 CORE DIMENSIONS:**\n\n"
    
    "## 1. COMPANY REVENUE ARCHITECTURE ANALYSIS\n"
    "**Industry Revenue Segmentation:** Analyze revenue distribution across industry verticals using actual financial data where available. Calculate revenue growth rates from quarterly data. What percentage comes from each sector? How has this mix evolved? Compare to competitors.\n"
    "**Product Portfolio Performance:** Use actual revenue figures to identify top-performing segments. Calculate quarter-over-quarter and year-over-year growth rates. Which products show strongest growth trajectories?\n"
    "**Geographic Revenue Distribution:** Break down domestic versus international revenue using available data. Calculate growth rates by geography where possible.\n\n"
    
    "## 2. INDUSTRY STRUCTURAL DYNAMICS ANALYSIS\n"
    "**Market Segmentation & Positioning:** Map industry segments and company's position. Use market cap, revenue data to assess relative positioning.\n"
    "**Supply-Demand Equilibrium:** Assess using capacity utilization data, pricing trends, and margin analysis from financial statements.\n"
    "**Total Addressable Market (TAM) Analysis:** Calculate current market share using company revenue versus total industry size. Use growth rates to project TAM expansion.\n"
    "**Industry Growth Dynamics:** Calculate actual industry CAGR using company and peer financial data. Compare company growth to industry benchmarks.\n"
    "**Performance Benchmarking:** Compare key financial ratios (ROE, ROCE, EBITDA margins, etc.) to industry averages using actual data.\n\n"
    
    "## 3. CONGLOMERATE PORTFOLIO ANALYSIS (if applicable)\n"
    "**Portfolio Balance Assessment:** Use revenue and profit contribution data to evaluate segment performance. Calculate segment-wise margins and returns where possible.\n"
    "**Segment Financial Structure Analysis:** Compare cost structures, asset utilization, and profitability across segments using actual financial data.\n\n"
    
    "## 4. DISASTER RISK & RESILIENCE ANALYSIS\n"
    "**External Disruption Vulnerability:** Assess using debt-to-equity ratios, interest coverage ratios, and cash flow stability from financial data.\n"
    "**Tax Policy Sensitivity:** Calculate effective tax rates and analyze tax expense trends from financial statements.\n"
    "**ESG Risk Assessment:** Use actual spending on ESG initiatives, compliance costs from financial data where available.\n\n"
    
    "## 5. INVESTMENT TIMING OPTIMIZATION\n"
    "**Economic Cycle Alignment:** Use cyclical metrics like working capital changes, inventory turnover from financial data.\n"
    "**Performance Momentum Indicators:** Calculate momentum metrics using quarterly growth rates, margin trends, and return patterns.\n"
    "**Valuation Timing:** Use current P/E, P/B, EV/EBITDA ratios compared to historical ranges and peer benchmarks.\n\n"
    
    "## 6. MANAGEMENT & STRATEGIC QUALITY ASSESSMENT\n"
    "**Leadership Quality:** Analyze management effectiveness using ROE, ROCE trends and capital allocation efficiency from financial data.\n"
    "**Corporate Governance:** Assess using related party transactions, auditor fees, and governance costs from financial statements.\n"
    "**Strategic Execution:** Measure using actual performance against guidance, capital deployment efficiency ratios.\n\n"
    
    "## 7. OPPORTUNITY & THREAT ASSESSMENT\n"
    "**Financial Health:** Use debt ratios, interest coverage, current ratios, and cash flow metrics from actual financial data.\n"
    "**Growth Investment:** Analyze capex trends, R&D spending, and investment intensity from financial statements.\n"
    "**Competitive Position:** Use margin analysis, market share data, and profitability metrics to assess competitive standing.\n\n"
    
    "## 8. QUANTITATIVE VALUATION FRAMEWORK\n"
    "**Core Valuation Metrics:** Calculate P/E, P/B, ROE, ROCE, EBITDA margins, EV/EBITDA using actual financial data. Compare to historical ranges and peer benchmarks.\n"
    "**Growth Analysis:** Calculate revenue, EBITDA, and profit growth rates from quarterly data. Analyze sustainability of growth trends.\n"
    "**Profitability Analysis:** Calculate gross margins, EBITDA margins, operating margins, and net margins. Analyze trends and compare to industry.\n"
    "**Return Metrics:** Calculate ROE, ROCE, ROIC using actual balance sheet and income statement data.\n"
    "**Cash Flow Analysis:** Analyze operating cash flow, free cash flow, and cash conversion metrics from financial statements.\n\n"
    
    "## 9. LONG-TERM STRATEGIC LOGIC\n"
    "**Competitive Advantages:** Use margin stability, market share data, and financial performance consistency to assess moat strength.\n"
    "**Capital Allocation:** Analyze capex efficiency, acquisition returns, dividend policy using actual financial data.\n"
    "**Innovation Investment:** Track R&D spending trends and innovation-driven revenue growth from financial statements.\n\n"
    
    "## 10. INVESTMENT DECISION SYNTHESIS\n"
    "**Risk-Adjusted Returns:** Calculate Sharpe ratios, beta, and volatility metrics using historical financial performance.\n"
    "**Valuation Assessment:** Synthesize multiple valuation approaches using actual financial metrics.\n"
    "**Investment Recommendation:** Provide clear recommendation supported by financial analysis and calculated target prices.\n\n"
    
    "**OUTPUT REQUIREMENTS:**\n"
    "- Use actual financial figures to calculate all ratios and metrics\n"
    "- Include specific percentages, growth rates, and financial data points\n"
    "- Support qualitative assessments with quantitative evidence\n"
    "- Calculate valuation multiples and compare to benchmarks\n"
    "- Provide clear investment thesis with supporting financial analysis\n\n"
    
    "Your analysis should demonstrate integration of both qualitative market intelligence and quantitative financial analysis, providing institutional-quality investment research supported by concrete financial metrics."
    ),
    ("human",
    "Company Name: {company_name}\n\nNews Articles and Market Data:\n\n{articles}\n\n"
    "Financial Data:\n\n{financial_data}\n\n"
    "Using the comprehensive 10-dimension framework above, analyze the provided information about {company_name}. "
    "For each analytical dimension:\n"
    "- Use actual financial data to calculate specific metrics, ratios, and growth rates\n"
    "- Extract and synthesize relevant insights from the articles\n"
    "- Support qualitative analysis with quantitative financial evidence\n"
    "- Address the key questions outlined in each section using both data sources\n"
    "- Calculate industry-standard financial ratios and valuation multiples\n\n"
    "Conclude with:\n"
    "1. **Executive Summary** - Key investment highlights with supporting financial metrics\n"
    "2. **Investment Recommendation** - Clear BUY/HOLD/SELL with calculated price targets and valuation rationale\n"
    "3. **Key Risk Factors** - Quantified risks with financial impact assessment\n"
    "4. **Upside Catalysts** - Potential positive drivers with financial impact estimates\n"
    "5. **Monitoring Framework** - Specific financial metrics and thresholds to track\n\n"
    "Deliver a comprehensive investment analysis report that integrates financial data analysis with market intelligence for {company_name}."
    )
])

# Create chain
chain = prompt_template | model | StrOutputParser()

def clean_company_name(name):
    return name.lower().replace(" full search", "").strip()

def chunk_text(text, max_length=3000):
    words = text.split()
    return [" ".join(words[i:i + max_length]) for i in range(0, len(words), max_length)]

def format_financial_data_for_top_down(financial_doc):
    """Format financial data specifically for top-down analysis with robust error handling."""
    if not financial_doc or 'financial_data' not in financial_doc:
        return "No financial data available."
    
    financial_data = financial_doc['financial_data']
    formatted_sections = []
    
    try:
        # Format Company Info with Valuation Focus
        if 'company_info' in financial_data and financial_data['company_info']:
            formatted_sections.append("## VALUATION & MARKET METRICS")
            info = financial_data['company_info']
            
            # Valuation multiples
            valuation_metrics = [
                ('Market Cap', 'marketCap'),
                ('Enterprise Value', 'enterpriseValue'), 
                ('P/E Ratio (Trailing)', 'trailingPE'),
                ('P/E Ratio (Forward)', 'forwardPE'),
                ('Price-to-Book', 'priceToBook'),
                ('EV/Revenue', 'enterpriseToRevenue'),
                ('EV/EBITDA', 'enterpriseToEbitda'),
                ('PEG Ratio', 'pegRatio')
            ]
            
            for label, key in valuation_metrics:
                if key in info:
                    value = safe_extract_value(info[key])
                    if value is not None and value != 0:
                        if key in ['marketCap', 'enterpriseValue']:
                            formatted_sections.append(f"**{label}**: ₹{value:,.0f}")
                        else:
                            formatted_sections.append(f"**{label}**: {value:.2f}")
            
            # Profitability metrics
            formatted_sections.append("\n## PROFITABILITY METRICS")
            profit_metrics = [
                ('Gross Margins', 'grossMargins'),
                ('Operating Margins', 'operatingMargins'),
                ('Profit Margins', 'profitMargins'),
                ('EBITDA Margins', 'ebitdaMargins'),
                ('Return on Assets', 'returnOnAssets'),
                ('Return on Equity', 'returnOnEquity')
            ]
            
            for label, key in profit_metrics:
                if key in info:
                    value = safe_extract_value(info[key])
                    if value is not None:
                        formatted_sections.append(f"**{label}**: {value:.2%}")
            
            # Financial health metrics
            formatted_sections.append("\n## FINANCIAL HEALTH METRICS")
            health_metrics = [
                ('Current Ratio', 'currentRatio'),
                ('Quick Ratio', 'quickRatio'),
                ('Debt-to-Equity', 'debtToEquity'),
                ('Total Debt', 'totalDebt'),
                ('Total Cash', 'totalCash'),
                ('Free Cash Flow', 'freeCashflow')
            ]
            
            for label, key in health_metrics:
                if key in info:
                    value = safe_extract_value(info[key])
                    if value is not None and value != 0:
                        if key in ['totalDebt', 'totalCash', 'freeCashflow']:
                            formatted_sections.append(f"**{label}**: ₹{value:,.0f}")
                        else:
                            formatted_sections.append(f"**{label}**: {value:.2f}")
        
        # Format Quarterly Financials with Growth Analysis (similar to bottom-up but focused on growth)
        if 'quarterly_financials' in financial_data and financial_data['quarterly_financials']:
            formatted_sections.append("\n\n## QUARTERLY FINANCIAL PERFORMANCE")
            qf = financial_data['quarterly_financials']
            quarters = sorted(list(qf.keys()), reverse=True)
            
            if len(quarters) >= 2:
                formatted_sections.append(f"**Analysis Period**: {quarters[-1]} to {quarters[0]} ({len(quarters)} quarters)")
                
                # Key financial metrics with growth analysis
                key_metrics = [
                    'Total Revenue', 'Gross Profit', 'EBITDA', 'Operating Income', 
                    'Net Income', 'Basic EPS', 'Cost Of Revenue', 'Operating Expense'
                ]
                
                for metric in key_metrics:
                    # Check if metric exists in the latest quarter
                    if quarters and quarters[0] in qf and metric in qf[quarters[0]]:
                        latest_value = safe_extract_value(qf[quarters[0]][metric])
                        if latest_value is not None:
                            formatted_sections.append(f"\n**{metric} Analysis:**")
                            
                            # Show values for each quarter
                            values = []
                            for quarter in quarters:
                                if quarter in qf and metric in qf[quarter]:
                                    value = safe_extract_value(qf[quarter][metric])
                                    if value is not None:
                                        values.append((quarter, value))
                                        if metric in ['Basic EPS', 'Diluted EPS']:
                                            formatted_sections.append(f"  - {quarter}: ₹{value:.2f}")
                                        else:
                                            formatted_sections.append(f"  - {quarter}: ₹{value:,.0f}")
                            
                            # Calculate growth rates
                            if len(values) >= 2:
                                latest_val = values[0][1]
                                previous_val = values[1][1]
                                if previous_val != 0:
                                    qoq_growth = ((latest_val - previous_val) / abs(previous_val)) * 100
                                    formatted_sections.append(f"  - **QoQ Growth**: {qoq_growth:.1f}%")
                                
                                if len(values) >= 4:  # YoY comparison if available
                                    year_ago_val = values[3][1] if len(values) > 3 else values[-1][1]
                                    if year_ago_val != 0:
                                        yoy_growth = ((latest_val - year_ago_val) / abs(year_ago_val)) * 100
                                        formatted_sections.append(f"  - **YoY Growth**: {yoy_growth:.1f}%")
                
                # Calculate key ratios
                formatted_sections.append("\n## CALCULATED FINANCIAL RATIOS")
                if quarters:
                    latest_quarter = quarters[0]
                    latest_data = qf[latest_quarter]
                    
                    # Calculate margins
                    revenue = safe_extract_value(latest_data.get('Total Revenue'))
                    gross_profit = safe_extract_value(latest_data.get('Gross Profit'))
                    ebitda = safe_extract_value(latest_data.get('EBITDA'))
                    operating_income = safe_extract_value(latest_data.get('Operating Income'))
                    net_income = safe_extract_value(latest_data.get('Net Income'))
                    
                    if revenue and revenue != 0:
                        if gross_profit is not None:
                            gross_margin = (gross_profit / revenue) * 100
                            formatted_sections.append(f"**Gross Margin**: {gross_margin:.1f}%")
                        
                        if ebitda is not None:
                            ebitda_margin = (ebitda / revenue) * 100
                            formatted_sections.append(f"**EBITDA Margin**: {ebitda_margin:.1f}%")
                        
                        if operating_income is not None:
                            operating_margin = (operating_income / revenue) * 100
                            formatted_sections.append(f"**Operating Margin**: {operating_margin:.1f}%")
                        
                        if net_income is not None:
                            net_margin = (net_income / revenue) * 100
                            formatted_sections.append(f"**Net Margin**: {net_margin:.1f}%")
        
        # Add other sections
        if 'balance_sheet' in financial_data and financial_data['balance_sheet']:
            formatted_sections.append("\n\n## BALANCE SHEET DATA")
            formatted_sections.append("Quarterly balance sheet data available for detailed analysis.")
        
        if 'cashflow' in financial_data and financial_data['cashflow']:
            formatted_sections.append("\n\n## CASH FLOW DATA")
            formatted_sections.append("Quarterly cash flow statements available for liquidity and cash generation analysis.")
        
        if 'history_1y' in financial_data and financial_data['history_1y']:
            formatted_sections.append("\n\n## STOCK PERFORMANCE DATA")
            formatted_sections.append("1-year historical price data available for technical and momentum analysis.")
    
    except Exception as e:
        logging.error(f"Error formatting financial data for top-down analysis: {e}")
        formatted_sections.append(f"Error processing financial data: {str(e)}")
    
    return "\n".join(formatted_sections) if formatted_sections else "Financial data structure not recognized."

def summarize_company(company_name):
    company_key = clean_company_name(company_name)
    logging.info(f"\n📊 Starting top-down summarization for: {company_key}")

    # Fetch scraped articles
    company_articles = [doc.get("raw_content", "").strip() for doc in collection.find({"company": {"$regex": f"^{company_key}", "$options": "i"}}) if doc.get("raw_content")]

    # Fetch and format financial data
    financial_doc = financial_collection.find_one({"company": company_key})
    financial_text = format_financial_data_for_top_down(financial_doc)
    
    if financial_doc:
        logging.info("✅ Successfully incorporated and formatted financial data for top-down analysis")
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
                logging.info(f"🧩 Processing chunk {idx + 1} of {len(chunks)}")
                
                # Split chunk back for proper formatting
                if "## VALUATION & MARKET METRICS" in chunk:
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
            
            # Final synthesis
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

        # Save with metadata
        summary_doc = {
            "company": company_key,
            "summary": final_summary,
            "has_financial_data": financial_doc is not None,
            "financial_data_status": "included" if financial_doc else "not_available",
            "articles_count": len([a for a in company_articles if a.strip()]),
            "summarized_at": datetime.now(timezone.utc)
        }
        
        summary_collection.update_one(
            {"company": company_key},
            {"$set": summary_doc},
            upsert=True
        )
        
        logging.info(f"✅ Top-down summary saved for {company_key}")
        logging.info(f"📈 Financial data included: {financial_doc is not None}")
        
    except Exception as e:
        logging.error(f"❌ Error summarizing {company_key}: {e}")
        raise  # Re-raise to help with debugging