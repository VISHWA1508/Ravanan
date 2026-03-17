import logging
import os
import random
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pymongo import MongoClient

# Setup detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Load environment variables
load_dotenv()

class TokenTracker:
    """Track token usage per API key for free tier management."""
    # Free tier limits: 15,000 tokens/min per model
    FREE_TIER_LIMIT = 15000
    RESET_INTERVAL = 60  # seconds
    
    def __init__(self):
        self.key_usage = {}  # {key_index: {tokens: int, timestamp: datetime}}
        self.request_times = {}  # Track request times for rate limiting
        
    def estimate_tokens(self, text):
        """Rough estimate of tokens based on text length (1 token ≈ 4 chars)."""
        return max(1, len(str(text)) // 4)
    
    def get_key_usage(self, key_index):
        """Get current token usage for a key."""
        if key_index not in self.key_usage:
            self.key_usage[key_index] = {"tokens": 0, "timestamp": datetime.now()}
        
        # Reset if window expired
        current_time = datetime.now()
        usage_data = self.key_usage[key_index]
        if (current_time - usage_data["timestamp"]).total_seconds() > self.RESET_INTERVAL:
            logger.info(f"🔄 Token window reset for key #{key_index + 1}")
            usage_data["tokens"] = 0
            usage_data["timestamp"] = current_time
        
        return usage_data["tokens"]
    
    def add_usage(self, key_index, tokens):
        """Add token usage for a key."""
        if key_index not in self.key_usage:
            self.key_usage[key_index] = {"tokens": 0, "timestamp": datetime.now()}
        
        self.key_usage[key_index]["tokens"] += tokens
        current_usage = self.key_usage[key_index]["tokens"]
        logger.debug(f"📊 Key #{key_index + 1} usage: {current_usage}/{self.FREE_TIER_LIMIT} tokens")
        
        # Warn if approaching limit
        if current_usage > self.FREE_TIER_LIMIT * 0.8:
            logger.warning(f"⚠️  Key #{key_index + 1} approaching limit: {current_usage}/{self.FREE_TIER_LIMIT}")
    
    def is_key_available(self, key_index):
        """Check if key is under quota."""
        return self.get_key_usage(key_index) < self.FREE_TIER_LIMIT
    
    def get_wait_time(self, key_index):
        """Calculate wait time until token window resets."""
        if key_index not in self.key_usage:
            return 0
        
        usage_data = self.key_usage[key_index]
        elapsed = (datetime.now() - usage_data["timestamp"]).total_seconds()
        wait = max(0, self.RESET_INTERVAL - elapsed)
        return wait

class APIKeyManager:
    """Manages API keys and switches when quota is exceeded."""
    def __init__(self, key_name, token_tracker=None):
        self.key_name = key_name
        self.keys = self._load_keys()
        self.current_index = random.randint(0, len(self.keys) - 1)
        self.failed_keys = set()
        self.token_tracker = token_tracker or TokenTracker()
        logger.info(f"✅ Loaded {len(self.keys)} {key_name} keys")
    
    def _load_keys(self):
        """Load all API keys from .env file."""
        key_str = os.getenv(self.key_name)
        if not key_str:
            raise ValueError(f"No {self.key_name} found in .env file")
        key_str = key_str.strip('[]')
        keys = [k.strip() for k in key_str.split(',') if k.strip()]
        if not keys:
            raise ValueError(f"No valid {self.key_name} keys found in .env file")
        return keys
    
    def get_current_key(self):
        """Get the current API key."""
        return self.keys[self.current_index]
    
    def switch_key(self):
        """Switch to the next available API key."""
        self.failed_keys.add(self.current_index)
        logger.warning(f"⚠️  Key #{self.current_index + 1} marked as failed (quota exceeded)")
        
        # Find available keys based on token usage
        available_indices = [i for i in range(len(self.keys)) 
                           if i not in self.failed_keys and self.token_tracker.is_key_available(i)]
        
        if not available_indices:
            # Try any non-failed key and wait if needed
            available_indices = [i for i in range(len(self.keys)) if i not in self.failed_keys]
            if available_indices:
                self.current_index = available_indices[0]
                wait_time = self.token_tracker.get_wait_time(self.current_index)
                if wait_time > 0:
                    logger.warning(f"⏳ All keys approaching quota. Waiting {wait_time:.1f}s for reset...")
                    time.sleep(wait_time + 2)  # Add buffer
            else:
                raise RuntimeError(f"❌ All {self.key_name} keys exhausted. Please add more keys to .env")
        else:
            self.current_index = random.choice(available_indices)
        
        logger.info(f"🔄 Switched to {self.key_name} #{self.current_index + 1}")
        return self.get_current_key()

# Initialize token tracker and API key manager
token_tracker = TokenTracker()
google_key_manager = APIKeyManager("GOOGLE_API_KEY", token_tracker)
GOOGLE_API_KEY = google_key_manager.get_current_key()
logger.info(f"✅ Successfully loaded API key manager with {len(google_key_manager.keys)} keys")
logger.info(f"📋 Free tier limit: {TokenTracker.FREE_TIER_LIMIT} tokens/minute per model")

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["ravanan"]
collection = db["raw_data"]
financial_collection = db["financial_data"]
summary_collection = db["bottom_up_summarization"]

# Gemini 2.5 Flash lite model with API key manager (quality model)
quality_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY
)

