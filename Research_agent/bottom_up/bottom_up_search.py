import os
import json
import re
import random
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from serpapi import GoogleSearch

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
    
# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",    google_api_key=GOOGLE_API_KEY
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
    Use the following methodology and key questions when creating your query:
 Part II: Bottom-Up Investment Analysis Framework

1. Segment Problem Analysis
2. Strategic Pillar Scorecard
3. Life Cycle and Disruption
4. Financial Analysis
5. Valuation
6. Strategic Intelligence Layer
7. Stress Simulation
8. CAN SLIM Integration

11. Segment Problem Analysis
 Segment Name
 Understanding the precise identity and positioning of a business segment is the
 foundation of bottom-up analysis. The segment name provides critical context about the
 specific market niche, product category, or service area being evaluated.
 Methodology:
    1. Identify the official segment designation as reported in company financial statements and investor presentations.
    2. Research alternative industry terminology or classifications that might apply to this segment.
    3. Analyze how the company positions this segment in its communications with investors and customers.
    4. Compare the segment naming convention with industry standards and competitor terminology.
    5. Evaluate whether the segment name accurately reflects its actual business activities and market focus.

Parent Division
 Understanding where a segment fits within the broader organizational structure
 provides insights into its strategic importance, resource allocation, and management
 attention.
 Methodology:
    1. Map the organizational hierarchy from segment to division to corporate level.
    2. Research the division's overall strategy and how the segment contributes to it.
    3. Analyze the segment's relative size and importance within its parent division.
    4. Identify key decision-makers at the division level who influence the segment.
    5. Evaluate how the division's priorities and resource allocation affect the segment.
    6. Research any planned reorganizations that might affect the segment's positioning.

 Parent Company
 The relationship between a segment and its parent company provides critical context for
 understanding strategic priorities, resource allocation, and potential corporate actions
 that might affect the segment.
 Methodology:
    1. Analyze the segment's contribution to overall corporate revenue, profit, and
    growth.
    2. Research statements from corporate leadership about the segment's strategic
    importance.
    3. Evaluate the segment's alignment with the parent company's core competencies
    and mission.
    4. Identify potential synergies or conflicts between the segment and other parts of the
    company.
    5. Research the history of corporate investments in the segment.
    6. Analyze any rumors or announcements regarding potential divestiture, spin-off, or
    expansion.

Industry Mapping
 Placing a segment within its broader industry context helps identify competitive
 dynamics, market trends, and growth opportunities that might not be apparent from
 company-specific analysis alone.
 Methodology:
    1. Identify the primary industry classification codes (e.g., NAICS, SIC, GICS) that apply
    to the segment.
    2. Map the segment's position within the industry value chain (upstream, midstream,
    downstream).
    3. Analyze the segment's overlap with adjacent or related industries.
    4. Identify key industry associations, regulatory bodies, and standards organizations
    relevant to the segment.
    5. Research industry-specific metrics and benchmarks applicable to the segment.
    6. Evaluate how industry boundaries are evolving and potential implications for the
    segment.

Segment Revenue
 Revenue analysis provides fundamental insights into a segment's scale, growth
 trajectory, and market penetration, forming the foundation for more detailed financial
 analysis.
 Methodology:
    1. Collect historical segment revenue data from company financial statements and
    presentations.
    2. Analyze revenue trends over at least 3-5 years, identifying patterns and inflection
    points.
    3. Break down revenue by product lines, customer segments, or geographic regions if
    data is available.
    4. Compare segment revenue growth to overall company, division, and industry
    growth rates.
    5. Identify seasonality patterns or cyclicality in revenue generation.
    6. Research management commentary on factors driving revenue performance.

Compound Annual Growth Rate (CAGR)
 CAGR provides a smoothed growth rate that helps identify sustainable trends and
 compare performance across different time periods, segments, or companies.
 Methodology:
    1. Calculate the segment's revenue CAGR over multiple timeframes (3-year, 5-year, 10
    year if available).
    2. Compare the segment's CAGR to division, company, industry, and relevant market
    benchmarks.
    3. Analyze CAGR for different components of the segment (product lines, geographies,
    etc.).
    4. Identify factors that have influenced CAGR during different periods.
    5. Evaluate whether historical CAGR is likely to be sustainable going forward.
    6. Research analyst projections for future growth rates.

 EBITDA Contribution
 EBITDA contribution analysis reveals a segment's profitability and its importance to
 overall company financial performance, helping assess both absolute and relative value
 creation.
Methodology:
    1. Calculate the segment's EBITDA (Earnings Before Interest, Taxes, Depreciation, and
    Amortization) from available financial data.
    2. Analyze the segment's EBITDA as a percentage of total company or division EBITDA.
    3. Track changes in EBITDA contribution over time (absolute and percentage).
    4. Compare the segment's EBITDA margin to division, company, and industry
    benchmarks.
    5. Identify factors driving changes in EBITDA contribution.
    6. Evaluate the relationship between revenue contribution and EBITDA contribution.

 Geographic Exposure
 Understanding a segment's geographic footprint provides insights into market
 penetration, growth opportunities, and exposure to regional economic conditions,
 regulatory environments, and currency fluctuations.
 Methodology:
    1. Map the segment's revenue by geographic region based on available disclosures.
    2. Analyze trends in geographic distribution over time.
    3. Research the segment's physical presence (facilities, employees) across regions.
    4. Identify growth rates and profitability by geographic market.
    5. Evaluate exposure to geopolitical risks, currency fluctuations, and regional
    economic conditions.
    6. Research the segment's expansion plans or contraction in specific geographies.

 Core-Non Core Classification
 Determining whether a segment represents a core or non-core business helps assess its
 strategic importance, resource allocation priority, and potential for corporate actions
 like expansion, divestiture, or spin-off.
 Methodology:
    1. Research company statements about strategic priorities and core businesses.
    2. Analyze the segment's alignment with the company's stated mission and long-term
    vision.
    3. Evaluate the segment's fit with the company's core competencies and capabilities.
    4. Assess the segment's historical importance to the company's identity and success.
    5. Research analyst opinions on whether the segment is considered core or non-core.
    6. Identify any signals suggesting potential changes in the segment's strategic
    classification.

12. Strategic Pillar Scorecard
 Growth Potential
 Assessing a segment's growth potential is critical for determining its future value
 contribution and investment attractiveness. This analysis examines both historical
 performance and forward-looking indicators to evaluate sustainable growth prospects.
 Methodology:
    1. Analyze historical growth patterns:
    2.  Revenue growth trends over multiple time periods
    3.  Market share evolution within the segment's addressable market
    4.  Growth relative to industry benchmarks and competitors
    5.  Consistency and volatility of growth rates
    6.  Evaluate market expansion opportunities:
    7.  Total addressable market (TAM) size and penetration rate
    8.  Adjacent market expansion possibilities
    9.  Geographic expansion potential
    10. New customer segment opportunities
    11. Assess product and service innovation pipeline:
    12. New product development roadmap
    13. R&D investment levels and effectiveness
    14. Patent applications and intellectual property portfolio
    15.  Innovation track record and time-to-market metrics
    16.  Analyze growth enablers and constraints:
    17.  Production capacity and scalability
    18.  Distribution channel development
    19.  Talent acquisition and retention capabilities
    20.  Capital availability for growth investments
    21.  Develop growth scenarios (base, upside, downside) with probability weightings.

 Profitability
 Profitability analysis evaluates a segment's ability to generate returns relative to its
 revenue and invested capital, providing insights into operational efficiency, pricing
 power, and competitive positioning.
 Methodology:
    1. Analyze profitability metrics and trends:
    2.  Gross margin evolution over time
    3.  EBITDA margin compared to industry benchmarks
    4.  Operating margin trajectory and drivers
    5.  Net profit margin sustainability
    6.  Evaluate profitability drivers:
    7.Pricing power and trends 
    8. Cost structure advantages or disadvantages
    9.  Scale economies and operational leverage
    10.  Product mix effects on overall profitability
    11.  Assess profitability sustainability:
    12.  Competitive intensity and margin pressure
    13.  Cost inflation exposure and mitigation strategies
    14.  Regulatory impacts on pricing or costs
    15.  Technology impacts on cost structure
    16.  Analyze profitability across product lines, customer segments, or geographies.
    17.  Develop profitability improvement scenarios and required actions.

