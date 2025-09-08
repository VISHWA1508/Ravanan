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
summary_collection = db["top_down_summarization"]

# Gemini 2.0 Flash model
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a senior financial analyst providing a comprehensive investment analysis summary for '{company_name}' based on extensive news data and market intelligence. "
    "Your analysis must follow a rigorous top-down investment framework that addresses critical investment questions across 10 key analytical dimensions. "
    "Structure your response as a professional investment research report with clear sections, actionable insights, and evidence-based conclusions. "
    "Use the provided articles to extract relevant data points, quote specific information where valuable, and focus exclusively on content directly related to {company_name}. "
    "Ignore general market commentary unless it specifically impacts the target company. Present findings in clear, analytical language suitable for institutional investors and portfolio managers.\n\n"
    
    "**ANALYTICAL FRAMEWORK - 10 CORE DIMENSIONS:**\n\n"
    
    "## 1. COMPANY REVENUE ARCHITECTURE ANALYSIS\n"
    "**Industry Revenue Segmentation:** Analyze revenue distribution across industry verticals. What percentage comes from each sector? How has this mix evolved over 3-5 years? Is the company strategically diversifying or becoming more concentrated? Compare diversification strategy to key competitors.\n"
    "**Product Portfolio Performance:** Identify top-performing products by growth rate. Which products are in growth, maturity, or decline phases? What is the revenue contribution from products launched in the last 2-3 years versus legacy offerings? How does new product performance compare to market benchmarks?\n"
    "**Geographic Revenue Distribution:** Break down domestic versus international revenue. Which regions show highest growth rates? How has geographic mix shifted over time? What are the key risks (political, economic, currency) in major international markets? Does international expansion align with stated strategic goals?\n\n"
    
    "## 2. INDUSTRY STRUCTURAL DYNAMICS ANALYSIS\n"
    "**Market Segmentation & Positioning:** Map industry segments and the company's position within each. Which segments are experiencing growth, stability, or decline? Are there underserved segments representing opportunities? How concentrated or fragmented is each segment?\n"
    "**Supply-Demand Equilibrium:** Assess current demand versus supply conditions. Is industry demand growing faster than supply capacity? What are primary demand drivers? How cyclical is demand? What leading indicators predict demand shifts?\n"
    "**Cross-Industry Migration Trends:** Identify companies entering from adjacent industries or existing players diversifying. What capabilities facilitate successful industry boundary crossing? How are customer needs evolving to redefine industry boundaries?\n"
    "**Total Addressable Market (TAM) Analysis:** Quantify current TAM size and company's addressable portion. What is the 5-10 year TAM growth projection and key expansion/contraction factors? How does company's current market share compare to realistic TAM capture potential?\n"
    "**Industry Growth Dynamics:** Calculate industry CAGR over past 5 years. Which segments grow faster than average? Is growth accelerating or decelerating? What factors drive high-performing segments? How sustainable is current trajectory?\n"
    "**PESTLE Impact Assessment:** Identify which Political, Economic, Social, Technological, Legal, Environmental factors most significantly impact the industry. What upcoming changes might affect industry dynamics? How do these factors vary across geographic markets?\n"
    "**Industry Life Cycle Positioning:** Determine current stage (Introduction/Growth/Maturity/Decline). How long has industry been in this stage? Are different segments at different stages? What strategic implications arise from current positioning?\n"
    "**Value Migration Patterns:** Track how economic value shifts within the industry value chain. Where is profit concentration increasing/decreasing? Which business models gain/lose economic value? How might emerging technologies redistribute future value?\n"
    "**Performance Benchmarking:** Define 5-7 critical industry KPIs and compare company performance to competitors. Which KPIs most strongly correlate with financial performance? What operational metrics serve as leading indicators?\n"
    "**Strategic Framework Application:** Apply Porter's 5 Forces, SWOT Analysis, BCG Matrix, and GE-9 Box Matrix to evaluate industry attractiveness and competitive positioning.\n\n"
    
    "## 3. CONGLOMERATE PORTFOLIO ANALYSIS (if applicable)\n"
    "**Portfolio Balance Assessment:** For multi-industry companies, evaluate balance across different sectors using weightage-based scoring. Which segments contribute most to overall performance? How does resource allocation align with segment performance and potential?\n"
    "**Segment Financial Structure Analysis:** Compare financial structures across segments using vertical analysis. Which segments demonstrate most efficient cost structures? Do any segments benefit from conglomerate synergies?\n"
    "**Cross-Segment Industry Dynamics:** How diverse are industry dynamics across the portfolio? Which segments face most favorable/challenging conditions? Are there opportunities for cross-pollination of best practices?\n\n"
    
    "## 4. DISASTER RISK & RESILIENCE ANALYSIS\n"
    "**External Disruption Vulnerability:** Assess exposure to geopolitical conflicts, natural disasters, pandemics, climate change. How has the industry historically responded to major external shocks? What structural changes resulted from previous disruptions?\n"
    "**Tax Policy Sensitivity:** Analyze impact of potential tax rate changes on industry profitability. Which companies have most tax-efficient structures? What tax policy changes are under consideration?\n"
    "**ESG Risk & Opportunity Matrix:** Identify material ESG factors affecting financial performance. How are regulatory requirements evolving? Which companies lead/lag on critical ESG metrics? What ESG-related risks could impact industry economics?\n"
    "**Political Risk Exposure:** Evaluate sensitivity to political leadership changes. Which political factors historically impacted industry performance most? What upcoming political events could affect operations?\n"
    "**Governance & Scandal Risk:** Assess structural factors enabling potential misconduct. Are there industry characteristics creating vulnerability to scandals? What early warning signs indicate emerging governance problems?\n\n"
    
    "## 5. INVESTMENT TIMING OPTIMIZATION\n"
    "**Economic Cycle Alignment:** Determine how well industry aligns with current/projected economic conditions. For cyclical industries, assess current cycle position. Are disaster risks adequately reflected in valuations?\n"
    "**Performance Momentum Indicators:** What do leading KPIs indicate about future financial performance? Are there visible inflection points in key metrics? Do operational metrics support or contradict financial trends?\n"
    "**Integrated Timing Score:** Develop comprehensive timing assessment weighing Economic Fit, Disaster Risk, and Life Cycle factors. What changes would significantly improve/worsen timing score?\n"
    "**Position Recommendations:** Provide specific short-term (0-12 months) and long-term (1-5 years) position guidance. What catalysts would trigger position changes? What risk management parameters should accompany recommendations?\n\n"
    
    "## 6. MANAGEMENT & STRATEGIC QUALITY ASSESSMENT\n"
    "**Leadership Pedigree Analysis:** Evaluate founder's background and ongoing influence on strategic direction. How has founder's vision been institutionalized? If departed, how smooth was transition?\n"
    "**Promoter Holdings & Governance:** Analyze promoter shareholding and pledging patterns over time. What do these patterns suggest about insider confidence and corporate control? How aligned are promoter interests with minority shareholders?\n"
    "**Corporate Governance Standards:** Assess board independence, effectiveness, and shareholder rights protection. How transparent is company communication? What is compliance and ethical track record?\n"
    "**Executive Team Capability:** Evaluate C-level backgrounds, track records, and team dynamics. Do executives have relevant experience? How well does team complement each other's skills?\n"
    "**Business Model Sustainability:** Analyze distinctive aspects and competitive advantages embedded in business model. How sustainable is model against industry changes? What disruptions could threaten it?\n"
    "**Strategic Execution Excellence:** Evaluate pricing strategy, strategic fit, growth pattern effectiveness. How clearly articulated is strategy? Does company have capabilities to execute? How adaptable is strategy to changing conditions?\n"
    "**Innovation & Technology Leadership:** Assess R&D investment trends and effectiveness. Is company technology leader, fast follower, or laggard? How well integrated is technology strategy with business strategy?\n\n"
    
    "## 7. OPPORTUNITY & THREAT ASSESSMENT\n"
    "**M&A Potential & Strategy:** Evaluate likelihood of company being acquirer or target. What types of acquisitions align with strategy? What would be likely premium in takeover scenario?\n"
    "**Promoter Activity Signals:** Track recent changes in promoter holdings and pledging. What might motivate these changes? Do patterns suggest insider confidence or concern?\n"
    "**Innovation Pipeline Impact:** Analyze upcoming product launches and their strategic significance. What is potential revenue contribution? How does pipeline compare to competitor innovation efforts?\n"
    "**Fraud & Scandal Vulnerability:** Identify business model characteristics creating fraud risk. Are there financial red flags? How robust are governance and control mechanisms?\n"
    "**Stress Test Resilience:** Develop adverse scenarios testing business model robustness. How would company perform under severe industry downturns? What mitigating actions could management take in crisis?\n\n"
    
    "## 8. QUANTITATIVE VALUATION FRAMEWORK\n"
    "**Core Valuation Metrics Analysis:** Evaluate P/E, P/B, ROE, ROCE, EBITDA, EV, EV/EBITDA ratios. How do current levels compare to historical ranges and peer benchmarks? What growth rates are implied by current valuations?\n"
    "**Growth Trajectory Assessment:** Analyze revenue growth patterns (YoY, QoQ trends). What are primary growth drivers? How sustainable are current growth rates? Is growth accelerating or decelerating?\n"
    "**Valuation Methodology Application:** Apply DCF and relative valuation approaches. What are key value drivers in DCF model? How sensitive is valuation to assumption changes? How does relative valuation compare to peers?\n"
    "**Financial Quality Indicators:** Assess earnings quality, cash conversion, capital allocation effectiveness. How does company perform on industry-specific financial KPIs?\n\n"
    
    "## 9. LONG-TERM STRATEGIC LOGIC\n"
    "**Sustainable Competitive Advantages:** Identify and evaluate durability of competitive moats. Which advantages are strengthening or weakening over time? How defensible are these advantages against disruption?\n"
    "**Strategic Vision Alignment:** Assess how well long-term strategy aligns with industry evolution, technological trends, and market opportunities. Is company positioning for future value creation or defending legacy positions?\n"
    "**Capital Allocation Excellence:** Evaluate historical and planned capital allocation decisions. Are investments generating returns above cost of capital? How does capital allocation support strategic priorities?\n\n"
    
    "## 10. INVESTMENT DECISION SYNTHESIS\n"
    "**Risk-Adjusted Return Potential:** Synthesize quantitative and qualitative factors into expected return scenarios. What is the risk-adjusted return potential over different time horizons?\n"
    "**Catalyst Identification:** Identify specific near-term and medium-term catalysts that could drive outperformance. What events or developments would most significantly impact valuation?\n"
    "**Investment Recommendation:** Provide clear BUY/HOLD/SELL recommendation with specific price targets and time horizons. What position sizing is appropriate given conviction level and risk assessment?\n"
    "**Monitoring Framework:** Establish key metrics and triggers for ongoing position management. What changes would warrant reassessment of investment thesis?\n\n"
    
    "**OUTPUT REQUIREMENTS:**\n"
    "- Structure as professional investment research report with executive summary\n"
    "- Include specific metrics, percentages, and financial data where available\n"
    "- Provide clear investment recommendation with rationale\n"
    "- Identify key risks and opportunity factors\n"
    "- Establish monitoring framework for ongoing assessment\n"
    "- Ensure analysis is actionable for portfolio management decisions\n\n"
    
    "Your analysis should demonstrate deep understanding of both quantitative metrics and qualitative factors, providing institutional-quality investment research that supports data-driven investment decisions."
    ),
    ("human",
    "Company Name: {company_name}\n\nNews Articles and Market Data:\n\n{markdown}\n\n"
    "Using the comprehensive 10-dimension framework above, analyze the provided information about {company_name}. "
    "For each analytical dimension:\n"
    "- Extract and synthesize relevant insights from the articles\n"
    "- Provide specific data points, percentages, and metrics where available\n"
    "- Address the key questions outlined in each section\n"
    "- Connect findings across different analytical dimensions\n"
    "- Identify gaps where additional information would strengthen the analysis\n\n"
    "Conclude with:\n"
    "1. **Executive Summary** - Key investment highlights and concerns\n"
    "2. **Investment Recommendation** - Clear BUY/HOLD/SELL with price target if possible\n"
    "3. **Key Risk Factors** - Primary downside risks to monitor\n"
    "4. **Upside Catalysts** - Potential positive drivers for outperformance\n"
    "5. **Monitoring Framework** - Critical metrics and events to track\n\n"
    "Deliver a comprehensive investment analysis report that provides actionable insights for institutional investment decisions regarding {company_name}."
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