# Gemma 3 27B model for cheap chunk summaries
cheap_model = ChatGoogleGenerativeAI(
    model="gemma-3-27b-it",
    google_api_key=GOOGLE_API_KEY
)

def reinitialize_models():
    """Reinitialize LLM models with current API key."""
    global quality_model, cheap_model, GOOGLE_API_KEY
    logger.info(f"🔧 Reinitializing models with new API key...")
    quality_model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY
    )
    cheap_model = ChatGoogleGenerativeAI(
        model="gemma-3-27b-it",
        google_api_key=GOOGLE_API_KEY
    )
    logger.debug("✅ Models reinitialized")

def safe_invoke(chain, input_data, max_retries=3, min_delay=2.0):
    """Safely invoke a chain with automatic API key switching on quota errors.
    
    Args:
        chain: The LangChain chain to invoke
        input_data: Input data for the chain
        max_retries: Maximum number of retry attempts
        min_delay: Minimum delay in seconds between requests (for free tier)
    """
    global GOOGLE_API_KEY, quality_model, cheap_model, google_key_manager, token_tracker
    
    # Estimate input tokens
    estimated_input_tokens = token_tracker.estimate_tokens(str(input_data))
    logger.debug(f"📝 Estimated input tokens: ~{estimated_input_tokens}")
    
    backoff_delay = min_delay
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"🚀 Attempt {attempt + 1}/{max_retries}: Invoking chain...")
            
            # Check current key status before invoking
            current_usage = token_tracker.get_key_usage(google_key_manager.current_index)
            remaining = token_tracker.FREE_TIER_LIMIT - current_usage
            logger.debug(f"  Current key usage: {current_usage}/{token_tracker.FREE_TIER_LIMIT} | Remaining: {remaining}")
            
            # Proactive key switching at 60% quota for better load balancing
            if current_usage > token_tracker.FREE_TIER_LIMIT * 0.60:
                logger.info(f"  Proactively switching keys at {current_usage}/{token_tracker.FREE_TIER_LIMIT} tokens")
                GOOGLE_API_KEY = google_key_manager.switch_key()
                reinitialize_models()
                logger.info(f"  Switched to key #{google_key_manager.current_index + 1} for load balancing")
                wait_time = token_tracker.get_wait_time(google_key_manager.current_index)
                if wait_time > 0:
                    logger.warning(f"  Waiting {wait_time:.1f}s for quota reset...")
                    time.sleep(wait_time + 1)
            
            # Wait if approaching quota
            if current_usage > token_tracker.FREE_TIER_LIMIT * 0.75:
                wait_time = token_tracker.get_wait_time(google_key_manager.current_index)
                if wait_time > 0:
                    logger.warning(f"  Waiting {wait_time:.1f}s for quota reset...")
                    time.sleep(wait_time + 1)
            
            # Invoke with delay to respect free tier limits
            time.sleep(backoff_delay)
            result = chain.invoke(input_data)
            
            # Track token usage (estimate output as 2x input)
            estimated_output_tokens = estimated_input_tokens * 2
            token_tracker.add_usage(google_key_manager.current_index, estimated_input_tokens + estimated_output_tokens)
            
            logger.debug(f"✅ Invocation successful (estimated {estimated_input_tokens + estimated_output_tokens} tokens used)")
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            error_repr = repr(e).lower()
            
            logger.error(f"❌ Request failed on attempt {attempt + 1}: {type(e).__name__}")
            logger.debug(f"📋 Error details: {str(e)[:200]}")
            
            # Check for quota/rate limit errors
            quota_keywords = ['quota', 'exceeded', 'resource_exhausted', '429', '403', 
                            'rate limit', 'permission denied', 'max tokens', 'daily limit',
                            'out of quota']
            is_quota_error = any(keyword in error_str for keyword in quota_keywords) or 'resourceexhausted' in error_repr
            
            if is_quota_error:
                logger.warning(f"⚠️  Quota/rate limit error detected on attempt {attempt + 1}/{max_retries}")
                
                if attempt < max_retries - 1:
                    try:
                        # Switch to next key
                        GOOGLE_API_KEY = google_key_manager.switch_key()
                        reinitialize_models()
                        
                        # Exponential backoff
                        backoff_delay = min_delay * (2 ** attempt)
                        logger.info(f"⏳ Waiting {backoff_delay:.1f}s before retry (exponential backoff)...")
                        time.sleep(backoff_delay)
                        
                        logger.info(f"🔄 Retrying with new API key (attempt {attempt + 2}/{max_retries})...")
                        continue
                    except RuntimeError as key_error:
                        logger.critical(f"🚨 {key_error}")
                        raise
                else:
                    logger.critical(f"🚨 All {max_retries} API key attempts exhausted")
                    raise
            else:
                logger.debug(f"Non-quota error, raising immediately")
                raise

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


