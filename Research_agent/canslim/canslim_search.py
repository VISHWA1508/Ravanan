import os
import json
import re
import random
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from serpapi.google_search import GoogleSearch  # Updated import

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
        print(f"Error getting random API key for {key_name}: {e}")
        raise

try:
    SERP_API_KEY = get_random_api_key("SERPAPI_API_KEY")
    GOOGLE_API_KEY = get_random_api_key("GOOGLE_API_KEY")
    print("✅ Successfully loaded random API keys")
except Exception as e:
    print(f"❌ Error loading API keys: {e}")
    raise
    
# Initialize Gemini LLM with random API key
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY
)

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

Complete CAN SLIM Investment Analysis Framework
Current Quarterly Earnings (C) - Short-term Factor
Current quarter earnings growth and quality are essential indicators of business momentum and can trigger significant stock price movements when results exceed or fall short of expectations.

Methodology:
Analyze current earnings performance:

Current quarter earnings per share growth rate

Revenue growth rate and sustainability

Earnings quality and composition analysis

Beat/miss versus consensus expectations

Guidance provided and tone of management

Operating leverage and margin trends

One-time items and adjustments impact

Cash flow generation relative to earnings

Working capital changes and implications

Segment performance breakdown

Evaluate earnings momentum indicators:
11. Sequential quarter-over-quarter trends
12. Year-over-year acceleration or deceleration
13. Earnings revision trends leading up to announcement
14. Surprise history and consistency
15. Quality of earnings surprise (revenue vs. cost)
16. Management commentary on forward trends
17. Peer group earnings comparison
18. Industry-specific metrics performance
19. Leading indicator alignment with results

Annual Earnings Growth (A) - Long-term Factor
Consistent annual earnings growth over multiple years demonstrates a company's ability to compound shareholder value and adapt to changing business conditions, forming the foundation for long-term investment success.

Methodology:
Analyze historical earnings growth:

Annual EPS growth rate over 3-5 years

Revenue growth consistency and trajectory

Earnings growth stability and volatility

Growth rate acceleration or deceleration trends

Cyclical versus secular growth characteristics

Geographic and segment contribution to growth

Organic versus acquisition-driven growth

Market share gains supporting growth

Pricing power demonstration through cycles

Operational efficiency improvements

Evaluate growth quality and sustainability:
11. Return on equity and invested capital trends
12. Cash conversion and working capital efficiency
13. Capital allocation effectiveness
14. Reinvestment rate and growth correlation
15. Competitive advantage sustainability
16. Management execution track record
17. Industry tailwinds supporting growth
18. Scalability of business model
19. Innovation pipeline and R&D effectiveness
20. Financial leverage and capital structure optimization

New Products, Services, or Management (N) - Long-term Factor
Innovation in products, services, or leadership can create significant long-term value by opening new markets, improving competitive positioning, or enhancing operational effectiveness.

Methodology:
Evaluate new product and service developments:

New product launch pipeline and timeline

Innovation investment levels and R&D spending

Patent portfolio and intellectual property strength

Product lifecycle management effectiveness

Time-to-market capabilities and speed

Customer adoption rates of new offerings

Revenue contribution from new products

Competitive differentiation of innovations

Market size and opportunity for new products

Technology platform scalability

Assess management quality and changes:
11. Leadership team experience and track record
12. Recent management changes and impact
13. Strategic vision articulation and execution
14. Capital allocation decision quality
15. Operational excellence and efficiency focus
16. Corporate governance and transparency
17. Stakeholder communication effectiveness
18. Industry expertise and relationships
19. Cultural transformation and employee engagement
20. Succession planning and talent development


CAN SLIM Investment Analysis Framework - Supply & Demand and Leadership Analysis
Supply and Demand (S) - Short-term Factor
Business and stock supply-demand fundamentals are critical short-term indicators that can drive significant price movements through their impact on operational performance and investor behavior.

Methodology:
Analyze business supply-demand fundamentals:

Product demand trends and growth trajectory

Market size expansion or contraction

Inventory levels throughout value chain

Pricing power and pricing trend analysis

Customer demand visibility and backlog

Supply chain constraints or advantages

Raw material availability and pricing

Production capacity utilization rates

Working capital efficiency trends

Revenue per unit and unit growth decomposition

Evaluate stock supply-demand dynamics:
11. Float size and trading liquidity
12. Insider buying or selling activity
13. Share buyback programs and execution
14. Share dilution from issuance or options
15. Short interest levels and trends
16. Days to cover ratio
17. Institutional accumulation or distribution
18. Retail investor sentiment and activity
19. Options activity and positioning
20. Technical supply and resistance levels

Identify near-term catalysts affecting supply-demand balance:
21. Upcoming earnings announcements
22. Industry conferences or trade shows
23. Product launch events
24. Regulatory decisions
25. Index inclusion possibilities

Leader and Industry (L) - Long-term Factor
Industry leadership position and overall industry strength are powerful determinants of long-term performance potential, providing context for sustainable competitive advantage and growth opportunity.

Methodology:
Evaluate industry characteristics:

Industry growth rate and trajectory

Industry profit pool size and distribution

Competitive intensity and structure

Barriers to entry and disruption risk

Regulatory environment and outlook

Industry life cycle positioning

Assess company leadership position:
7. Market share and rank within industry
8. Market share trend (gaining or losing)
9. Differentiation and competitive advantages
10. Brand strength and recognition
11. Innovation leadership
12. Thought leadership and industry influence

