import os
import json
import re
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from serpapi import GoogleSearch

# Load environment variables
load_dotenv()
SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
    
# Initialize Groq LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# LLM prompt template
instruction_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert assistant that only responds with valid JSON. Do not explain anything. Output format:
{{
  "query": "<search phrase>",
  "source_type": "news",
  "info_depth": "deep",
  "language": "English",
}}
    Use the following methodology when creating your query:
1. Revenue Splitting by Industry:
   - Extract revenue data from annual reports and investor presentations.
   - Break down by industry segments.
   - Calculate each segment's revenue contribution.
   - Track changes over the last 3–5 years.
   - Compare the company's segment diversification to its peers.

2. Top Products Revenue Growth Analysis:
   - Identify major product lines or services.
   - Analyze year-over-year revenue growth.
   - Determine lifecycle maturity of each product.
   - Compare growth trends with competitors.
   - Evaluate product contribution to total revenue.
   - Highlight recent product launches or discontinuations.

3. Domestic vs International Business Distribution:
   - Segment revenue geographically (India vs foreign).
   - Observe changes in regional revenue share.
   - Detect exposure to foreign markets and expansion efforts.
   - Analyze risks and opportunities in each region.
   - Identify revenue from exports vs local sales.
   - Compare the company's regional business mix to industry norms.
   """
    ),
    ("human", "{user_prompt}")
])


# Create the chain
instruction_chain = instruction_prompt | llm | StrOutputParser()

# Function to get structured instruction
def get_scraping_instruction(user_prompt):
    result = instruction_chain.invoke({"user_prompt": user_prompt})
    print("\n🧠 Raw LLM Output:\n", result)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("LLM did not return valid JSON")

# Function to run DuckDuckGo search
def duckduckgo_search(query):
    search = GoogleSearch({
        "engine": "duckduckgo",
        "q": query,
        "kl": "us-en",
        "api_key": SERP_API_KEY
    })
    results = search.get_dict()
    return results.get("organic_results", [])

# Function to run Google search
def google_search(query, max_pages=5):
    all_results = []
    for start in range(0, max_pages * 10, 10):  # paginate
        search = GoogleSearch({
            "engine": "google",
            "q": query,
            "hl": "en",
            "gl": "us",
            "start": start,
            "api_key": SERP_API_KEY
        })
        results = search.get_dict()
        all_results.extend(results.get("organic_results", []))
    return all_results

def build_user_prompt(company_name):
    return (
        f"Provide in-depth news and analysis on {company_name} including revenue split, product growth, "
        "and domestic vs international business for the latest quarter results."
    )

# Final wrapper
def full_search(company_name):
    user_prompt = build_user_prompt(company_name)
    print("\n🔍 Step 1: Convert prompt to query...")
    instruction = get_scraping_instruction(user_prompt)
    query = instruction["query"]
    
    print(f"\n🔎 Step 2: DuckDuckGo Search for: {query}")
    ddg_results = duckduckgo_search(query)

    print(f"\n🔎 Step 3: Google Search (multi-page) for: {query}")
    google_results = google_search(query, max_pages=3)

    all_links = []
    for r in ddg_results + google_results:
        link = r.get("link")
        if link:
            all_links.append(link)

    unique_links = list(set(all_links))  # deduplication

    print(f"\n✅ Found {len(unique_links)} unique links:")
    for link in unique_links:
        print(link)

    return unique_links

def run_search(company_name):
    return full_search(company_name)