# Bottom-Up Summarization Prompt Template (same as before)
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a professional financial analyst providing a comprehensive bottom-up investment analysis summary for '{company_name}' based on the latest news, articles, and financial data. "
    "Structure your response to align with a bottom-up segment analysis framework, conducting detailed examination of business segments and their fundamental drivers. "
    "Use the provided articles AND financial data to extract relevant insights. Be specific, quote or paraphrase sources where useful, and focus only on content directly related to {company_name}. "
    "When financial data is available, use it to support your analysis with concrete numbers, ratios, and trends. "
    "Ignore general market commentary. Present in clear, plain English using bullet points or short paragraphs under each framework section for an educated investor audience.\n\n"
    "1. If financial data is available, calculate actual ratios and growth rates\n"
    "2. If some financial data is missing, clearly state what's available vs. missing\n"
    "3. Use available data to make reasonable inferences about missing data\n"
    "4. Always provide analysis based on what IS available rather than stating 'no data'\n"
    "5. When data is limited, focus on qualitative analysis from news articles\n\n"
    
    "Bottom-Up Framework Sections to Cover:\n\n"
    
    "1. **Segment Problem Analysis:**\n"
    "   - Segment Name: Identify specific business segments and their market positioning\n"
    "   - Parent Division: Analyze divisional structure and segment importance within divisions\n"
    "   - Parent Company: Evaluate segment strategic importance to overall company\n"
    "   - Industry Mapping: Position segments within industry value chains and classifications\n"
    "   - Segment Revenue: Analyze revenue scale, growth trajectory, and market penetration (use actual financial data when available)\n"
    "   - Compound Annual Growth Rate (CAGR): Calculate and compare segment growth rates using financial data\n"
    "   - EBITDA Contribution: Assess segment profitability and company contribution using actual EBITDA figures\n"
    "   - Geographic Exposure: Map segment geographic footprint and regional performance\n"
    "   - Core-Non Core Classification: Determine strategic classification and potential corporate actions\n\n"
    
    "2. **Strategic Pillar Scorecard:**\n"
    "   - Growth Potential: Evaluate sustainable growth prospects, TAM penetration, innovation pipeline\n"
    "   - Profitability: Analyze margin trends, cost structure advantages, pricing power (use actual margin data)\n"
    "   - MOAT of Differentiation: Assess competitive advantages, brand strength, IP portfolio\n"
    "   - Opportunity vs Risk: Balance upside opportunities against downside risks\n"
    "   - Strategic Synergy: Evaluate segment integration with broader company operations\n\n"
    
    "3. **Life Cycle and Disruption:**\n"
    "   - Industry Life Cycle Stage: Determine maturity stage and competitive dynamics\n"
    "   - Technology Disruption Risk: Assess vulnerability to technological change\n"
    "   - ESG Policy Shock Risk: Evaluate regulatory and policy change exposure\n"
    "   - Broad Substitution Risk: Analyze threats from alternative solutions\n"
    "   - High Innovation Impact: Assess innovation-driven opportunities and threats\n\n"
    
    "4. **Financial Analysis:**\n"
    "   - Revenue Analysis: Trends, growth rates, mix breakdown, export share, pricing power (use actual revenue figures)\n"
    "   - Profitability Analysis: Gross, EBITDA, operating, net margins and growth trends (calculate from actual data)\n"
    "   - Return Metrics: ROE, ROCE, ROIC, asset turnover, working capital efficiency (calculate where possible)\n"
    "   - Cash Flow Analysis: OCF, FCF, conversion rates, margin sustainability\n"
    "   - Cost Structure: COGS, employee costs, SG&A breakdown, operating leverage (use actual cost data)\n"
    "   - Balance Sheet Health: Leverage ratios, liquidity metrics, debt structure\n"
    "   - Investment Intensity: Capex ratios, R&D spending, depreciation trends (use actual figures)\n\n"
    
    "5. **Valuation:**\n"
    "   - Relative Valuation: P/E, P/B, EV/EBITDA, EV/Sales, PEG ratio analysis (calculate using actual data)\n"
    "   - DCF Analysis: Cash flow projections, discount rate determination, terminal value\n"
    "   - Valuation Synthesis: Multiple methodology reconciliation and value range\n\n"
    
    "6. **Strategic Intelligence Layer:**\n"
    "   - Globalization Readiness: Export potential, FX sensitivity, international capabilities\n"
    "   - Innovation Index: R&D productivity, IP strength, innovation pipeline health\n"
    "   - ESG Alignment: Environmental impact, social responsibility, governance quality\n"
    "   - Market Evolution: Changing preferences, demographic trends, digital adoption\n"
    "   - Strategic Options: M&A potential, partnerships, major initiatives\n"
    "   - Disaster/Event Trap: Vulnerability assessment, contingency planning\n\n"
    
    "7. **Stress Simulation:**\n"
    "   - Rate Hike/Liquidity Scenarios: Interest rate sensitivity, refinancing risks (use actual interest expense data)\n"
    "   - Commodity Price Spike Impact: Input cost vulnerabilities, hedging effectiveness (analyze cost structure)\n"
    "   - Policy Shift/ESG Regulation: Compliance costs, adaptation requirements\n"
    "   - Global Recession Effects: Cyclical sensitivity, defensive positioning (analyze historical performance)\n"
    "   - Currency Volatility Impacts: FX exposure, hedging strategies, competitive effects\n\n"
    
    "For each section, highlight key metrics, trends, competitive positioning, and forward-looking catalysts using BOTH qualitative insights from articles AND quantitative data from financial statements. "
    "When segment-specific financial data is not available, clearly state this limitation but provide company-level financial insights that can inform segment analysis. "
    "Calculate key financial ratios and growth rates from the provided data to support your analysis. "
    "Ensure the summary provides actionable investment insights supported by concrete financial evidence."
    ),
    ("human",
    "Company Name: {company_name}\n\nArticles:\n\n{articles}\n\n"
    "Financial Data:\n\n{financial_data}\n\n"
    "# Apply the bottom-up framework above to synthesize insights from both the articles and financial data. For each section:\n"
    "- Use actual financial figures to calculate ratios, growth rates, and trends\n"
    "- Support qualitative insights with quantitative evidence\n"
    "- Highlight data limitations where segment-level breakdowns are not available\n"
    "- Provide actionable investment recommendations based on the combined analysis\n"
    "# Your response should be a complete, structured bottom-up analysis report with integrated financial analysis for {company_name}."
    )
])