Analyze relative strength metrics:
13. Revenue growth versus industry average
14. Margin premium or discount to peers
15. Return on invested capital ranking
16. Stock price performance versus industry index
17. Valuation premium or discount to sector

Identify leadership sustainability factors:
18. Scale advantages and network effects
19. Intellectual property protection
20. Customer switching costs
21. Data or technology advantages
22. Talent acquisition and retention capabilities

Institutional Interest (I) - Short-term Factor
Institutional ownership patterns and changes can signal professional investor conviction and create significant buying pressure, providing insight into potential near-term price support and momentum.

Methodology:
Analyze institutional ownership metrics:

Percentage of shares held by institutions

Number of institutional holders

Concentration among top institutional holders

Quality and type of institutional investors

Changes in institutional ownership over recent quarters

Evaluate institutional trading patterns:
6. New institutional positions established
7. Existing positions increased significantly
8. Positions reduced or eliminated
9. Ownership changes by investor type (growth, value, index, etc.)
10. Block trade activity

Assess institutional sentiment indicators:
11. Analyst coverage trends
12. Consensus recommendation changes
13. Price target revisions
14. Institutional investor commentary
15. Conference call participation and questions

Identify potential institutional catalysts:
16. Index inclusion or weighting changes
17. Investment style rotation
18. Activist investor involvement
19. Sell-side conferences or non-deal roadshows
20. Potential for institutional re-rating

Market Trends (M) - Both Short and Long-term Factor
Overall market direction and sector rotation patterns significantly influence individual stock performance, providing essential context for both timing decisions and long-term positioning.

Methodology:
Analyze broad market trends:

Major index direction and momentum

Market breadth indicators

Sector rotation patterns

Risk appetite metrics

Technical support and resistance levels

Volatility environment

Evaluate sector-specific trends:
7. Sector performance relative to broad market
8. Sector momentum and leadership rotation
9. Sector fund flows
10. Sector sentiment indicators
11. Sector valuation relative to historical ranges

Assess stock-specific technical patterns:
12. Price trend direction and strength
13. Volume patterns and accumulation/distribution
14. Moving average relationships
15. Relative strength versus market and sector
16. Chart patterns and support/resistance levels

Identify market environment characteristics:
17. Prevailing investment factors (growth, value, quality, etc.)
18. Correlation regime (high or low correlation environment)
19. Macro influence degree (macro or stock-specific driven)
20. Risk-on or risk-off sentiment
21. Liquidity conditions

Integration of Long-term Factors (A, N, L, M)
The integration of long-term CAN SLIM factors provides a comprehensive framework for evaluating a company's sustainable growth potential and competitive positioning, forming the foundation for long-term investment decisions.

Methodology:
Synthesize long-term factor insights:

Annual earnings growth trajectory and quality

New product pipeline and innovation potential

Industry attractiveness and leadership position

Long-term market trends and sector positioning

Evaluate factor interaction effects:
5. Reinforcing patterns across multiple factors
6. Contradictory signals requiring resolution
7. Relative importance weighting in current environment
8. Leading versus lagging indicator analysis

Develop long-term investment thesis:
9. Sustainable growth rate expectations
10. Competitive advantage durability
11. Value creation potential
12. Key risks and mitigating factors
13. Appropriate investment time horizon

Establish long-term monitoring framework:
14. Critical metrics for ongoing evaluation
15. Thesis validation milestones
16. Warning signs that would challenge thesis
17. Potential catalysts for re-rating
18. Regular reassessment schedule
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
        f"Provide in-depth news and analysis on {company_name}"
        f"What is the current quarter earnings growth rate and quality? - Did earnings beat, meet, or miss expectations and by how much? - What drove the earnings performance (revenue growth, margin expansion, cost control)? - How sustainable is the current earnings momentum? - What guidance or commentary did management provide about future quarters? - How do current results compare to industry peers?"
        f"What is the company's annual earnings growth rate over the past 3-5 years? - How consistent and sustainable is the historical growth pattern? - What are the primary drivers of earnings growth? - How does growth compare to industry peers and market averages? - What factors support continued long-term earnings growth? - What risks could disrupt the historical growth trajectory?"
        f"What new products or services is the company developing or launching? - How significant could new products be to future revenue and profits? - What is the company's track record of successful innovation? - Has there been recent management changes that could drive improvement? - How effective is the current management team at executing strategy? - What competitive advantages do new products or management changes create?"
        f"What do industry supply-demand dynamics suggest about pricing power? - How tight is inventory throughout the value chain? - What unusual trading volume or ownership patterns are evident in the stock? - Is institutional ownership increasing or decreasing? - What potential near-term catalysts could shift supply-demand balance? - How might current supply-demand dynamics affect short-term price movement?"
        f"Is the company a leader in its industry by market share or innovation? - Is the company gaining or losing market share? - How attractive is the industry structure and growth outlook? - What sustainable competitive advantages support leadership position? - How does the company's performance compare to industry peers? - What threats could challenge the company's leadership position?"
        f"Is institutional ownership increasing, stable, or decreasing? - What quality of institutions are buying or selling? - Are there new institutional investors establishing positions? - How concentrated is institutional ownership? - What is the potential for additional institutional buying? - What catalysts might drive increased institutional interest?"
        f"What is the direction and strength of the overall market trend? - How is the stock's sector performing relative to the broader market? - Is the stock showing relative strength or weakness versus its sector? - What technical patterns suggest potential support or resistance levels? - How might current market conditions affect the stock's performance? - What market environment would be most favorable for this stock?"
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

