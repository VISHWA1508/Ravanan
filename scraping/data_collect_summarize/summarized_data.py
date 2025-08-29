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
summary_collection = db["summarized_data"]

# Gemini 2.0 Flash model
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are a professional financial analyst providing a comprehensive investment analysis summary for '{company_name}' based on the latest news and data. "
    "Structure your response to align with a top-down investment framework, addressing key questions from each section. "
    "Use the provided articles to extract relevant insights. Be specific, quote or paraphrase sources where useful, and focus only on content directly related to {company_name}. "
    "Ignore general market commentary. Present in clear, plain English using bullet points or short paragraphs under each framework section for an educated investor audience.\n\n"
    "Framework Sections to Cover:\n"
    "1. **Company Analysis:** Revenue splitting by industry/products/geography, growth trends, diversification vs. competitors, alignment with goals.\n"
    "2. **Industry Analysis:** Segmentation, demand/supply trends, cross-industry migration, TAM, CAGR, PESTLE, cycle/life cycle stage, value migration, KPIs, financial/strategic tools (Porter's, SWOT, BCG, GE Matrix).\n"
    "3. **Conglomerate Analysis (if applicable):** Portfolio balance, segment performance, financial structures, industry dynamics.\n"
    "4. **Disaster Management:** External disruptions, tax/ESG/political risks, scandals.\n"
    "5. **Investment Time Decision:** Economic fit, KPI/financial evaluation, timing score, position recommendations.\n"
    "6. **Company Qualitative Analysis:** Founder/promoter background, governance, executives, business model, pricing/strategy, growth patterns, R&D, technology adoption.\n"
    "7. **Opportunity & Threat Analysis:** M&A potential, promoter trends, product pipeline, fraud risks, stress scenarios.\n"
    "8. **Company Quantitative Analysis:** Valuation metrics (P/E, P/B, ROE, ROCE, EBITDA, EV, EV/EBITDA), growth metrics (revenue, YoY/QoQ), valuation methodologies (DCF, relative).\n\n"
    "For each section, highlight key metrics, trends, risks, opportunities, and forward-looking insights. If data is insufficient for a section, note it briefly. Ensure the summary is direct, insightful, and actionable for investment decisions."
    ),
    ("human",
    "Company Name: {company_name}\n\nArticles:\n\n{markdown}\n\n"
    "# Apply the framework above to synthesize insights from the articles. For each section:\n"
    "- Summarize key findings with supporting evidence from the data.\n"
    "- Address specific questions like revenue distribution changes, TAM growth, PESTLE impacts, valuation justifications, etc.\n"
    "- End with implications for investors (e.g., buy/hold/sell signals, risks to monitor).\n"
    "# Your response should be a complete, structured analysis report for tracking {company_name}."
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