MOAT of Differentiation
 The MOAT analysis evaluates a segment's sustainable competitive advantages that
 protect it from competition and enable superior returns over time. This assessment is
 crucial for determining long-term value creation potential.
 Methodology:
    1. Identify and evaluate potential competitive advantages:
    2.  Brand strength and customer loyalty
    3.  Proprietary technology or intellectual property
    4.  Network effects or ecosystem advantages
    5.  Scale economies or cost advantages
    6. Regulatory barriers or licenses 
    7. Exclusive partnerships or distribution channels
    8.  Assess the sustainability of each advantage:
    9.  Difficulty of replication by competitors
    10.  Historical durability under competitive pressure
    11.  Vulnerability to technological disruption
    12.  Dependence on specific individuals or relationships
    13.  Quantify the impact of competitive advantages:
    14.  Premium pricing ability
    15.  Customer retention metrics
    16.  Market share stability or growth
    17.  Profitability relative to competitors
    18.  Evaluate management actions to strengthen or expand the MOAT.
    19. Identify potential threats to existing competitive advantages.

 Opportunity of Risk
 This analysis evaluates the balance between upside opportunities and downside risks
 facing the segment, providing a nuanced view of its risk-reward profile and potential
 volatility.
Methodology:
    1. Identify and categorize key opportunities:
    2.  Market expansion possibilities
    3.  New product or service development
    4.  Potential acquisitions or partnerships
    5.  Operational improvement initiatives
    6.  Favorable regulatory or market trends
    7.  Assess and categorize key risks:
    8.  Competitive threats
    9.  Technological disruption potential
    10.  Regulatory or compliance challenges
    11.  Operational vulnerabilities
    12.  Macroeconomic sensitivities
    13.  Evaluate each opportunity and risk based on:
    14.  Probability of occurrence
    15.  Potential magnitude of impact
    16.  Timeframe for materialization
    17.  Management preparedness and response capability
    18.  Develop integrated scenarios incorporating multiple opportunities and risks.
    19.  Assess management's risk awareness and mitigation strategies.

Strategic Synergy
 Strategic synergy analysis evaluates how effectively the segment integrates with and
 contributes to the broader company, assessing both realized and potential synergies
 across various dimensions.
 Methodology:
    1. Identify and evaluate existing synergies:
    2.  Cost synergies (shared services, purchasing power, etc.)
    3.  Revenue synergies (cross-selling, bundling, etc.)
    4.  Innovation synergies (shared R&D, technology transfer)
    5.  Market access synergies (shared distribution channels)
    6.  Financial synergies (capital allocation, tax efficiency)
    7.  Quantify the value of realized synergies:
    8.  Cost savings achieved
    9.  Incremental revenue generated
    10.  Capability enhancements enabled
    11.  Assess potential for additional synergy capture:
    12.  Untapped synergy opportunities
    13.  Barriers to further synergy realization
    14.  Management initiatives to enhance synergies
    15.  Evaluate negative synergies or conflicts:
    16.  Resource competition with other segments
    17.  Strategic misalignment issues
    18.  Cultural or operational friction points
    19. Analyze how the segment would perform as a standalone entity versus within the
    company.

13. Life Cycle and Disruption
 Industry Life Cycle Stage
 Understanding where an industry segment sits in its life cycle provides crucial context
 for growth expectations, competitive dynamics, and appropriate strategies. This analysis
 helps determine whether a segment is in the emerging, growth, mature, or decline
 phase.
 Methodology:
    1. Analyze key life cycle indicators:
    2.  Market growth rate trends over multiple periods
    3.  Customer adoption patterns and penetration levels
    4.  Industry consolidation trends and M&A activity
    5.  Standardization of products and services
    6.  Competitive intensity evolution
    7.  Pricing trends and margin pressures
    8.  Identify specific characteristics of the current life cycle stage:
    9.  Emerging: Rapid innovation, uncertain standards, limited competition, high growth potential
    10.  Growth: Accelerating adoption, increasing competition, expanding market, business model validation
    11. Mature: Slowing growth, consolidation, efficiency focus, established standards, stable market shares
    12. Decline: Negative growth, excess capacity, price competition, diminishing innovation, market contraction
    13. Evaluate where different subsegments may be at different life cycle stages.
    14. Assess the segment's position relative to the broader industry life cycle.
    15. Estimate the likely duration of the current life cycle stage.
    16. Identify potential catalysts that could accelerate transition to the next stage.

 Technology Disruption Risk
 This analysis evaluates the vulnerability of a segment to technological disruption that
 could fundamentally alter its business model, competitive landscape, or value
 proposition.
 Methodology:
    1. Identify potential disruptive technologies relevant to the segment:
    2.  Emerging technologies in research or early commercialization
    3.  Adjacent technologies that could be applied to the segment
    4.  Exponential technologies with rapidly improving price-performance
    5.  Technologies enabling new business models or value propositions
    6.  Assess each technology's disruptive potential:
    7.  Performance trajectory relative to incumbent solutions
    8.  Cost reduction potential
    9.  Ability to address unserved customer needs
    10. Potential to remove industry constraints or bottlenecks
    11. Network effects or platform potential
    12.  Evaluate the segment's vulnerability to disruption:
    13.  Reliance on legacy technologies or infrastructure
    14.  Profit pool concentration in potentially disrupted activities
    15.  Historical adaptability to technological change
    16.  Regulatory or structural barriers to technology adoption
    17.  Analyze the segment's response to potential disruption:
    18.  R&D investments in potentially disruptive technologies
    19.  Acquisition or partnership strategy for emerging technologies
    20.  Organizational flexibility and innovation culture
    21.  Willingness to cannibalize existing products or services

ESG Policy Shock Risk
 This analysis evaluates the segment's vulnerability to sudden or significant changes in
 environmental, social, or governance policies that could impact operations, costs, or
 market access.
 Methodology:
    1.  Identify key ESG policy areas relevant to the segment:
    2. Environmental: Carbon emissions, resource usage, waste management, biodiversity impact
    3. Social: Labor practices, community relations, product safety, data privacy
    4. Governance: Board structure, executive compensation, shareholder rights, business ethics
    5. Assess current and emerging regulatory trends in these areas:
    6. Pending legislation or regulatory changes
    7. International policy convergence or divergence
    8. Industry-specific standards and requirements
    9. Voluntary frameworks becoming mandatory
    10. Evaluate the segment's exposure to policy changes:
    11. Current compliance status and gaps
    12. Cost implications of potential policy changes
    13. Ability to pass through compliance costs
    14. Competitive positioning relative to ESG performance
    15. Analyze the segment's preparedness for policy changes:
    16. Proactive investments in ESG improvements
    17. Scenario planning and risk management
    18. Disclosure practices and transparency
    19. Engagement with policymakers and stakeholders

Broad Substitution Risk
 This analysis examines the vulnerability of a segment to substitution by alternative
 products, services, or solutions that could capture market share or render current
 offerings obsolete.
 Methodology:
    1. Identify potential substitutes for the segment's key offerings:
    2.  Direct substitutes (similar products with different attributes)
    3.  Indirect substitutes (different solutions to the same customer need)
    4.  New categories that could make current offerings unnecessary
    5.  Do-it-yourself or insourcing alternatives
    6.  Assess substitution drivers and barriers:
    7.  Relative price-performance of substitutes
    8.  Switching costs for customers
    9.  Complementary ecosystem lock-in
    10.  Customer awareness and perception of alternatives
    11.  Network effects or installed base advantages
    12.  Evaluate substitution trends and patterns:
    13.  Historical substitution rates and patterns
    14.  Customer segments most vulnerable to substitution
    15.  Geographic variations in substitution trends
    16.  Inflection points that could accelerate substitution
    17.  Analyze the segment's response to substitution threats:
    18.  Product innovation to maintain differentiation
    19.  Pricing strategies to retain customers
    20.  Expansion into substitute categories
    21.  Business model adaptation


 High Innovation Impact
 This analysis evaluates how innovation within and around the segment could create
 significant opportunities or threats, focusing on the potential magnitude of impact
 rather than just the likelihood.
 Methodology:
    1. Identify high-impact innovation areas relevant to the segment:
    2.  Product or service innovations that could dramatically expand the market
    3.  Process innovations that could significantly alter cost structures
    4.  Business model innovations that could change how value is created and captured
    5.  Experience innovations that could redefine customer expectations
    6.  Assess the potential magnitude of impact:
    7.  Market size expansion or contraction potential
    8.  Margin enhancement or compression implications
    9.  Capital intensity increases or reductions
    10.  Value chain reconfiguration possibilities
    11.  Evaluate innovation sources and dynamics:
    12.  Internal R&D pipelines within the segment
    13.  Startup ecosystem and venture capital focus
    14.  Adjacent industry spillover effects
    15.  Academic and research institution priorities
    16.  Analyze the segment's innovation positioning:
    17.  Innovation investment levels relative to peers
    18.  Track record of successful innovation
    19.  Organizational capabilities for innovation
    20.  Cultural openness to disruptive ideas