# Gemma-compatible prompt (no system message)
gemma_prompt = ChatPromptTemplate.from_messages([
    ("human", """You are a financial analyst.
Analyze the following content about {company_name} and extract 
only the most important investment-relevant insights.
Summarize in maximum 200 words. Be concise and specific.

Content:
{articles}

Financial Data:
{financial_data}

Provide a 200-word maximum investment insight summary only.""")
])

# Create chains
cheap_chain = gemma_prompt | cheap_model | StrOutputParser()
quality_chain = prompt_template | quality_model | StrOutputParser()

def clean_company_name(name):
    return name.lower().replace(" full search", "").strip()

def chunk_text(text, max_length=800):
    words = text.split()
    return [" ".join(words[i:i + max_length]) for i in range(0, len(words), max_length)]

def format_financial_data(financial_doc):
    """Format financial data for better LLM analysis with robust error handling."""
    if not financial_doc or 'financial_data_normalized' not in financial_doc:
        return "No financial data available."

    financial_data = financial_doc['financial_data_normalized']
    formatted_sections = []
    
    try:
        # Format Ratios Section (this contains the key company metrics)
        if 'ratios' in financial_data and financial_data['ratios']:
            formatted_sections.append("## COMPANY INFORMATION")
            ratios = financial_data['ratios']
            
            # Key company info to extract
            key_info = [
                ('Market Cap', 'marketCap'),
                ('Enterprise Value', 'enterpriseValue'),
                ('Trailing P/E', 'pe_trailing'),
                ('Forward P/E', 'pe_forward'),
                ('Price to Book', 'priceToBook'),
                ('Enterprise to Revenue', 'enterpriseToRevenue'),
                ('Enterprise to EBITDA', 'enterpriseToEbitda'),
                ('Profit Margins', 'profit_margin'),
                ('Operating Margins', 'operating_margin'),
                ('Return on Assets', 'roa'),
                ('Return on Equity', 'roe'),
                ('Revenue Growth', 'revenue_growth'),
                ('Earnings Growth', 'earnings_growth'),
                ('Gross Margins', 'gross_margin'),
                ('EBITDA Margins', 'ebitda_margin'),
                ('Debt to Equity', 'debt_to_equity'),
                ('EPS (TTM)', 'eps_ttm'),
                ('Beta', 'beta'),
                ('Full Time Employees', 'fullTimeEmployees')
            ]
            
            for label, key in key_info:
                if key in ratios:
                    value = safe_extract_value(ratios[key])
                    if value is not None and value != 0:
                        if key in ['marketCap', 'enterpriseValue']:
                            formatted_sections.append(f"**{label}**: ₹{value:,.0f}")
                        elif key in ['profit_margin', 'operating_margin', 'roa', 'roe', 'revenue_growth', 'earnings_growth', 'gross_margin', 'ebitda_margin']:
                            formatted_sections.append(f"**{label}**: {value:.2%}")
                        elif key in ['fullTimeEmployees']:
                            formatted_sections.append(f"**{label}**: {value:,.0f}")
                        else:
                            formatted_sections.append(f"**{label}**: {value:.2f}")
        
        # Format Quarterly Financials
        if 'quarterly' in financial_data and financial_data['quarterly']:
            formatted_sections.append("\n\n## QUARTERLY FINANCIAL STATEMENTS")
            qf = financial_data['quarterly']
            
            # Get available quarters and sort them
            quarters = sorted(list(qf.keys()), reverse=True)
            formatted_sections.append(f"Available Quarters: {', '.join(quarters)}")
            
            if quarters:
                formatted_sections.append("\n### Key Financial Metrics by Quarter:")
                
                # Key metrics to extract
                key_metrics = [
                    'revenue', 'net_income', 'operating_income', 'eps_basic', 'eps_diluted',
                    'Total Revenue', 'Operating Revenue', 'Gross Profit', 'EBITDA', 
                    'EBIT', 'Net Income', 'Basic EPS', 'Diluted EPS',
                    'Cost Of Revenue', 'Operating Expense', 'Interest Expense',
                    'Tax Provision'
                ]
                
                for metric in key_metrics:
                    # Check if metric exists in any quarter
                    metric_exists = False
                    for quarter in quarters:
                        if quarter in qf and metric in qf[quarter]:
                            value = safe_extract_value(qf[quarter][metric])
                            if value is not None:
                                metric_exists = True
                                break
                    
                    if metric_exists:
                        formatted_sections.append(f"\n**{metric}:**")
                        for quarter in quarters:
                            if quarter in qf and metric in qf[quarter]:
                                value = safe_extract_value(qf[quarter][metric])
                                if value is not None:
                                    if 'EPS' in metric or 'eps' in metric:
                                        formatted_sections.append(f"  - {quarter}: ₹{value:.2f}")
                                    else:
                                        formatted_sections.append(f"  - {quarter}: ₹{value:,.0f}")
                
                # Calculate Growth Rates
                if len(quarters) >= 2:
                    formatted_sections.append("\n\n## CALCULATED GROWTH METRICS")
                    
                    current_quarter = quarters[0]
                    previous_quarter = quarters[1]
                    
                    growth_metrics = ['revenue', 'net_income', 'Total Revenue', 'EBITDA', 'Net Income']
                    
                    for metric in growth_metrics:
                        if (current_quarter in qf and metric in qf[current_quarter] and
                            previous_quarter in qf and metric in qf[previous_quarter]):
                            
                            current_val = safe_extract_value(qf[current_quarter][metric])
                            previous_val = safe_extract_value(qf[previous_quarter][metric])
                            
                            if (current_val is not None and previous_val is not None and 
                                previous_val != 0):
                                growth = ((current_val - previous_val) / abs(previous_val)) * 100
                                formatted_sections.append(f"**{metric} QoQ Growth**: {growth:.1f}%")

        # Format Annual Data
        if 'annual' in financial_data and financial_data['annual']:
            formatted_sections.append("\n\n## ANNUAL FINANCIAL PERFORMANCE")
            af = financial_data['annual']
            
            # Get available years and sort them
            years = sorted(list(af.keys()), reverse=True)
            formatted_sections.append(f"Available Years: {', '.join(years)}")
            
            if len(years) >= 2:
                formatted_sections.append("\n### Annual Growth Analysis:")
                
                current_year = years[0]
                previous_year = years[1]
                
                annual_metrics = ['revenue', 'net_income', 'operating_income', 'eps_basic']
                
                for metric in annual_metrics:
                    if (current_year in af and metric in af[current_year] and
                        previous_year in af and metric in af[previous_year]):
                        
                        current_val = safe_extract_value(af[current_year][metric])
                        previous_val = safe_extract_value(af[previous_year][metric])
                        
                        if (current_val is not None and previous_val is not None and 
                            previous_val != 0):
                            growth = ((current_val - previous_val) / abs(previous_val)) * 100
                            formatted_sections.append(f"**{metric} YoY Growth**: {growth:.1f}%")

        # Add other sections
        if 'balance_sheet' in financial_data and financial_data['balance_sheet']:
            formatted_sections.append("\n\n## QUARTERLY BALANCE SHEET")
            formatted_sections.append("Balance sheet data available for detailed analysis.")
        
        if 'cashflow' in financial_data and financial_data['cashflow']:
            formatted_sections.append("\n\n## QUARTERLY CASH FLOW")
            formatted_sections.append("Cash flow data available for liquidity and cash generation analysis.")
        
        if 'market_data' in financial_data and financial_data['market_data']:
            formatted_sections.append("\n\n## HISTORICAL PRICE PERFORMANCE")
            formatted_sections.append("Historical market data available for trend analysis.")
        
        if 'analyst' in financial_data and financial_data['analyst']:
            formatted_sections.append("\n\n## ANALYST DATA")
            formatted_sections.append("Analyst recommendations and price targets available.")
        
        if 'holders' in financial_data and financial_data['holders']:
            formatted_sections.append("\n\n## INSTITUTIONAL HOLDERS")
            formatted_sections.append("Institutional and insider holding data available.")
    
    except Exception as e:
        logging.error(f"Error formatting financial data: {e}")
        formatted_sections.append(f"Error processing financial data: {str(e)}")
    
    return "\n".join(formatted_sections) if formatted_sections else "Financial data structure not recognized."

