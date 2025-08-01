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
     "You are a professional financial assistant helping an investor understand the latest news about '{company_name}'. "
     "Write a clear, concise summary that highlights key points about the company’s performance, outlook, results, and any important management commentary. "
     "Ignore general market updates or irrelevant news. Present it in a way that's easy to understand."),
    ("human", "Company Name: {company_name}\n\nArticles:\n\n{markdown}")
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

# Group all raw articles by company
company_articles = defaultdict(list)
for doc in collection.find():
    raw_content = doc.get("raw_content", "").strip()
    company = clean_company_name(doc.get("company", ""))
    if raw_content and company:
        company_articles[company].append(raw_content)

# Summarize each company
for company, articles in company_articles.items():
    combined_text = "\n\n---\n\n".join(articles)

    print(f"\n📊 Summarizing {len(articles)} articles for: {company}")

    try:
        # You may chunk if content is too long (Gemini 2.0 Flash can handle ~20,000 tokens)
        if len(combined_text.split()) > 10000:
            chunks = chunk_text(combined_text, max_length=3000)
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                print(f"🧩 Processing chunk {idx + 1} of {len(chunks)}")
                summary = chain.invoke({
                    "markdown": chunk,
                    "company_name": company
                }).strip()
                chunk_summaries.append(summary)

            # Now combine the chunk summaries into one final summary
            final_summary = chain.invoke({
                "markdown": "\n\n".join(chunk_summaries),
                "company_name": company
            }).strip()

        else:
            # One-shot summary for shorter input
            final_summary = chain.invoke({
                "markdown": combined_text,
                "company_name": company
            }).strip()

        # Save result to MongoDB
        summary_collection.insert_one({
            "company": company,
            "summary": final_summary,
            "summarized_at": datetime.now(timezone.utc)
        })
        print(f"✅ Summary saved for {company}")

    except Exception as e:
        print(f"❌ Error summarizing {company}: {e}")
