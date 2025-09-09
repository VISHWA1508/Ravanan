import logging
import os
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

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["ravanan"]
collection = db["raw_data"]
financial_collection = db["financial_data"]
summary_collection = db["bottom_up_summarization"]

# Gemini 2.0 Flash model
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Bottom-Up Summarization Prompt Template (enhanced for financial data)
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a professional financial analyst providing a comprehensive bottom-up investment analysis summary for '{company_name}' based on the latest news, articles, and financial data. "
    "Structure your response to align with a bottom-up segment analysis framework, conducting detailed examination of business segments and their fundamental drivers. "
    "Use the provided articles AND financial data to extract relevant insights. Be specific, quote or paraphrase sources where useful, and focus only on content directly related to {company_name}. "
    "When financial data is available, use it to support your analysis with concrete numbers, ratios, and trends. "
    "Ignore general market commentary. Present in clear, plain English using bullet points or short paragraphs under each framework section for an educated investor audience.\n\n"
    
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

# Create chain
chain = prompt_template | model | StrOutputParser()

def clean_company_name(name):
    return name.lower().replace(" full search", "").strip()

def chunk_text(text, max_length=3000):
    words = text.split()
    return [" ".join(words[i:i + max_length]) for i in range(0, len(words), max_length)]

def format_financial_data(financial_doc):
    """Format financial data for better LLM analysis."""
    if not financial_doc or 'financial_data' not in financial_doc:
        return "No financial data available."
    
    financial_data = financial_doc['financial_data']
    formatted_sections = []
    
    # Format Quarterly Financials
    if 'quarterly_financials' in financial_data:
        formatted_sections.append("## QUARTERLY FINANCIAL STATEMENTS")
        qf = financial_data['quarterly_financials']
        
        # Get available quarters
        quarters = list(qf.keys())
        formatted_sections.append(f"Available Quarters: {', '.join(quarters)}")
        
        # Create summary table for key metrics
        if quarters:
            formatted_sections.append("\n### Key Financial Metrics by Quarter:")
            
            # Key metrics to extract
            key_metrics = [
                'Total Revenue', 'Operating Revenue', 'Gross Profit', 'EBITDA', 
                'EBIT', 'Operating Income', 'Net Income', 'Basic EPS', 'Diluted EPS',
                'Cost Of Revenue', 'Operating Expense', 'Interest Expense',
                'Tax Provision', 'Depreciation And Amortization In Income Statement'
            ]
            
            for metric in key_metrics:
                if metric in qf.get(quarters[0], {}):
                    formatted_sections.append(f"\n**{metric}:**")
                    for quarter in quarters:
                        if quarter in qf and metric in qf[quarter]:
                            value = qf[quarter][metric]
                            if isinstance(value, dict) and '$numberDouble' in value:
                                value = float(value['$numberDouble'])
                            if value and str(value) != 'NaN':
                                formatted_sections.append(f"  - {quarter}: ₹{value:,.0f}")
    
    # Format Balance Sheet
    if 'balance_sheet' in financial_data:
        formatted_sections.append("\n\n## QUARTERLY BALANCE SHEET")
        bs = financial_data['balance_sheet']
        formatted_sections.append("Balance sheet data available for analysis.")
    
    # Format Cash Flow
    if 'cash_flow' in financial_data:
        formatted_sections.append("\n\n## QUARTERLY CASH FLOW")
        cf = financial_data['cash_flow']
        formatted_sections.append("Cash flow data available for analysis.")
    
    # Format Company Info
    if 'company_info' in financial_data:
        formatted_sections.append("\n\n## COMPANY INFORMATION")
        info = financial_data['company_info']
        
        # Key company info to extract
        key_info = [
            'marketCap', 'enterpriseValue', 'trailingPE', 'forwardPE', 
            'priceToBook', 'enterpriseToRevenue', 'enterpriseToEbitda',
            'profitMargins', 'operatingMargins', 'returnOnAssets', 'returnOnEquity',
            'totalRevenue', 'grossMargins', 'ebitdaMargins', 'debtToEquity',
            'currentRatio', 'quickRatio', 'totalDebt', 'totalCash'
        ]
        
        for key in key_info:
            if key in info and info[key] is not None:
                value = info[key]
                if isinstance(value, (int, float)) and value != 0:
                    if key in ['marketCap', 'enterpriseValue', 'totalRevenue', 'totalDebt', 'totalCash']:
                        formatted_sections.append(f"**{key}**: ₹{value:,.0f}")
                    elif key in ['profitMargins', 'operatingMargins', 'returnOnAssets', 'returnOnEquity', 'grossMargins', 'ebitdaMargins']:
                        formatted_sections.append(f"**{key}**: {value:.2%}")
                    else:
                        formatted_sections.append(f"**{key}**: {value:.2f}")
    
    # Format Historical Prices Summary
    if 'historical_prices' in financial_data:
        formatted_sections.append("\n\n## HISTORICAL PRICE PERFORMANCE")
        formatted_sections.append("1-year historical price data available for trend analysis.")
    
    # Calculate Growth Rates
    if 'quarterly_financials' in financial_data:
        qf = financial_data['quarterly_financials']
        if len(quarters) >= 2:
            formatted_sections.append("\n\n## CALCULATED GROWTH METRICS")
            
            # Calculate quarter-over-quarter growth for key metrics
            current_quarter = quarters[0]
            previous_quarter = quarters[1]
            
            growth_metrics = ['Total Revenue', 'EBITDA', 'Net Income']
            
            for metric in growth_metrics:
                if (metric in qf.get(current_quarter, {}) and 
                    metric in qf.get(previous_quarter, {})):
                    
                    current_val = qf[current_quarter][metric]
                    previous_val = qf[previous_quarter][metric]
                    
                    if isinstance(current_val, dict):
                        current_val = float(current_val['$numberDouble'])
                    if isinstance(previous_val, dict):
                        previous_val = float(previous_val['$numberDouble'])
                    
                    if previous_val and previous_val != 0 and str(current_val) != 'NaN' and str(previous_val) != 'NaN':
                        growth = ((current_val - previous_val) / previous_val) * 100
                        formatted_sections.append(f"**{metric} QoQ Growth**: {growth:.1f}%")
    
    return "\n".join(formatted_sections)

