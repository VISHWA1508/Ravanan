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
summary_collection = db["top_down_summarization"]

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
            logger.debug(f"📊 Current key usage: {current_usage}/{token_tracker.FREE_TIER_LIMIT} | Remaining: {remaining}")
            
            # Proactive key switching at 60% quota for better load balancing
            if current_usage > token_tracker.FREE_TIER_LIMIT * 0.60:
                logger.info(f"🔄 Proactively switching keys at {current_usage}/{token_tracker.FREE_TIER_LIMIT} tokens")
                GOOGLE_API_KEY = google_key_manager.switch_key()
                reinitialize_models()
                logger.info(f"✅ Switched to key #{google_key_manager.current_index + 1} for load balancing")
                wait_time = token_tracker.get_wait_time(google_key_manager.current_index)
                if wait_time > 0:
                    logger.warning(f"⏳ Waiting {wait_time:.1f}s for quota reset...")
                    time.sleep(wait_time + 1)
            
            # Wait if approaching quota
            if current_usage > token_tracker.FREE_TIER_LIMIT * 0.75:
                wait_time = token_tracker.get_wait_time(google_key_manager.current_index)
                if wait_time > 0:
                    logger.warning(f"⏳ Waiting {wait_time:.1f}s for quota reset...")
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
    logger.debug(f"📦 Extracting value: {type(value).__name__}")
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



# Top-Down Summarization Prompt Template (enhanced for financial data)
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a senior financial analyst providing a comprehensive investment analysis summary for '{company_name}' based on extensive news data, market intelligence, and financial data. "
    "Your analysis must follow a rigorous top-down investment framework that addresses critical investment questions across 10 key analytical dimensions. "
    "Structure your response as a professional investment research report with clear sections, actionable insights, and evidence-based conclusions. "
    "Use the provided articles AND financial data to extract relevant data points, calculate key ratios and metrics, quote specific information where valuable, and focus exclusively on content directly related to {company_name}. "
    "When financial data is available, use actual numbers to calculate ratios, growth rates, and valuation metrics to support your analysis. "
    "Ignore general market commentary unless it specifically impacts the target company. Present findings in clear, analytical language suitable for institutional investors and portfolio managers.\n\n"
    "1. If financial data is available, calculate actual ratios and growth rates\n"
    "2. If some financial data is missing, clearly state what's available vs. missing\n"
    "3. Use available data to make reasonable inferences about missing data\n"
    "4. Always provide analysis based on what IS available rather than stating 'no data'\n"
    "5. When data is limited, focus on qualitative analysis from news articles\n\n"

    
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

def format_financial_data_for_top_down(financial_doc):
    """Format financial data specifically for top-down analysis with robust error handling."""
    if not financial_doc or 'financial_data_normalized' not in financial_doc:
        return "No financial data available."
    
    financial_data = financial_doc['financial_data_normalized']
    formatted_sections = []
    
    try:
        # Format Company Info with Valuation Focus - data is in 'ratios' section
        if 'ratios' in financial_data and financial_data['ratios']:
            formatted_sections.append("## VALUATION & MARKET METRICS")
            info = financial_data['ratios']
            
            # Valuation multiples
            valuation_metrics = [
                ('Market Cap', 'marketCap'),
                ('Enterprise Value', 'enterpriseValue'),
                ('P/E Ratio (Trailing)', 'pe_trailing'),
                ('P/E Ratio (Forward)', 'pe_forward'),
                ('Price-to-Book', 'priceToBook'),
                ('EV/Revenue', 'priceToSalesTrailing12Months'),
                ('EV/EBITDA', 'enterpriseToEbitda'),
                ('PEG Ratio', 'peg_ratio')
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
                ('Gross Margins', 'gross_margin'),
                ('Operating Margins', 'operating_margin'),
                ('Profit Margins', 'profit_margin'),
                ('EBITDA Margins', 'ebitda_margin'),
                ('Return on Assets', 'roa'),
                ('Return on Equity', 'roe')
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
                ('Debt-to-Equity', 'debt_to_equity'),
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
        
        # Format Quarterly Financials - correct key is 'quarterly'
        if 'quarterly' in financial_data and financial_data['quarterly']:
            formatted_sections.append("\n\n## QUARTERLY FINANCIAL PERFORMANCE")
            qf = financial_data['quarterly']
            quarters = sorted(list(qf.keys()), reverse=True)
            
            if len(quarters) >= 2:
                formatted_sections.append(f"**Analysis Period**: {quarters[-1]} to {quarters[0]} ({len(quarters)} quarters)")
                
                # Key financial metrics with growth analysis
                key_metrics = [
                    'revenue', 'net_income', 'operating_income', 'eps_basic', 'eps_diluted'
                ]
                
                for metric in key_metrics:
                    # Check if metric exists in the latest quarter
                    if quarters and quarters[0] in qf and metric in qf[quarters[0]]:
                        latest_value = safe_extract_value(qf[quarters[0]][metric])
                        if latest_value is not None:
                            formatted_sections.append(f"\n**{metric.replace('_', ' ').title()} Analysis:**")
                            
                            # Show values for each quarter
                            values = []
                            for quarter in quarters:
                                if quarter in qf and metric in qf[quarter]:
                                    value = safe_extract_value(qf[quarter][metric])
                                    if value is not None:
                                        values.append((quarter, value))
                                        if 'eps' in metric:
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
                
                # Calculate key ratios from quarterly data
                formatted_sections.append("\n## CALCULATED FINANCIAL RATIOS")
                if quarters:
                    latest_quarter = quarters[0]
                    latest_data = qf[latest_quarter]
                    
                    # Calculate margins using the correct field names
                    revenue = safe_extract_value(latest_data.get('revenue'))
                    net_income = safe_extract_value(latest_data.get('net_income'))
                    operating_income = safe_extract_value(latest_data.get('operating_income'))
                    
                    if revenue and revenue != 0:
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
        
        if 'market_data' in financial_data and financial_data['market_data']:
            formatted_sections.append("\n\n## STOCK PERFORMANCE DATA")
            formatted_sections.append("Historical price data available for technical and momentum analysis.")
    
    except Exception as e:
        import logging
        logging.error(f"Error formatting financial data for top-down analysis: {e}")
        formatted_sections.append(f"Error processing financial data: {str(e)}")
    
    return "\n".join(formatted_sections) if formatted_sections else "Financial data structure not recognized."

def summarize_company(company_name):
    company_key = clean_company_name(company_name)
    logging.info(f"\n📊 Starting top-down summarization for: {company_key}")

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

        # Save with metadata
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
        
        logging.info(f"✅ Top-down summary saved for {company_key}")
        logging.info(f"📈 Financial data included: {financial_doc is not None}")
        
    except Exception as e:
        logging.error(f"❌ Error summarizing {company_key}: {e}")
        raise  # Re-raise to help with debugging