14. Financial Analysis
 Revenue Analysis
 A comprehensive revenue analysis provides critical insights into a segment's growth
 trajectory, market position, and business model sustainability. This multifaceted
 examination goes beyond simple growth rates to understand the fundamental drivers of
 revenue performance.
 Revenue Trends
 Methodology:
    1. Collect historical revenue data for at least 5 years, preferably quarterly if available. 
    2.  Analyze absolute revenue levels and year-over-year changes.
    3.  Identify seasonality patterns and adjust for one-time events.
    4.  Compare revenue trends to industry benchmarks and key competitors.
    5.  Identify inflection points and their potential causes.
    6.   Evaluate the consistency and predictability of revenue streams.

 Revenue Growth Rate
 Methodology:
    1. Calculate growth rates across multiple timeframes:
    2.  Quarter-over-quarter (sequential)
    3.  Year-over-year (annual)
    4.  Compound annual growth rate (3-year, 5-year)
    5.  Rolling 12-month growth rates
    6.  Decompose growth into organic versus acquired components.
    7.  Adjust for currency effects, divestitures, and accounting changes.
    8.  Compare growth rates to relevant market growth and competitive benchmarks.
    9.  Analyze acceleration or deceleration patterns and their drivers.
    10. Evaluate growth sustainability based on market penetration and addressable market

Revenue Mix Breakdown
 Methodology:
    1. Segment revenue by relevant categories:
    2.  Product lines or service offerings
    3.  Customer segments or industries
    4.  Geographic regions or countries
    5.  Distribution channels
    6.  Business models (subscription, transaction, etc.)
    7.  Analyze the evolution of revenue mix over time.
    8.  Identify high-growth and high-margin components.
    9.  Evaluate concentration risks in specific categories.
    10.  Assess strategic alignment of revenue mix with company priorities.
    11.  Compare revenue mix to industry peers and best practices.

 Export Share Percentage
 Methodology:
    1.  Calculate export revenue as a percentage of total revenue.
    2. Track changes in export share over time.
    3. Break down exports by destination region or country.
    4.  Analyze growth rates in domestic versus export markets.
    5.  Evaluate currency exposure and hedging strategies.
    6.  Assess competitive positioning in key export markets.
    7.  Research trade policies and barriers affecting export potential.

 Pricing Power Analysis
 Methodology:
    1. Analyze historical pricing trends:
    2.  Average selling price evolution
    3.  Price increases versus inflation
    4.  Discount levels and promotional activity
    5.  Price realization rates
    6.  Evaluate factors affecting pricing power:
    7.  Brand strength and differentiation
    8.  Competitive intensity
    9.  Customer concentration
    10.  Switching costs
    11.  Value proposition clarity
    12.  Research customer price sensitivity through:
    13.  Price elasticity calculations
    14.  Win/loss analysis
    15.  Customer interviews or surveys
    16.  Competitive response patterns
    17.  Assess potential for future price increases or pressure.
    18. Analyze pricing strategies across different product lines or markets.

    
Profitability Analysis
 Profitability analysis examines a segment's ability to convert revenue into various levels
 of profit, providing insights into operational efficiency, competitive positioning, and
 value creation potential.
 Gross Margin Percentage
 Methodology:
    1. Calculate gross margin percentage (gross profit divided by revenue).
    2.  Track gross margin trends over multiple periods.
    3.  Compare gross margins to industry benchmarks and key competitors.
    4.  Analyze factors affecting gross margin:
    5.  Pricing trends
    6.  Input cost fluctuations
    7.  Product mix shifts
    8.  Manufacturing efficiency
    9.  Scale effects
    10.  Evaluate gross margin differences across product lines or business units.
    11.  Assess the relationship between gross margin and volume or market share.


 EBITDA Margin Percentage
 Methodology:
    1. Calculate EBITDA margin percentage (EBITDA divided by revenue).
    2.  Track EBITDA margin trends over multiple periods.
    3.  Compare EBITDA margins to industry benchmarks and key competitors.
    4.  Analyze the relationship between gross margin and EBITDA margin.
    5.  Evaluate operating expense efficiency and scalability.
    6.  Assess the impact of fixed versus variable cost structure.
    7.  Identify opportunities for operational leverage improvement.

    
 Operating Margin Percentage
 Methodology:
    1. Calculate operating margin percentage (operating profit divided by revenue).
    2.  Track operating margin trends over multiple periods.
    3.  Compare operating margins to industry benchmarks and key competitors.
    4.  Analyze the impact of depreciation and amortization on performance.
    5.  Evaluate capital intensity and asset efficiency.
    6. Assess the relationship between operating margin and investment cycles.
    7. Identify opportunities for capital efficiency improvement.

Net Profit Margin Percentage
 Methodology:
    1. Calculate net profit margin percentage (net profit divided by revenue).
    2.  Track net profit margin trends over multiple periods.
    3.  Compare net profit margins to industry benchmarks and key competitors.
    4.  Analyze the impact of financing costs, tax strategies, and extraordinary items.
    5.  Evaluate the quality and sustainability of net profit.
    6.  Assess the relationship between net profit and cash generation.
    7.  Identify opportunities for financial structure optimization.

    