def summarize_company(company_name):
    company_key = clean_company_name(company_name)
    logging.info(f"\n📊 Starting bottom-up summarization for: {company_key}")

    # Fetch scraped articles
    company_articles = [doc.get("raw_content", "").strip() for doc in collection.find({"company": {"$regex": f"^{company_key}", "$options": "i"}}) if doc.get("raw_content")]

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

    try:
        # Combine articles and financial data with appropriate sizing
        combined_input = f"Articles: {articles_text}\n\nFinancial Data: {financial_text}"
        
        chunks = chunk_text(combined_input)
        if len(chunks) > 1:
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                logging.info(f"🧩 Processing chunk {idx + 1} of {len(chunks)}")
                # Split chunk back into articles and financial data for proper formatting
                chunk_parts = chunk.split("Financial Data: ", 1)
                chunk_articles = chunk_parts[0].replace("Articles: ", "")
                chunk_financial = chunk_parts[1] if len(chunk_parts) > 1 else financial_text
                
                summary = chain.invoke({
                    "articles": chunk_articles, 
                    "financial_data": chunk_financial,
                    "company_name": company_key
                }).strip()
                chunk_summaries.append(summary)
            
            # Final synthesis
            final_summary = chain.invoke({
                "articles": "\n\n".join(chunk_summaries), 
                "financial_data": "See individual chunk analyses above for financial data details.",
                "company_name": company_key
            }).strip()
        else:
            final_summary = chain.invoke({
                "articles": articles_text, 
                "financial_data": financial_text,
                "company_name": company_key
            }).strip()

        # Save with additional metadata
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
        
        logging.info(f"✅ Bottom-up summary saved for {company_key}")
        logging.info(f"📈 Financial data included: {financial_doc is not None}")
        
    except Exception as e:
        logging.error(f"❌ Error summarizing {company_key}: {e}")
        raise  # Re-raise to help with debugging