def summarize_company(company_name):
    company_key = clean_company_name(company_name)
    logging.info(f"\n📊 Starting bottom-up summarization for: {company_key}")

    try:
        # Fetch scraped articles with quality filtering
        all_docs = list(collection.find(
            {'company': {'$regex': f'^{company_key}', '$options': 'i'}}
        ))

        quality_articles = [
            doc.get('raw_content', '').strip()
            for doc in all_docs
            if doc.get('raw_content')
            and len(doc.get('raw_content', '')) > 500
            and len(doc.get('raw_content', '')) < 50000
            and doc.get('raw_content', '').count(' ') > 50
        ]

        company_articles = sorted(
            quality_articles,
            key=len,
            reverse=True
        )[:20]

        # Fetch and format financial data
        financial_doc = financial_collection.find_one({"company": company_key})
        financial_text = format_financial_data(financial_doc)
        
        if financial_doc:
            logging.info("✅ Successfully incorporated and formatted financial data")
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

        # Combine articles and financial data
        combined_input = f"Articles: {articles_text}\n\nFinancial Data: {financial_text}"
        
        chunks = chunk_text(combined_input)
        if len(chunks) > 1:
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                logging.info(f"🧩 Processing chunk {idx + 1} of {len(chunks)}")

                summary = safe_invoke(cheap_chain, {
                    "articles": chunk,
                    "financial_data": "See final synthesis for full financial analysis.",
                    "company_name": company_key
                }).strip()
                chunk_summaries.append(summary)
                time.sleep(10)
            
            # Final synthesis
            final_summary = safe_invoke(quality_chain, {
                "articles": "\n\n---\n\n".join(chunk_summaries), 
                "financial_data": financial_text,
                "company_name": company_key
            }).strip()
        else:
            final_summary = safe_invoke(quality_chain, {
                "articles": articles_text, 
                "financial_data": financial_text,
                "company_name": company_key
            }).strip()

        # Save with additional metadata
        summary_doc = {
            "company": company_key,
            "summary": final_summary,
            "analysis_mode": "hybrid_gemma_chunks_gemini_final",
            "chunk_model": "gemma-3-27b-it",
            "synthesis_model": "gemini-2.5-flash",
            "has_financial_data": financial_doc is not None,
            "financial_data_status": "included" if financial_doc else "not_available",
            "articles_count": len([a for a in company_articles if a.strip()]),
            "articles_used": len([a for a in company_articles if a.strip()]),
            "summarized_at": datetime.now(timezone.utc)
        }
        
        summary_collection.update_one(
            {"company": company_key},
            {"$set": summary_doc},
            upsert=True
        )
        
        logging.info(f"✅ Bottom-up summary saved for {company_key}")
        logging.info(f"📈 Financial data included: {financial_doc is not None}")
        
    except Exception as e:
        logging.error(f"❌ Error summarizing {company_key}: {e}")
        raise