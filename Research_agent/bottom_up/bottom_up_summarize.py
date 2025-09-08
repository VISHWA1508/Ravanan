from pymongo import MongoClient
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime, timezone
from collections import defaultdict
import os

# Load environment variables
load_dotenv()

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["ravanan"]
collection = db["raw_data"]
summary_collection = db["bottom_up_summarization"]

# Gemini 2.0 Flash model
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Bottom-Up Summarization Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a professional financial analyst providing a comprehensive bottom-up investment analysis summary for '{company_name}' based on the latest news and data. "
    "Structure your response to align with a bottom-up segment analysis framework, conducting detailed examination of business segments and their fundamental drivers. "
    "Use the provided articles to extract relevant insights. Be specific, quote or paraphrase sources where useful, and focus only on content directly related to {company_name}. "
    "Ignore general market commentary. Present in clear, plain English using bullet points or short paragraphs under each framework section for an educated investor audience.\n\n"
    "Bottom-Up Framework Sections to Cover:\n\n"
    
    "1. **Segment Problem Analysis:**\n"
    "   - Segment Name: Identify specific business segments and their market positioning\n"
    "   - Parent Division: Analyze divisional structure and segment importance within divisions\n"
    "   - Parent Company: Evaluate segment strategic importance to overall company\n"
    "   - Industry Mapping: Position segments within industry value chains and classifications\n"
    "   - Segment Revenue: Analyze revenue scale, growth trajectory, and market penetration\n"
    "   - Compound Annual Growth Rate (CAGR): Calculate and compare segment growth rates\n"
    "   - EBITDA Contribution: Assess segment profitability and company contribution\n"
    "   - Geographic Exposure: Map segment geographic footprint and regional performance\n"
    "   - Core-Non Core Classification: Determine strategic classification and potential corporate actions\n\n"
    
    "2. **Strategic Pillar Scorecard:**\n"
    "   - Growth Potential: Evaluate sustainable growth prospects, TAM penetration, innovation pipeline\n"
    "   - Profitability: Analyze margin trends, cost structure advantages, pricing power\n"
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
    "   - Revenue Analysis: Trends, growth rates, mix breakdown, export share, pricing power\n"
    "   - Profitability Analysis: Gross, EBITDA, operating, net margins and growth trends\n"
    "   - Return Metrics: ROE, ROCE, ROIC, asset turnover, working capital efficiency\n"
    "   - Cash Flow Analysis: OCF, FCF, conversion rates, margin sustainability\n"
    "   - Cost Structure: COGS, employee costs, SG&A breakdown, operating leverage\n"
    "   - Balance Sheet Health: Leverage ratios, liquidity metrics, debt structure\n"
    "   - Investment Intensity: Capex ratios, R&D spending, depreciation trends\n\n"
    
    "5. **Valuation:**\n"
    "   - Relative Valuation: P/E, P/B, EV/EBITDA, EV/Sales, PEG ratio analysis\n"
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
    "   - Rate Hike/Liquidity Scenarios: Interest rate sensitivity, refinancing risks\n"
    "   - Commodity Price Spike Impact: Input cost vulnerabilities, hedging effectiveness\n"
    "   - Policy Shift/ESG Regulation: Compliance costs, adaptation requirements\n"
    "   - Global Recession Effects: Cyclical sensitivity, defensive positioning\n"
    "   - Currency Volatility Impacts: FX exposure, hedging strategies, competitive effects\n\n"
    
    "For each section, highlight key segment-specific metrics, trends, competitive positioning, and forward-looking catalysts. "
    "Focus on granular business unit performance rather than company-wide generalizations. "
    "If segment-specific data is insufficient, note it briefly and provide what company-level insights are available. "
    "Ensure the summary provides actionable investment insights at the segment level for portfolio allocation decisions."
    ),
    ("human",
    "Company Name: {company_name}\n\nArticles:\n\n{markdown}\n\n"
    "# Apply the bottom-up framework above to synthesize segment-level insights from the articles. For each section:\n"
    "- Conduct detailed segment analysis with supporting evidence from the data\n"
    "- Address specific questions like segment revenue distribution, ROIC by business unit, competitive moats by segment, etc.\n"
    "- Evaluate each segment's standalone attractiveness and contribution to overall company value\n"
    "- Identify segment-specific catalysts, risks, and valuation drivers\n"
    "- End with segment-level investment implications (overweight/underweight segments, sum-of-parts valuation insights)\n"
    "# Your response should be a complete, structured bottom-up analysis report for detailed segment evaluation of {company_name}."
    )
])


# Create chain
chain = prompt_template | model | StrOutputParser()

# Clean company name helper
def clean_company_name(name):
    return name.lower().replace(" full search", "").strip()

# Optional: Break large text if too long
def chunk_text(text, max_length=3000):
    words = text.split()
    chunks, current_chunk = [], []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def summarize_company(company_name):
    company_key = clean_company_name(company_name)
    company_articles = []
    for doc in collection.find({"company": {"$regex": f"^{company_key}", "$options": "i"}}):
        raw_content = doc.get("raw_content", "").strip()
        if raw_content:
            company_articles.append(raw_content)

    if not company_articles:
        print(f"No articles found for {company_name}")
        return

    combined_text = "\n\n---\n\n".join(company_articles)
    print(f"\n📊 Summarizing {len(company_articles)} articles for: {company_key}")

    try:
        if len(combined_text.split()) > 10000:
            chunks = chunk_text(combined_text, max_length=3000)
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                print(f"🧩 Processing chunk {idx + 1} of {len(chunks)}")
                summary = chain.invoke({
                    "markdown": chunk,
                    "company_name": company_key
                }).strip()
                chunk_summaries.append(summary)
            final_summary = chain.invoke({
                "markdown": "\n\n".join(chunk_summaries),
                "company_name": company_key
            }).strip()
        else:
            final_summary = chain.invoke({
                "markdown": combined_text,
                "company_name": company_key
            }).strip()

        summary_collection.insert_one({
            "company": company_key,
            "summary": final_summary,
            "summarized_at": datetime.now(timezone.utc)
        })
        print(f"✅ Summary saved for {company_key}")

    except Exception as e:
        print(f"❌ Error summarizing {company_key}: {e}")