Profit Growth Trends
 Methodology:
    1.Calculate growth rates for different profit metrics:
    2.  Gross profit
    3.  EBITDA
    4.  Operating profit
    5.  Net profit
    6.  Compare profit growth rates to revenue growth rates.
    7.  Analyze profit growth consistency and volatility.
    8.  Evaluate profit growth sustainability and drivers.
    9.  Assess the relationship between profit growth and investment.
    10. Compare profit growth to industry benchmarks and key competitors.


 Return and Capital Efficiency Rates
 Return metrics evaluate how effectively a segment utilizes invested capital to generate
 profits, providing insights into management effectiveness, competitive advantage, and
 value creation.
 Return on Equity (ROE)
 Methodology:
    1. Calculate ROE (net income divided by average shareholders' equity).
    2.  Track ROE trends over multiple periods.
    3.  Compare ROE to industry benchmarks and key competitors.
    4. Decompose ROE using the DuPont analysis:
    5.  Net profit margin (net income/revenue)
    6.  Asset turnover (revenue/total assets)
    7.  Financial leverage (total assets/equity)
    8.  Analyze which components are driving ROE changes.
    9.  Evaluate the sustainability of current ROE levels.
    10. Assess the relationship between ROE and growth investments.    

    
 Return on Capital Employed (ROCE)
 Methodology:
    1. Calculate ROCE (EBIT divided by capital employed, where capital employed equals total assets minus current liabilities).
    2. Track ROCE trends over multiple periods.
    3. Compare ROCE to industry benchmarks, key competitors, and the weighted average cost of capital (WACC).
    4. Analyze factors driving ROCE performance:
    5. Operating margin
    6. Capital turnover
    7. Working capital management
    8. Fixed asset utilization
    9. Evaluate ROCE across different business units or product lines.
    10. Assess the relationship between ROCE and investment decisions.

    
 Return on Invested Capital (ROIC)
 Methodology:
    1. Calculate ROIC (NOPAT divided by invested capital, where NOPAT is net operating profit after tax and invested capital is total assets minus non-interest-bearing current liabilities).
    2. Track ROIC trends over multiple periods.
    3. Compare ROIC to industry benchmarks, key competitors, and the weighted average cost of capital (WACC).
    4. Analyze the spread between ROIC and WACC as a measure of value creation.
    5. Evaluate the sustainability of ROIC advantages or disadvantages.
    6. Assess the relationship between ROIC and competitive positioning.
    7. Analyze ROIC for different business units or investment categories.

    
 Asset Turnover Ratio
 Methodology:
    1.  Calculate asset turnover ratio (revenue divided by average total assets).
    2. Track asset turnover trends over multiple periods.
    3. Compare asset turnover to industry benchmarks and key competitors.
    4.  Analyze asset turnover for different asset categories:
    5.  Fixed assets
    6.  Inventory
    7.  Accounts receivable
    8.  Other major asset classes
    9.  Evaluate the relationship between asset turnover and profitability.
    10. Assess the impact of investment cycles on asset turnover.
    11. Identify opportunities for asset utilization improvement.


 Working Capital Turnover
 Methodology:
    1. Calculate working capital turnover (revenue divided by average working capital).
    2. Track working capital turnover trends over multiple periods.
    3. Compare working capital turnover to industry benchmarks and key competitors.
    4. Analyze individual working capital components:
    5. Days inventory outstanding
    6. Days sales outstanding
    7. Days payables outstanding
    8. Cash conversion cycle
    9. Evaluate seasonal patterns in working capital requirements.
    10. Assess the relationship between working capital efficiency and growth.
    11. Identify opportunities for working capital optimization.

    
Cash Flow Analysis
 Cash flow analysis examines a segment's ability to generate cash from operations, its
 investment requirements, and its overall financial sustainability beyond accounting
 profits.
 Operating Cash Flow (OCF)
 Methodology:
    1. Calculate operating cash flow using direct or indirect method.
    2.  Track OCF trends over multiple periods.
    3. Compare OCF to industry benchmarks and key competitors.
    4. Analyze the relationship between net income and OCF.
    5. Evaluate the impact of working capital changes on OCF.
    6. Assess the quality and sustainability of OCF.
    7. Identify factors causing volatility or predictability in OCF.

    
Free Cash Flow (FCF)
 Methodology:
    1. Calculate free cash flow (OCF minus capital expenditures).
    2. Track FCF trends over multiple periods.
    3. Compare FCF to industry benchmarks and key competitors.
    4. Analyze the relationship between FCF and growth investments.
    5. Evaluate the impact of maintenance versus growth capex on FCF.
    6. Assess the sustainability of current FCF levels.
    7. Identify opportunities to improve FCF generation.

    
 FCF Conversion Rate
 Methodology:
    1. Calculate FCF conversion rate (FCF divided by net income or EBITDA).
    2. Track FCF conversion trends over multiple periods.
    3. Compare FCF conversion to industry benchmarks and key competitors.
    4. Analyze factors affecting conversion efficiency:
    5. Working capital management
    6. Capital expenditure requirements
    7. Non-cash expenses
    8. Tax strategies
    9. Evaluate differences in conversion rates across business cycles.
    10. Assess the relationship between FCF conversion and growth rates.

    
 FCF Margin
 Methodology:
    1. Calculate FCF margin (FCF divided by revenue).
    2. Track FCF margin trends over multiple periods.
    3. Compare FCF margin to industry benchmarks and key competitors.
    4. Analyze the relationship between FCF margin and other profitability metrics.
    5. Evaluate the impact of capital intensity on FCF margin.
    6. Assess the sustainability of current FCF margin levels.
    7. Identify strategies to improve FCF margin performance.

    
Cost Structure and Operating Leverage
 This analysis examines the composition of a segment's cost base and how it responds to
 changes in volume, providing insights into operational efficiency, scalability, and profit
 sensitivity.
 Cost of Goods Sold (COGS) as Percentage of Revenue
 Methodology:
    1. Calculate COGS as a percentage of revenue.
    2.  Track COGS percentage trends over multiple periods.
    3. Compare COGS percentage to industry benchmarks and key competitors.
    4. Break down COGS into major components:
    5. Raw materials
    6. Direct labor
    7. Manufacturing overhead
    8. Other direct costs
    9. Analyze factors driving COGS changes:
    10. Input price fluctuations
    11. Production efficiency
    12. Scale effects
    13. Product mix shifts
    14. Evaluate COGS differences across product lines or business units.


Employee Cost as Percentage of Revenue
 Methodology:
    1. Calculate employee costs as a percentage of revenue.
    2. Track employee cost percentage trends over multiple periods.
    3. Compare employee cost percentage to industry benchmarks and key competitors.
    4. Analyze employee cost components:
    5. Salaries and wages
    6. Benefits and payroll taxes
    7. Bonuses and incentives
    8. Temporary or contract labor
    9. Evaluate employee productivity metrics:
    10. Revenue per employee
    11. Profit per employee
    12. Value added per employee
    13. Assess the relationship between employee costs and growth or innovation.


Selling, General and Administrative Expenses (SG&A) to Sales Ratio
 Methodology:
    1. Calculate SG&A as a percentage of revenue.
    2. Track SG&A percentage trends over multiple periods.
    3. Compare SG&A percentage to industry benchmarks and key competitors.
    4. Break down SG&A into major components:
    5. Sales and marketing expenses
    6. Research and development
    7. General administrative costs
    8. Other overhead expenses
    9. Analyze factors driving SG&A changes:
    10. Growth investments
    11. Organizational complexity
    12. Efficiency initiatives
    13. Scale effects
    14. Evaluate SG&A differences across business units or regions.


 Other Expenses Percentage
 Methodology:
    1. Identify and categorize significant expenses not captured in COGS or SG&A.
    2. Calculate these expenses as a percentage of revenue.
    3. Track expense percentage trends over multiple periods.
    4. Compare expense percentages to industry benchmarks where available.
    5. Analyze factors driving changes in these expense categories.
    6. Evaluate the strategic importance and controllability of these expenses.
    7. Identify opportunities for expense optimization or strategic investment.

    
 Break-Even Analysis
 Methodology:
    1. Classify costs as fixed or variable.
    2. Calculate total fixed costs.
    3. Calculate total variable costs.
    4. Determine sales price per unit.
    5. Calculate contribution margin (sales price per unit minus variable cost per unit).
    6. Determine break-even point (fixed costs divided by contribution margin percentage).
    7. Calculate contribution margin (revenue minus variable costs).

    
 Operating Leverage
 Methodology:
    1. Calculate degree of operating leverage (percentage change in operating profit divided by percentage change in revenue).
    2. Track operating leverage trends over multiple periods.
    3. Compare operating leverage to industry benchmarks and key competitors.
    4. Analyze the fixed versus variable cost structure.
    5. Evaluate operating leverage differences across business units or product lines.
    6. Assess the relationship between operating leverage and profit volatility.
    7. Identify strategies to optimize operating leverage for current business conditions.

    
 Balance Sheet Health
 Balance sheet analysis evaluates a segment's financial structure, liquidity, and overall financial resilience, providing insights into long-term sustainability and risk profile.
 Debt to Equity Ratio
 Methodology:
    1. Calculate debt to equity ratio (total debt divided by shareholders' equity).
    2. Track debt to equity trends over multiple periods.
    3. Compare debt to equity to industry benchmarks and key competitors.
    4. Analyze debt composition:
    5. Short-term versus long-term debt
    6. Fixed versus floating rate
    7. Secured versus unsecured
    8. Currency denomination
    9. Evaluate the strategic rationale for the current capital structure.
    10. Assess the relationship between leverage and financial flexibility.

    
 Net Debt to EBITDA
 Methodology:
    1. Calculate net debt to EBITDA ratio (total debt minus cash divided by EBITDA).
    2.  Track net debt to EBITDA trends over multiple periods.
    3. Compare net debt to EBITDA to industry benchmarks and key competitors.
    4. Analyze factors driving changes in the ratio:
    5. EBITDA performance
    6. Debt issuance or repayment
    7. Cash accumulation or deployment
    8. Evaluate the ratio relative to debt covenant requirements.
    9. Assess the segment's debt capacity for future investments or acquisitions.

    
Interest Coverage Ratio (ICR)
 Methodology:
    1. Calculate interest coverage ratio (EBIT divided by interest expense).
    2.  Track ICR trends over multiple periods.
    3. Compare ICR to industry benchmarks and key competitors.
    4. Analyze factors driving changes in the ratio:
    5. EBIT performance
    6. Interest rate fluctuations
    7. Debt level changes
    8. Evaluate the ratio relative to debt covenant requirements.
    9. Assess the segment's vulnerability to interest rate increases.
    10. Identify strategies to improve interest coverage.
 
    
Current Ratio (CR)
 Methodology:
    1. Calculate current ratio (current assets divided by current liabilities).
    2. Track current ratio trends over multiple periods.
    3. Compare current ratio to industry benchmarks and key competitors.
    4. Analyze components of current assets and liabilities:
    5. Cash and cash equivalents
    6. Accounts receivable
    7. Inventory
    8. Short-term investments
    9. Accounts payable
    10. Short-term debt
    11. Other current liabilities
    12. Evaluate seasonal patterns in the current ratio.
    13. Assess the relationship between the current ratio and operational efficiency.


Quick Ratio (QR)
 Methodology:
    1. Calculate quick ratio ((current assets minus inventory) divided by current liabilities).
    2. Track quick ratio trends over multiple periods.
    3. Compare quick ratio to industry benchmarks and key competitors.
    4. Analyze the gap between current ratio and quick ratio as an indicator of inventory dependence.
    5. Evaluate the segment's ability to meet short-term obligations without inventory liquidation.
    6. Assess seasonal patterns in the quick ratio.
    7. Identify strategies to improve liquidity position.

    
Leverage Trends
 Methodology:
    1. Analyze multiple leverage metrics over time:
    2. Debt to equity
    3. Net debt to EBITDA
    4. Total liabilities to total assets
    5. Financial debt to capital
    6. Evaluate changes in leverage relative to business cycle position.
    7. Compare leverage trends to industry peers and sector evolution.
    8.  Assess management's stated leverage targets and policies.
    9. Analyze the relationship between leverage changes and strategic initiatives.
    10. Evaluate the impact of leverage on financial flexibility and risk profile.


Capex and Investment Intensity
 This analysis examines a segment's capital expenditure patterns and investment
 requirements, providing insights into growth strategy, maintenance needs, and long
term competitiveness.
Capital Expenditure to Revenue Ratio
 Methodology:
    1. Calculate capex to revenue ratio (capital expenditures divided by revenue).
    2. Track capex to revenue ratio trends over multiple periods.
    3. Compare capex to revenue ratio to industry benchmarks and key competitors.
    4. Analyze capex by category:
    5. Maintenance versus growth capex
    6. Capacity expansion
    7. Efficiency improvements
    8. Regulatory compliance
    9. Digital transformation
    10. Evaluate the relationship between capex and subsequent performance improvements.
    11. Assess the timing and magnitude of investment cycles.


Capex CAGR
 Methodology:
    1. Calculate compound annual growth rate of capital expenditures over multiple timeframes.
    2.  Compare capex CAGR to revenue and profit growth rates.
    3. Analyze factors driving changes in capex growth:
    4. Strategic shifts
    5. Technology adoption
    6. Competitive pressures
    7. Regulatory requirements
    8. Evaluate the sustainability of current capex growth trends.
    9. Assess the relationship between capex growth and market share or competitive position changes.

    
 R&D Spend to Revenue Ratio
 Methodology:
    1. Calculate R&D to revenue ratio (R&D expenditures divided by revenue).
    2.  Track R&D ratio trends over multiple periods.
    3.  Compare R&D ratio to industry benchmarks and key competitors.
    4.  Analyze R&D allocation across different initiatives:
    5.  Product development
    6.  Process innovation
    7.  Basic research
    8.  Applied development
    9.  Evaluate R&D productivity metrics:
    10.  New product revenue percentage
    11.  Patent generation
    12.  Time to market
    13.  R&D ROI estimates
    14.  Assess the relationship between R&D investment and competitive differentiation.

Depreciation Trends
 Methodology:
    1. Analyze depreciation as a percentage of revenue and fixed assets.
    2. Track depreciation trend changes over multiple periods.
    3. Compare depreciation metrics to industry benchmarks and key competitors.
    4. Evaluate the relationship between capex and subsequent depreciation changes.
    5. Assess the impact of depreciation policies on reported profitability.
    6. Analyze asset age and replacement cycle implications.
    7. Identify potential future depreciation changes based on recent investments.

 15. Valuation
 Relative Valuation
 Relative valuation assesses a segment's value by comparing its financial metrics to
 similar companies or industry benchmarks, providing context for how the market might
 value the segment if it were a standalone entity.
 Price to Earnings Ratio (P/E)
 The Price to Earnings ratio is one of the most widely used valuation metrics, comparing a
 company's share price to its earnings per share. For segment analysis, this requires
 constructing implied P/E ratios based on comparable companies.
 Methodology:
    1. Identify a set of pure-play comparable companies that closely match the segment's business model, growth profile, and risk characteristics.
    2.  Collect current and historical P/E ratios for these comparable companies.
    3.  Adjust for differences in growth rates, margins, and business mix using regression analysis or qualitative adjustments.
    4.  Develop a justified P/E range for the segment based on:
    5. Comparable company average and median P/E
    6. Historical P/E ranges through different market cycles
    7. Growth-adjusted P/E (PEG ratio) comparisons
    8. Segment-specific risk factors
    9. Apply the justified P/E range to the segment's earnings to estimate implied value.
    10. Conduct sensitivity analysis using different earnings projections and P/E scenarios.

 Price to Book Ratio (P/B)
 The Price to Book ratio compares a company's market value to its book value, providing
 insights into how the market values the company's net assets. This metric is particularly
 useful for asset-intensive businesses or those with significant tangible assets.
 Methodology:
    1. Identify appropriate comparable companies for P/B analysis.
    2. Collect current and historical P/B ratios for these comparable companies.
    3. Analyze the relationship between P/B ratios and key performance metrics:
    4. Return on equity (ROE)
    5. Growth rates
    6. Risk profile
    7. Asset quality
    8. Adjust for differences in accounting policies that might affect book value comparability.
    9. Develop a justified P/B range for the segment based on:
    10. Comparable company average and median P/B
    11. ROE-adjusted P/B comparisons
    12. Historical P/B ranges through different market cycles
    13. Segment-specific factors affecting asset valuation
    14. Apply the justified P/B range to the segment's book value to estimate implied value.
    15. Conduct sensitivity analysis using different book value adjustments and P/B scenarios.


Enterprise Value (EV)
 Enterprise Value represents the total value of a business, including both equity and debt,
 minus cash. For segment analysis, calculating implied enterprise value provides a
 foundation for multiple-based valuation approaches.
 Methodology:
    1. Estimate the segment's standalone enterprise value components:
    2.  Allocate corporate debt based on appropriate metrics (e.g., EBITDA contribution, asset base)
    3.  Identify segment-specific debt or liabilities
    4.  Allocate cash based on operational requirements
    5.  Adjust for pension obligations, operating leases, and other off-balance sheet items
    6.  Compare the constructed enterprise value to segment financial metrics.
    7.  Analyze how the segment's implied enterprise value would change under different capital structure scenarios.
    8.  Evaluate the impact of synergies or dissynergies on enterprise value if the segment were standalone.
    9.  Assess the relationship between enterprise value and replacement cost of assets.
    10. Develop multiple enterprise value scenarios based on different assumptions.


 EV to EBITDA Ratio
 The EV/EBITDA ratio is widely used for comparing companies with different capital
 structures or depreciation policies, making it particularly useful for segment analysis
 within diversified companies.
 Methodology:
    1. Identify appropriate comparable companies for EV/EBITDA analysis.
    2.  Collect current and historical EV/EBITDA ratios for these comparable companies.
    3.  Analyze the relationship between EV/EBITDA ratios and key performance metrics:
    4.  Growth rates
    5.  EBITDA margins
    6.  Capital intensity
    7.  Return on invested capital
    8.  Develop a justified EV/EBITDA range for the segment based on:
    9.  Comparable company average and median EV/EBITDA
    10.  Growth-adjusted EV/EBITDA comparisons
    11.  Historical EV/EBITDA ranges through different market cycles
    12.  Segment-specific risk and growth factors
    13.  Apply the justified EV/EBITDA range to the segment's EBITDA to estimate implied enterprise value.
    14. Conduct sensitivity analysis using different EBITDA projections and multiple scenarios.

EV to Sales Ratio
 The EV/Sales ratio is useful for valuing segments with negative or volatile earnings, high
 growth potential, or those undergoing significant transitions. It provides a revenue
based perspective on valuation.
 Methodology:
    1. Identify appropriate comparable companies for EV/Sales analysis.
    2.  Collect current and historical EV/Sales ratios for these comparable companies.
    3.  Analyze the relationship between EV/Sales ratios and key performance metrics:
    4.  Profit margins
    5.  Growth rates
    6.  Revenue quality and predictability
    7.  Business model (subscription, transaction, etc.)
    8.  Develop a justified EV/Sales range for the segment based on:
    9.  Comparable company average and median EV/Sales
    10. Margin-adjusted EV/Sales comparisons
    11. Historical EV/Sales ranges through different market cycles
    12. Segment-specific factors affecting revenue valuation
    13. Apply the justified EV/Sales range to the segment's revenue to estimate implied enterprise value.
    14. Conduct sensitivity analysis using different revenue projections and multiple scenarios.


 Price/Earnings to Growth Ratio (PEG)
 The PEG ratio adjusts the P/E ratio for expected growth rates, providing a growth
normalized valuation metric that is particularly useful for comparing segments with
 different growth profiles.
 Methodology:
    1. Calculate PEG ratios for the segment and comparable companies (P/E ratio divided by expected earnings growth rate).
    2.  Analyze historical PEG ratios and their relationship to actual delivered growth.
    3.  Evaluate the quality and sustainability of projected growth rates.
    4.  Adjust for differences in risk profiles that might affect appropriate PEG levels.
    5.  Develop a justified PEG range for the segment based on:
    6.  Comparable company average and median PEG
    7.  Historical PEG ranges through different market cycles
    8.  Segment-specific growth quality factors
    9.  Risk-adjusted growth considerations
    10. Apply the justified PEG analysis to estimate an appropriate P/E multiple given the segment's growth profile.
    11. Conduct sensitivity analysis using different growth projections and PEG scenarios.

 Discounted Cash Flow (DCF) Analysis
 Discounted Cash Flow analysis determines a segment's intrinsic value by projecting
 future cash flows and discounting them to present value, providing a fundamental
 valuation approach that can capture segment-specific growth, profitability, and risk
 characteristics.
 Cash Flow Projections
 Methodology:
    1. Develop detailed cash flow projections for an explicit forecast period (typically 5-10 years):
    2.  Revenue growth by product line or geography
    3.  Margin evolution based on scale, mix, and efficiency initiatives
    4.  Working capital requirements
    5.  Capital expenditure needs
    6.  Tax considerations
    7.  Support projections with:
    8.  Historical performance analysis
    9.  Management guidance and strategic plans
    10.  Industry research and market forecasts
    11.  Competitive positioning assessment
    12.  Technological and regulatory trends
    13.  Create multiple scenarios (base, upside, downside) with different assumptions.
    14.  Ensure internal consistency across projection components.
    15.  Validate key assumptions against industry benchmarks and historical patterns.
    16.  Incorporate specific growth initiatives and efficiency programs with realistic timelines.

 Discount Rate Determination
 Methodology:
    1. Calculate an appropriate weighted average cost of capital (WACC):
    2.  Determine cost of equity using Capital Asset Pricing Model (CAPM):
    3.  Risk-free rate based on long-term government bonds
    4.  Equity risk premium based on historical data and forward expectations
    5.  Beta derived from comparable companies and adjusted for segment-specific factors
    6.  Determine cost of debt:
    7.  Current yield on comparable debt instruments
    8.  Segment-specific credit risk assessment
    9.  Tax shield effect based on applicable tax rates
    10. Establish target capital structure based on industry norms and segment characteristics
    11. Adjust the WACC for segment-specific factors:
    12. Size premium for smaller segments
    13. Country risk premium for international operations
    14. Specific risk factors not captured in beta
    15. Develop multiple discount rate scenarios to reflect different risk assumptions.
    16. Validate the final discount rate range against industry benchmarks and historical returns.


 Terminal Value Calculation
 Methodology:
    1. Determine the appropriate terminal value methodology:
    2.  Perpetuity growth method (Gordon Growth Model)
    3.  Exit multiple approach
    4.  Liquidation value (if applicable)
    5.  For perpetuity growth method:
    6.  Establish sustainable long-term growth rate based on:
    7.  Industry maturity and growth potential
    8.  GDP growth in relevant markets
    9.  Inflation expectations
    10.  Competitive dynamics and market share potential
    11.  Ensure terminal year cash flow represents a normalized, sustainable level
    12.  For exit multiple approach:
    13.  Select appropriate multiple (typically EV/EBITDA)
    14.  Base multiple on historical averages through full market cycles
    15.  Adjust for expected industry evolution and segment positioning
    16.  Develop multiple terminal value scenarios to reflect different long-term outcomes.
    17.  Validate terminal value reasonableness through:
    18.  Implied growth rates and returns on capital
    19.  Percentage of total value represented by terminal value
    20.  Comparison to current trading multiples


Valuation Synthesis
 Methodology:
    1. Calculate present value of projected cash flows using the determined discount rate.
    2. Calculate present value of terminal value.
    3. Sum these components to determine enterprise value.
    4. Adjust enterprise value for:
    5. Net debt
    6. Non-operating assets
    7. Contingent liabilities
    8. Minority interests
    9. Other relevant items
    10. Develop a valuation range based on different scenarios and sensitivity analyses.
    11. Compare DCF valuation results with relative valuation approaches.
    12. Reconcile differences between valuation methodologies.
    13. Identify key value drivers and risks based on sensitivity analysis.


16. Strategic Intelligence Layer
 Globalization Readiness
 Globalization readiness assesses a segment's ability to expand internationally and
 compete effectively in global markets, providing insights into growth potential beyond
 domestic boundaries.
 Export Potential
 Methodology:
    1. Analyze the segment's current export performance:
    2.  Export revenue as percentage of total revenue
    3.  Export growth rates compared to domestic growth
    4.  Geographic distribution of exports
    5.  Export market share in key countries
    6.  Evaluate product or service suitability for international markets:
    7.  Degree of localization required
    8.  Regulatory compliance requirements
    9.  Cultural adaptation needs
    10.  Competitive differentiation in target markets
    11.  Assess operational capabilities for international expansion:
    12.  International supply chain infrastructure
    13.  Distribution partnerships or channels
    14.  Local market knowledge and relationships
    15.  Service and support capabilities
    16.  Identify high-potential export markets based on:
    17.  Market size and growth projections
    18.  Competitive landscape
    19.  Regulatory environment
    20.  Cultural and business fit
    21.  Existing presence or relationships
    22.  Develop export potential scenarios with timeline and investment requirements.

    
 Foreign Exchange (FX) Sensitivity
 Methodology:
    1. Analyze the segment's current FX exposure:
    2.  Revenue and cost currency mix
    3. Natural hedges in the business model
    4. Net exposure by currency
    5. Historical impact of currency fluctuations
    6. Evaluate FX risk management practices:
    7. Hedging strategies and effectiveness
    8. Pricing policies for currency fluctuations
    9. Treasury management capabilities
    10. Reporting and monitoring systems
    11. Conduct sensitivity analysis of financial performance under different FX scenarios:
    12. Impact on revenue, margins, and earnings
    13. Cash flow implications
    14. Competitive positioning effects
    15. Assess strategic options for reducing FX vulnerability:
    16. Geographic diversification of revenue and costs
    17. Local manufacturing or sourcing
    18. Pricing strategies and contract structures
    19. Financial hedging optimization


 Innovation Index
 The Innovation Index evaluates a segment's ability to generate, adopt, and
 commercialize innovations, providing insights into long-term competitiveness and
 growth potential.
Research & Development (R&D)
 Methodology:
    1. Analyze R&D investment patterns:
    2.  R&D spending as percentage of revenue
    3.  R&D growth rates compared to revenue growth
    4.  R&D allocation across different initiatives
    5.  Comparison to industry benchmarks and competitors
    6.  Evaluate R&D productivity metrics:
    7.  New product revenue percentage
    8.  Time to market for new developments
    9.  Success rate of R&D projects
    10.  Return on R&D investment estimates
    11.  Assess R&D organizational capabilities:
    12.  Technical talent depth and specialization
    13.  Research partnerships and ecosystem engagement
    14.  Knowledge management systems
    15.  Innovation culture and incentives
    16.  Analyze alignment between R&D priorities and strategic objectives:
    17.  Market-driven versus technology-driven approach
    18.  Balance between incremental and disruptive innovation
    19.  Short-term versus long-term focus
    20.  Core versus adjacent market exploration

    
Intellectual Property (IP)
 Methodology:
    1. Analyze the segment's IP portfolio:
    2.  Patent count and quality metrics
    3.  Patent growth rate and citation impact
    4.  Trademark and copyright assets
    5.  Trade secrets and proprietary know-how
    6.  Evaluate IP strategic positioning:
    7.  Coverage of core technologies and products
    8.  Defensive versus offensive IP strategy
    9.  White space opportunities
    10.  Freedom to operate risks
    11.  Assess IP management capabilities:
    12.  IP generation processes
    13.  Protection and enforcement practices
    14.  Licensing and monetization approach
    15.  IP portfolio maintenance and pruning
    16.  Analyze competitive IP landscape:
    17.  Relative IP strength versus key competitors
    18.  Litigation environment and history
    19.  Technology adjacencies and convergence risks
    20.  Potential IP acquisition targets

Innovation Pipeline
 Methodology:
    1. Inventory current innovation initiatives across categories:
    2.  Product or service innovations
    3.  Process innovations
    4.  Business model innovations
    5.  Customer experience innovations
    6.  Evaluate the innovation pipeline structure:
    7.  Stage-gate process effectiveness
    8.  Balance across different time horizons (short, medium, long-term)
    9.  Risk profile distribution (incremental to disruptive)
    10.  Resource allocation across initiatives
    11.  Assess pipeline health metrics:
    12.  Number of initiatives by development stage
    13.  Progression and attrition rates
    14.  Time in stage metrics
    15.  Expected value and probability-weighted returns
    16.  Analyze innovation portfolio management practices:
    17.  Decision-making processes and criteria
    18.  Resource allocation mechanisms
    19.  Performance measurement systems
    20.  Learning and adaptation from failures


ESG Alignment
 ESG alignment evaluates how well a segment addresses environmental, social, and
 governance factors, providing insights into sustainability, risk exposure, and long-term
 value creation potential.
 Environmental Impact
 Methodology:
    1. Analyze the segment's environmental footprint:
    2.  Carbon emissions (Scope 1, 2, and 3)
    3.  Energy consumption and mix
    4.  Water usage and impact
    5.  Waste generation and management
    6.  Biodiversity impact
    7.  Evaluate environmental management systems:
    8.  Policies and governance
    9.  Targets and commitments
    10.  Measurement and reporting practices
    11.  Certification and compliance status
    12.  Assess product environmental attributes:
    13.  Life cycle environmental impact
    14.  Circular economy integration
    15.  Sustainable design principles
    16.  Green product certifications
    17.  Analyze environmental strategy and initiatives:
    18.  Decarbonization roadmap
    19.  Resource efficiency programs
    20.  Sustainable sourcing practices
    21.  Environmental innovation focus

Social Responsibility
 Methodology:
    1. Analyze the segment's social impact areas:
    2. Labor practices and working conditions
    3. Diversity, equity, and inclusion
    4. Community engagement and impact
    5. Product safety and responsibility
    6. Data privacy and security
    7. Human rights in operations and supply chain
    8. Evaluate social management systems:
    9. Policies and governance
    10. Targets and commitments
    11. Measurement and reporting practices
    12. Certification and compliance status
    13. Assess stakeholder relationships:
    14. Employee engagement and turnover
    15. Customer satisfaction and trust
    16. Supplier relationships and standards
    17. Community perception and engagement
    18. Regulatory relationships
    19. Analyze social strategy and initiatives:
    20. Workforce development programs
    21. Diversity and inclusion efforts
    22. Community investment approach
    23. Product responsibility initiatives


 Governance Quality
 Methodology:
    1. Analyze the segment's governance structure:
    2.  Leadership team composition and capabilities
    3.  Decision-making processes and authorities
    4.  Performance management systems
    5.  Risk management framework
    6.  Compliance programs
    7.  Evaluate governance practices:
    8.  Transparency and disclosure
    9.  Accountability mechanisms
    10.  Stakeholder engagement
    11.  Ethics and integrity systems
    12.  Incentive alignment
    13.  Assess governance effectiveness:
    14.  Decision quality and timeliness
    15.  Resource allocation efficiency
    16.  Risk anticipation and management
    17.  Compliance track record
    18.  Adaptability to changing conditions
    19.  Analyze governance evolution and improvement initiatives:
    20.  Recent governance changes
    21.  Ongoing enhancement efforts
    22.  Benchmarking and best practice adoption
    23.  Response to governance failures or challenges

    
 Changing Preferences
 Methodology:
    1. Analyze current customer preference trends relevant to the segment:
    2.  Product or service attribute priorities
    3.  Brand value drivers
    4.  Price sensitivity patterns
    5.  Quality expectations
    6.  Experience requirements
    7.  Evaluate the segment's alignment with emerging preferences:
    8.  Product portfolio fit with trend direction
    9.  Brand positioning relative to evolving values
    10.  Pricing strategy sustainability
    11.  Experience delivery capabilities
    12.  Assess the segment's preference monitoring systems:
    13.  Customer research methodologies
    14.  Feedback collection mechanisms
    15.  Trend analysis capabilities
    16.  Leading indicator tracking
    17.  Analyze the segment's adaptability to preference changes:
    18.  Product development agility
    19.  Marketing responsiveness
    20.  Business model flexibility
    21.  Historical adaptation examples

 Demographic Trends
 Methodology:
    1. Analyze demographic trends in the segment's key markets:
    2. Age distribution shifts
    3. Household composition changes
    4. Income and wealth distribution
    5. Geographic population movements
    6. Education and employment patterns
    7. Analyze the segment's customer base demographics:
    8. Current customer demographic profile
    9. Customer acquisition trends by demographic
    10. Retention patterns across demographics
    11. Lifetime value by demographic segment
    12. Assess the segment's demographic strategy:
    13. Target demographic focus
    14. Multi-generational approach
    15. Geographic expansion priorities
    16. Income segment positioning
    17. Analyze product and marketing alignment with demographic evolution:
    18. Product design for different demographic needs
    19. Marketing channel effectiveness by demographic
    20. Pricing strategy across demographic segments
    21. Brand relevance across age cohorts


Digital Adoption
 Methodology:
   1. Analyze digital adoption trends relevant to the segment:`
   2.  E-commerce penetration
   3.  Mobile usage patterns
   4.  Social media engagement
   5.  Digital service expectations
   6.  Technology integration in customer journey
   7.  Evaluate the segment's digital capabilities:
   8.  Digital channel presence and effectiveness
   9.  Mobile optimization
   10.  Social media strategy
   11.  Digital customer experience
   12.  Data collection and utilization
   13.  Assess the segment's digital transformation initiatives:
   14.  Digital roadmap and priorities
   15.  Investment in digital capabilities
   16.  Organizational alignment for digital
   17.  Digital talent acquisition and development
   18.  Analyze competitive digital positioning:
   19.  Digital capabilities relative to traditional competitors
   20.  Vulnerability to digital-native disruptors
   21.  Partnership opportunities in digital ecosystem
   22.  Digital innovation pipeline

 Mergers & Acquisitions
 Methodology:
   1. Analyze the segment's M&A strategy and history:
   2. Historical acquisition pattern and performance
   3. Stated M&A priorities and criteria
   4. Integration capabilities and track record
   5. Financial capacity for acquisitions
   6. Evaluate potential acquisition opportunities:
   7. Target identification in priority areas
   8. Strategic fit assessment
   9. Valuation and financial impact analysis
   10. Integration complexity evaluation
   11. Assess potential acquisition risks:
   12. Target availability and willingness
   13. Competitive bidding dynamics
   14. Regulatory approval challenges
   15. Integration execution risks
   16. Analyze the segment as a potential acquisition target:
   17. Strategic attractiveness to potential acquirers
   18. Valuation as standalone entity
   19. Synergy potential with likely acquirers
   20. Defensive positioning and options

 Partnerships
 Methodology:
   1. Analyze the segment's partnership strategy and portfolio:
   2. Current strategic partnerships and performance
   3. Partnership objectives and selection criteria
   4. Partnership management capabilities
   5. Resource allocation to partnership initiatives
   6. Evaluate potential partnership opportunities:
   7. Partner identification in priority areas
   8. Strategic fit and complementarity assessment
   9. Value creation and sharing analysis
   10. Implementation complexity evaluation
   11. Assess potential partnership risks:
   12. Partner alignment and commitment
   13. Competitive implications
   14. Intellectual property and knowledge transfer
   15. Dependency and control issues
   16. Analyze partnership models and structures:
   17. Joint ventures
   18. Strategic alliances
   19. Licensing arrangements
   20. Co-development agreements
   21. Channel partnerships

 Major Initiatives
 Methodology:
   1. Inventory current and planned major strategic initiatives:
   2. Transformation programs
   3. Major product launches
   4. Geographic expansions
   5. Business model changes
   6. Significant investments
   7.  Evaluate initiative portfolio characteristics:
   8.  Strategic alignment and importance
   9.  Resource requirements and allocation
   10.  Risk profile and mitigation plans
   11.  Expected outcomes and success metrics
   12.  Timeline and milestone structure
   13.  Assess initiative execution capabilities:
   14.  Program management infrastructure
   15.  Resource adequacy and quality
   16.  Leadership commitment and sponsorship
   17.  Change management approach
   18.  Performance tracking and accountability
   19.  Analyze initiative interdependencies and sequencing:
   20.  Critical path identification
   21.  Resource competition between initiatives
   22.  Prerequisite relationships
   23.  Potential synergies or conflicts


Disaster/Event Trap
 Disaster/event trap analysis evaluates the segment's vulnerability to low-probability,
 high-impact events that could significantly disrupt operations or strategy, providing
 insights into resilience and contingency planning needs.
 Vulnerability Assessment
 Methodology:
   1. Identify potential disaster or event scenarios relevant to the segment:
   2.  Natural disasters (earthquakes, floods, hurricanes, etc.)
   3.  Public health crises
   4.  Geopolitical conflicts or trade disruptions
   5.  Cyber attacks or data breaches
   6.  Regulatory or legal actions
   7.  Reputational crises
   8.  Supply chain disruptions
   9.  Critical infrastructure failures
   10.  Evaluate the segment's exposure to each scenario:
   11.  Geographic concentration risks
   12.  Single points of failure
   13.  Critical dependencies
   14.  Historical vulnerability patterns
   15.  Assess potential impact of each scenario:
   16.  Operational disruption severity and duration
   17.  Financial impact magnitude
   18.  Reputational damage potential
   19.  Recovery time and cost estimates
   20.  Analyze vulnerability trends and emerging risks:
   21.  Climate change implications
   22.  Geopolitical tension evolution
   23.  Cyber threat landscape changes
   24.  Regulatory environment shifts

 Contingency Planning
 Methodology:
   1. Analyze the segment's disaster preparedness and response capabilities:
   2.  Business continuity plans
   3.  Crisis management protocols
   4.  Emergency response procedures
   5.  Recovery strategies and resources
   6.  Evaluate contingency plan coverage and quality:
   7.  Scenario comprehensiveness
   8.  Plan detail and practicality
   9.  Testing and simulation frequency
   10.  Update and maintenance processes
   11.  Assess organizational readiness for crisis response:
   12.  Leadership roles and responsibilities
   13.  Decision-making authorities
   14.  Communication protocols
   15.  Training and awareness
   16.  Analyze financial resilience mechanisms:
   17.  Insurance coverage adequacy
   18.  Cash reserves and liquidity access
   19.  Financial stress testing
   20.  Capital structure flexibility

17. Stress Simulation
 Stress simulation evaluates how a segment would perform under various adverse
 scenarios, providing insights into resilience, vulnerabilities, and contingency planning
 needs. This systematic approach to stress testing helps identify potential breaking
 points and mitigation strategies before crises occur.
Rate Hike/Liquidity Scenarios
 This analysis examines how a segment would perform in environments of rising interest
 rates or constrained liquidity, revealing financial vulnerabilities and funding risks.
 Methodology:
   1. Develop multiple interest rate scenarios:
   2. Gradual rate increases (e.g., 100, 200, 300 basis points over different timeframes)
   3. Rapid rate shock scenarios
   4. Yield curve shifts (flattening, steepening, inversion)
   5. Sector-specific credit spread widening
   6. Analyze direct financial impacts:
   7. Interest expense increases on variable rate debt
   8. Refinancing challenges for maturing debt
   9. Discount rate effects on pension obligations
   10. Capitalization rate impacts on real estate or asset values
   11. Investment portfolio mark-to-market effects
   12. Evaluate secondary business impacts:
   13. Customer demand sensitivity to interest rates
   14. Working capital financing costs
   15. Capital expenditure affordability
   16. Acquisition financing availability
   17. Competitor stress and industry dynamics
   18. Assess liquidity resilience:
   19. Cash reserve adequacy
   20. Debt maturity profile and refinancing needs
   21. Credit facility availability and covenants
   22. Cash conversion cycle flexibility
   23. Asset liquidity for emergency sales
   24. Develop mitigation strategies:
   25. Interest rate hedging opportunities
   26. Debt structure optimization
   27. Liquidity enhancement options
   28. Business model adjustments
   29. Contingency funding plans

Commodity Price Spike Impact
 This analysis evaluates how a segment would perform during significant commodity
 price volatility, revealing cost structure vulnerabilities and pricing power limitations.
 Methodology:
   1. Identify key commodity exposures:
   2.  Direct raw material inputs
   3.  Energy dependencies
   4.  Packaging materials
   5.  Transportation costs
   6.  Indirect exposures through suppliers
   7.  Develop commodity price scenarios:
   8.  Moderate price increases (e.g., 20%, 50%, 100%)
   9.  Severe shock scenarios (e.g., 200%+)
   10. Sustained versus temporary price spikes
   11. Correlated commodity movements
   12. Regional supply disruptions
   13.Analyze financial impacts: 
   14. Cost of goods sold increases
   15. Gross margin compression
   16. Working capital requirements
   17. Cash flow implications
   18. Potential inventory valuation effects
   19. Evaluate strategic responses:
   20. Pricing power and pass-through ability
   21. Substitution or reformulation options
   22. Hedging strategy effectiveness
   23. Supplier relationship leverage
   24. Vertical integration opportunities
   25.  Assess competitive implications:
   26.  Relative exposure compared to competitors
   27.  Industry pricing discipline
   28.  Market share shifts during previous commodity cycles
   29.  Customer switching behavior under price pressure

Policy Shift/ESG Regulation Changes
 This analysis examines how a segment would perform under significant regulatory
 changes, particularly related to environmental, social, and governance factors, revealing
 compliance risks and adaptation requirements.
 Methodology:
   1. Identify potential policy and regulatory scenarios:
   2.  Carbon pricing or emissions restrictions
   3.  Extended producer responsibility requirements
   4.  Labor practice regulations
   5.  Data privacy and security mandates
   6.  Corporate governance reforms
   7.  Industry-specific regulatory changes
   8.  Analyze compliance impacts:
   9.  Capital investment requirements
   10. Operating cost increases
   11. Product redesign needs
   12. Supply chain modifications
   13. Reporting and monitoring costs
   14. Potential penalties or liabilities
   15. Assess strategic implications:
   16. Market access restrictions
   17. Competitive positioning shifts
   18. Customer preference changes
   19. Reputation and brand effects
   20. Innovation opportunities
   21. Business model viability
   22. Assess adaptation capabilities:
   23. Regulatory monitoring systems
   24. Compliance management resources
   25. Technical capabilities for adaptation
   26. Financial capacity for required investments
   27. Organizational agility and change management
   28. Develop response strategies:
   29. Proactive compliance investments
   30. Product and process innovations
   31. Industry collaboration opportunities
   32. Stakeholder engagement approaches
   33. Policy influence strategies

 Global Recession Effects
 This analysis evaluates how a segment would perform during a significant economic
 downturn, revealing cyclical vulnerabilities and resilience factors.
 Methodology:
   1. Develop recession scenarios:
   2. Moderate downturn (e.g., 1-2% GDP contraction)
   3. Severe recession (e.g., 3-5% GDP contraction)
   4. Prolonged stagnation
   5. Industry-specific downturn
   6. Regional versus global recession
   7.  Analyze revenue impacts:
   8.  Historical sales sensitivity to economic cycles
   9.  Customer segment vulnerability differences
   10.  Geographic market resilience variations
   11.  Product line cyclicality differences
   12.  Pricing pressure expectations
   13.  Evaluate cost structure implications:
   14.  Fixed versus variable cost breakdown
   15.  Cost reduction flexibility
   16.  Operational leverage effects
   17.  Restructuring requirements and costs
   18.  Minimum viable operation assessment
   19.  Assess financial resilience:
   20.  Cash flow sustainability at different revenue levels
   21.  Debt covenant compliance
   22.  Liquidity runway
   23.  Credit rating implications
   24.  Capital expenditure flexibility
   25.  Develop downturn strategies:
   26.  Defensive positioning options
   27.  Opportunistic investments during weakness
   28.  Customer retention approaches
   29.  Talent preservation priorities
   30.  Recovery positioning preparation

Currency Volatility Impacts
 This analysis examines how a segment would perform during significant currency
 f
 luctuations, revealing translation and transaction exposures that could affect financial
 performance and competitive positioning.
 Methodology:
   1. Identify currency exposures:
   2.  Revenue currency mix
   3.  Cost currency mix
   4.  Asset and liability currency denomination
   5.  Competitor production locations
   6.  Customer and supplier currency sensitivities
   7.  Develop currency scenarios:
   8.  Major trading currency movements (e.g., 10%, 20%, 30%)
   9.  Emerging market currency crises
   10. Currency regime changes or controls
   11. Correlated currency movements
   12. Short-term volatility versus sustained shifts
   13. Analyze financial impacts:
   14. Translation effects on reported results
   15. Transaction exposure on cross-border activities
   16. Competitive positioning shifts
   17. Pricing strategy implications
   18. Local market affordability changes
   19. Evaluate hedging effectiveness:
   20. Natural hedge alignment
   21. Financial hedge coverage
   22. Hedging cost implications
   23. Residual exposures after hedging
   24. Hedge accounting implications
   25. Develop currency strategies:
   26. Operational hedging opportunities
   27. Pricing policy adjustments
   28. Geographic diversification benefits
   29. Local sourcing initiatives
   30. Financial hedging optimization
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
def google_search(query, max_pages=1):
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
        # Phase 1: Strategic Context & Positioning
f"Provide in-depth news and analysis on {company_name}"
f"What industry classification best captures the segment's activities? - Where does the segment sit within the industry value chain? - Does the segment name clearly communicate its business focus and market position? - Has the segment been renamed or rebranded recently, and if so, why? - How does the segment naming align with industry standard classifications? - Is the segment considered core or non-core to the company's future? - What level of corporate resources and attention does the segment receive? - How strategically important is this segment to its parent division and company? - What percentage of division revenue and profit does the segment represent?"

# Phase 2: Revenue Analysis Module  
f"Revenue Analysis Module"
# Phase 2: Profitability Analysis Module
f"Profitability Analysis Module"
# Phase 2: Capital Efficiency Module
f"Capital Efficiency Module"
# Phase 2: Cost Structure Analysis
f"Cost Structure Analysis"
# Phase 2: Investment Analysis
f"Investment Analysis"
# Phase 3: Financial Health Assessment
f"Financial Health Assessment"
# Phase 4: Relative Valuation Module
f"Relative Valuation Module"
# Phase 4: Intrinsic Valuation Module
f"Intrinsic Valuation Module"
# Phase 5: Competitive Positioning Module
f"Competitive Positioning Module"
# Phase 5: Risk Assessment Module  
f"Risk Assessment Module"
# Phase 5: Growth & Strategic Options Module
f"Growth & Strategic Options Module"
# Phase 6: Stress Testing Module
f"Stress Testing Module"
# Phase 6: Contingency Assessment Module  
f"Contingency Assessment Module"
# Phase 7: Investment Thesis Synthesis
f"Investment Thesis Synthesis"
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
    google_results = google_search(query, max_pages=1)

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

