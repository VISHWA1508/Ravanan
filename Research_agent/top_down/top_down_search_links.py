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
    Use the following methodology and key questions when creating your query:
Part I: Top- Down Investment Analysis Framework

# Comprehensive Investment Analysis Framework

1. Company Analysis  
2. Industry Analysis  
3. Conglomerate Industry Analysis  
4. Disaster Management (Industry)  
5. Investment Time Decision  
6. Company Qualitative Analysis  
7. Company Opportunity & Threat Analysis  
8. Company Quantitative Analysis  
9. Long-Term Logic  
10. Investment Decision Logic

# 1. Company Analysis

# Revenue Splitting by Industry

Understanding how a company's revenue is distributed across different industry segments provides crucial insights into its diversification strategy and potential vulnerabilities. This analysis helps identify which sectors contribute most significantly to the company's financial performance and how changes in specific industries might impact overall results.

# Methodology:

Methodology:1. Collect revenue data from the company's annual reports, investor presentations, and financial statements.2. Categorize revenue streams by industry segments as defined by the company or by standard industry classification systems.3. Calculate the percentage contribution of each industry segment to total revenue.4. Track changes in these percentages over at least 3- 5 years to identify trends.5. Compare the company's industry revenue distribution with industry peers to identify unique positioning or vulnerabilities.

# Top Products Revenue Growth Analysis

This analysis focuses on identifying which specific products or product lines are driving growth or experiencing decline. It helps determine whether the company's flagship offerings remain competitive or if newer products are becoming more significant contributors to revenue.

# Methodology:

Methodology:1. Identify the company's top products or product lines by revenue contribution.2. Collect historical revenue data for each product over at least 3- 5 years.3. Calculate year- over- year growth rates for each product.4. Analyze product lifecycle stages for each major offering.5. Identify products with accelerating or decelerating growth rates.6. Research market share data for each product within its respective category.

# Domestic vs International Business Distribution

Understanding the geographical distribution of a company's business provides insights into its exposure to regional economic conditions, currency fluctuations, and growth opportunities in different markets.

# Methodology:

Methodology:1. Collect revenue data by geographical region from financial statements and annual reports.2. Calculate the percentage contribution of domestic versus international markets.3. Further break down international revenue by major regions (e.g., North America, Europe, Asia- Pacific).4. Track changes in geographical distribution over at least 3- 5 years.5. Analyze growth rates in different regions to identify emerging market opportunities.6. Research the company's expansion strategies in different regions.

# Integration with Other Analysis Sections:

The findings from the Company Analysis section should inform subsequent analyses, particularly Industry Analysis and Company Qualitative Analysis. Understanding revenue distribution by industry, product, and geography provides the foundation for deeper investigation into the company's strategic positioning and future prospects.

# 2. Industry Analysis

# Industry Segmentation

Understanding the structure and segmentation of an industry provides critical context for evaluating a company's position and potential. Industry segmentation reveals how the market is divided among different types of products, services, customer groups, or business models.

# Methodology:

1. Identify the primary industry and its standard classification code (e.g., NAICS, SIC, GICS).  
2. Research industry reports from sources like IBISWorld, Statista, or industry associations to understand established segmentation approaches.  
3. Analyze the industry by product/service categories, customer types, geographic regions, price points, and distribution channels.  
4. Determine market share distribution across segments to identify dominant and niche areas.  
5. Identify emerging segments that may represent future growth opportunities.  
6. Map the company's position within these segments relative to competitors.

# Demand & Supply Trends

Demand & Supply TrendsAnalyzing the balance between demand and supply helps forecast industry pricing power, profitability, and competitive dynamics. This analysis identifies whether an industry is facing favorable tailwinds or challenging headwinds.

# Methodology:

Methodology:1. Collect historical data on industry production capacity, utilization rates, and inventory levels.2. Research demand drivers specific to the industry (e.g., consumer trends, technological adoption, regulatory changes).3. Analyze pricing trends as indicators of supply- demand balance.4. Identify capacity expansion plans across the industry.5. Research customer behavior changes that may impact demand patterns.6. Develop forecasts for how supply and demand may evolve over the next 3- 5 years.

# Cross-Industry Migration

Cross- Industry MigrationThis analysis examines how companies, customers, or value are moving between related industries. Understanding these migration patterns helps identify threats from adjacent industries and opportunities for expansion.

# Methodology:

Methodology:1. Identify adjacent or related industries with potential overlap.2. Research companies that have successfully crossed industry boundaries.3. Analyze technological developments that are blurring industry lines.4. Track customer spending patterns across related industries.5. Identify regulatory changes that may facilitate or hinder cross- industry movement.6. Evaluate the transferability of competitive advantages across industry boundaries.

# Total Addressable Market (TAM)

TAM analysis quantifies the maximum market potential for an industry or segment, providing context for growth projections and helping evaluate whether a company has room to expand significantly.

# Methodology:

Methodology:1. Define the boundaries of the market being analyzed (geographic scope, product categories, customer segments).2. Use top- down approaches: start with broad market statistics and narrow down to the specific segment.3. Use bottom- up approaches: calculate potential customers multiplied by average purchase value.4. Triangulate between multiple calculation methods to increase confidence.5. Segment the TAM by geography, customer type, or product category.6. Develop scenarios for how TAM might evolve based on different assumptions.

# Compound Annual Growth Rate (CAGR)

Compound Annual Growth Rate (CAGR)CAGR analysis provides a standardized measure of growth over time, allowing for comparisons between different segments, companies, or time periods. This metric helps identify which parts of an industry are experiencing accelerated growth.

# Methodology:

Methodology:1. Collect historical revenue or unit sales data for the industry and its segments.2. Calculate CAGR using the formula: CAGR = (Ending Value / Beginning Value)^(1 / number of years) - 13. Compare industry CAGR to GDP growth to determine relative performance.4. Calculate CAGR for different time periods to identify acceleration or deceleration.

5. Compare CAGR across different segments to identify high-growth areas.  
6. Analyze factors driving growth differences between segments.

# PESTLE Analysis

PESTLE analysis examines how external macro- environmental factors impact an industry. This structured approach ensures comprehensive consideration of all major external influences that may affect industry performance and evolution.

# Methodology:

1. Political: Analyze government policies, political stability, trade restrictions, and regulatory trends affecting the industry.  
2. Economic: Examine economic growth rates, interest rates, inflation, unemployment, and other macroeconomic factors.  
3. Social: Identify demographic trends, cultural shifts, lifestyle changes, and evolving consumer preferences.  
4. Technological: Research emerging technologies, innovation rates, R&D spending, and technological disruption potential.  
5. Legal: Review existing and pending legislation, employment laws, consumer protection, and intellectual property considerations.  
6. Environmental: Assess climate change impacts, sustainability pressures, environmental regulations, and resource constraints.

# Industry Cycle Classification

Industry Cycle ClassificationThis analysis categorizes industries based on their sensitivity to economic cycles, helping investors understand how industry performance may vary under different economic conditions.

# Methodology:

Methodology:1. Collect historical industry performance data across multiple economic cycles.2. Calculate correlation between industry revenue/profit and GDP growth.3. Analyze performance during recessions versus expansions.4. Classify the industry as:5. Defensive: Relatively stable regardless of economic conditions (e.g., healthcare, utilities)6. Cyclical: Strongly correlated with economic cycles (e.g., luxury goods, construction)7. Semi- Cyclical: Moderately affected by economic cycles (e.g., certain consumer goods)8. Identify leading and lagging indicators specific to the industry cycle.9. Determine the current position within the industry cycle.

# Industry Life Cycle Stage

This framework identifies where an industry sits in its evolution from emergence to decline, providing context for growth expectations, competitive dynamics, and appropriate strategies.

# Methodology:

1. Analyze industry growth rates, consolidation trends, and innovation patterns.  
2. Classify the industry into one of four stages:  
3. Introduction: Emerging industry with rapid innovation, low penetration, and uncertain standards  
4. Growth: Accelerating adoption, increasing competition, and expanding market  
5. Maturity: Slowing growth, consolidation, emphasis on efficiency and market share  
6. Decline: Negative growth, excess capacity, and diminishing innovation  
7. Identify where different segments may be at different life cycle stages.  
8. Research potential disruptive forces that could reset the life cycle.  
9. Determine appropriate strategies based on the life cycle stage.

# Value Migration Patterns

Value Migration PatternsValue migration analysis tracks how economic value moves within an industry over time, shifting between different business models, segments, or positions in the value chain. This helps identify where future profits will concentrate.

# Methodology:

Methodology:1. Map the industry value chain from raw materials to end customer.2. Analyze historical profit pool distribution across the value chain.3. Identify shifts in profit concentration over time.4. Research emerging business models that may capture value differently.5. Analyze how technology or market changes are redistributing value.6. Project future value migration based on identified trends.

# Key Performance Indicators (KPIs)

Identifying and tracking industry- specific KPIs provides standardized metrics for comparing company performance and understanding what drives success in a particular sector.

# Methodology:

Methodology:1. Research industry- standard performance metrics used by analysts and industry associations.2. Identify operational KPIs specific to the industry (e.g., same- store sales for retail, RevPAR for hotels).3. Determine financial KPIs most relevant to industry value drivers.4. Benchmark KPI ranges for top performers versus average performers.5. Analyze how KPIs have evolved over time and what that indicates about changing success factors.6. Identify leading indicator KPIs that predict future financial performance.

# Financial Analysis

Financial AnalysisIndustry financial analysis examines typical financial structures, performance metrics, and trends across the sector, providing context for evaluating individual company performance.

# Methodology:

Methodology:1. Calculate industry averages for key financial ratios (profitability, efficiency, liquidity, leverage).2. Analyze how these metrics have trended over time.3. Compare financial structures across different segments or business models.4. Identify financial characteristics of top performers versus underperformers.5. Research industry- specific financial metrics and benchmarks.

6. Analyze capital allocation patterns across the industry.

# Strategic Analysis Tools

# Porter's 5 Forces

This framework assesses the competitive intensity and attractiveness of an industry by analyzing five key forces that determine its structure and profitability potential.

# Methodology:

Methodology:1. Supplier Power: Evaluate concentration, differentiation, switching costs, and forward integration threat.2. Buyer Power: Assess concentration, purchase volume, switching costs, price sensitivity, and backward integration threat.3. Competitive Rivalry: Analyze number and size of competitors, industry growth, fixed costs, exit barriers, and product differentiation.4. Threat of Substitutes: Identify alternative solutions, switching costs, relative price- performance, and buyer propensity to substitute.5. Threat of New Entrants: Evaluate economies of scale, capital requirements, access to distribution, expected retaliation, and regulatory barriers.6. Synthesize findings to determine overall industry attractiveness and profit potential.

# SWOT Analysis

SWOT analysis at the industry level identifies internal strengths and weaknesses of the sector as a whole, along with external opportunities and threats that may impact its future.

# Methodology:

1. Strengths: Identify structural advantages of the industry (e.g., high barriers to entry, strong growth, favorable regulation). 
2. Weaknesses: Determine inherent challenges or limitations (e.g., commoditization, high capital intensity, labor shortages). 
3. Opportunities: Research external factors that could benefit the industry (e.g., emerging markets, technological innovations, changing consumer preferences). 
4. Threats: Analyze external risks to the industry (e.g., disruptive technologies, regulatory changes, shifting demographics). 
5. Evaluate how these factors vary across different segments or geographies. 
6. Identify how the target company is positioned relative to these industry-level factors.

# BCG Matrix

While traditionally used for product portfolio analysis, the BCG matrix can be adapted to analyze different segments within an industry based on market growth and relative market share.

# Methodology:

1. Identify distinct segments within the industry.2. Plot each segment on a matrix with:3. X-axis: Relative market share (company's share divided by largest competitor's share)4. Y-axis: Market growth rate5. Classify segments into four categories:6. Stars: High growth, high market share7. Cash Cows: Low growth, high market share8. Question Marks: High growth, low market share9. Dogs: Low growth, low market share10. Analyze how segments have moved within the matrix over time.11. Evaluate the company's position within each segment.12. Determine appropriate strategies based on segment classification.

# GE-9 Box Matrix

For conglomerate analysis, the GE- 9 Box Matrix evaluates business units or industry segments based on industry attractiveness and competitive strength, providing guidance for resource allocation.

# Methodology:

Methodology:1. Industry Attractiveness: Rate each segment on factors like market size, growth rate, profitability, competitive intensity, and cyclicality.2. Competitive Strength: Evaluate the company's position in each segment based on market share, technological position, brand strength, and cost structure.3. Plot each segment on a 3x3 matrix with:4. Y- axis: Industry attractiveness (high, medium, low)5. X- axis: Competitive strength (strong, average, weak)6. Classify segments into three zones:7. Green (invest/grow): High attractiveness and/or strong position8. Yellow (selective investment): Medium attractiveness and position9. Red (harvest/divest): Low attractiveness and/or weak position10. Determine appropriate strategies for each segment based on its position.

# 3. Conglomerate Industry Analysis

# Weightage-based Scorecard Methodology

For conglomerate companies operating across multiple industries, a weightage- based scorecard provides a structured approach to evaluating the overall attractiveness and performance of the diverse business portfolio. This methodology allows investors to assess the conglomerate as a whole while accounting for the varying significance of different business segments.

# Methodology:

Methodology:1. Identify all business segments within the conglomerate and their respective industries.2. Determine appropriate weightage for each segment based on:3. Revenue contribution to the conglomerate4. Profit contribution to the conglomerate5. Strategic importance to future growth6. Capital allocation priorities7. Develop industry- specific evaluation criteria for each segment, including:8. Market growth potential9. Competitive position10. Profitability metrics11. Return on invested capital12. Industry attractiveness factors13. Score each business segment on these criteria using a consistent scale (e.g., 1- 10).14. Calculate weighted scores by multiplying segment scores by their respective weightages.15. Sum the weighted scores to derive an overall conglomerate score.16. Track changes in the scorecard over time to identify improving or deteriorating segments.

# Vertical Analysis Approach

Vertical analysis examines the financial structure of each business segment within a conglomerate, allowing for standardized comparisons across diverse industries and identification of structural advantages or weaknesses.

# Methodology:

1. Collect segment-level financial data from the conglomerate's annual reports and presentations.  
2. For each segment, calculate key financial metrics as percentages:  
3. Revenue components as a percentage of total segment revenue  
4. Cost components as a percentage of total segment revenue  
5. Profit margins at various levels (gross, operating, net)  
6. Asset categories as a percentage of total segment assets  
7. Liability categories as a percentage of total segment assets  
8. Compare these percentage-based metrics across:  
9. Different segments within the conglomerate  
10. Industry benchmarks for each segment  
11. Historical trends for each segment  
12. Identify segments with superior or inferior financial structures.  
13. Analyze how financial structures have evolved over time.  
14. Determine whether segments benefit from being part of the conglomerate structure.

# Extended Industry Analysis for Multiple Segments

This approach applies the comprehensive industry analysis framework to each major segment within a conglomerate, enabling a detailed understanding of the diverse operating environments facing the company.

# Methodology:

1. Identify the 3-5 most significant business segments within the conglomerate.  
2. For each segment, conduct a full industry analysis covering:  
3. Industry segmentation and structure  
4. Demand and supply trends  
5. Competitive landscape  
6. Industry life cycle stage  
7. PESTLE factors specific to that industry  
8. Industry-specific KPIs  
9. Develop a standardized format for comparing key findings across segments.  
10. Identify common themes or divergent trends across the conglomerate's industries.  
11. Assess how well the conglomerate's strategy addresses the specific dynamics of each industry.  
12. Evaluate potential for knowledge or capability transfer between segments.

# GE-9 Box Matrix Implementation

The GE- 9 Box Matrix provides a strategic framework for evaluating and managing a portfolio of business units, making it particularly valuable for analyzing conglomerates with diverse operations across multiple industries.

# Methodology:

Methodology:1. Define criteria for evaluating industry attractiveness, including:2. Market size and growth rate3. Profit margins and pricing trends4. Competitive intensity5. Cyclicality and volatility6. Regulatory environment7. Technological disruption risk8. Define criteria for evaluating business strength, including:9. Market share and position10. Brand strength and differentiation11. Cost position relative to competitors12. Technological capabilities13. Management quality14. Financial performance15. Weight each criterion based on its importance to long- term success.16. Score each business segment on all criteria using a consistent scale (e.g., 1- 5).17. Calculate weighted scores for industry attractiveness and business strength.18. Plot each business segment on the 3x3 GE matrix.19. Develop strategic recommendations based on matrix positioning:20. Invest/Grow (high attractiveness, strong position)21. Selective Investment (medium attractiveness/position)22. Harvest/Divest (low attractiveness, weak position)

# Integration with Other Analysis Sections:

The Conglomerate Industry Analysis builds upon the standard Industry Analysis but adapts it for multi- industry companies. The findings from this section should inform the Investment Time Decision and Company Qualitative Analysis sections, particularly regarding resource allocation strategies and management effectiveness across diverse business environments.

# 4. Disaster Management (Industry)

# External Problem Analysis

External problems represent significant disruptions that can fundamentally alter industry dynamics and company performance. These events are typically beyond the control of individual companies but require strategic responses to mitigate their impact.

# Methodology:

1. Identify potential external disruptions relevant to the industry, including:2. War and geopolitical conflicts affecting supply chains, markets, or resources3. Natural disasters impacting production facilities, distribution networks, or demand4. Pandemic scenarios disrupting operations, consumer behavior, or global trade5. Climate change effects on resources, operations, or regulatory environment6. Assess historical impacts of similar events on the industry:7. Duration of disruption8. Magnitude of financial impact

9. Recovery patterns10. Winners and losers within the industry11. Evaluate the industry's structural vulnerability to different types of external shocks.12. Analyze company-specific exposure and resilience factors:13. Geographic concentration of operations14. Supply chain diversification15. Financial reserves and liquidity16. Operational flexibility17. Develop scenario analyses for potential future disruptions.18. Identify early warning indicators for monitoring purposes.

# Tax Policy Analysis

Tax Policy AnalysisTax policy changes can significantly impact industry economics, competitive dynamics, and investment decisions. Understanding tax sensitivity and monitoring potential policy shifts is crucial for comprehensive industry analysis.

# Methodology:

Methodology:1. Identify key tax policies affecting the industry:2. Corporate income tax rates and structures3. Industry- specific taxes or subsidies4. Import/export duties and tariffs5. Value- added or sales taxes6. Property and asset taxes7. Environmental or carbon taxes

8. Analyze the historical impact of tax changes on:  
9. Industry profitability  
10. Competitive positioning  
11. Investment patterns  
12. Pricing strategies  
13. Corporate structures and domiciles  
14. Research pending or proposed tax legislation that could affect the industry.  
15. Evaluate differential tax impacts across:  
16. Geographic markets  
17. Company sizes  
18. Business models within the industry  
19. Assess company-specific tax strategies and effective tax rates.  
20. Develop scenarios for potential tax policy changes and their implications.

# ESG Factor Analysis

Environmental, Social, and Governance (ESG) factors are increasingly important determinants of industry regulation, consumer preferences, investor sentiment, and long- term sustainability. This analysis examines how ESG considerations may impact industry dynamics and company performance.

# Methodology:

1. Identify material ESG factors specific to the industry:  
2. Environmental: Carbon emissions, resource usage, waste management, biodiversity impact  
3. Social: Labor practices, community relations, product safety, data privacy

4. Governance: Board structure, executive compensation, shareholder rights, business ethics  
5. Research current and emerging regulations related to these ESG factors.  
6. Analyze consumer sentiment and preference shifts related to ESG considerations.  
7. Evaluate investor focus on ESG metrics within the industry.  
8. Benchmark companies within the industry on key ESG metrics.  
9. Identify potential ESG-related risks and opportunities:  
10. Regulatory compliance costs  
11. Consumer boycotts or preference shifts  
12. Access to capital or financing costs  
13. Operational efficiency improvements  
14. New market opportunities

# Political Shift Analysis

Changes in political leadership, ideology, or policy priorities can significantly impact regulatory environments, trade relationships, and economic conditions affecting industries. This analysis examines political risk factors and their potential industry implications.

# Methodology:

1. Identify key political factors affecting the industry:  
2. Regulatory oversight and enforcement  
3. Trade policy and international relations

4. Government spending and procurement  
5. Subsidies and incentives  
6. Antitrust and competition policy  
7. Labor and employment regulations  
8. Map the industry's exposure to different political jurisdictions.  
9. Research upcoming elections or leadership transitions in relevant jurisdictions.  
10. Analyze historical impacts of political shifts on industry regulation and performance.  
11. Evaluate differences in industry treatment across political ideologies or parties.  
12. Develop scenarios for potential political changes and their industry implications.  
13. Assess company-specific political risk exposure and management strategies.

# Corporate Scandal/Scam Analysis

Corporate scandals or industry- wide scams can trigger regulatory backlash, consumer distrust, and fundamental changes to industry practices. This analysis examines vulnerability to such events and their potential consequences.

# Methodology:

1. Research historical scandals or scams within the industry:  
2. Nature of the misconduct  
3. Companies involved  
4. Regulatory response

5. Financial and reputational impact  
6. Industry-wide changes resulting from the event  
7. Identify structural factors that may enable misconduct:  
8. Complex or opaque business models  
9. Misaligned incentive structures  
10. Weak regulatory oversight  
11. Information asymmetry between companies and customers  
12. Industry culture and ethical norms  
13. Evaluate current governance practices and red flags across the industry.  
14. Assess company-specific risk factors and governance quality.  
15. Analyze potential contagion effects if a scandal emerges at one company.  
16. Develop early warning indicators for monitoring purposes.

# Integration with Other Analysis Sections:

The Disaster Management analysis provides critical context for risk assessment that should inform the Investment Time Decision section. Understanding potential disruptions and their likely impacts helps determine whether current valuations adequately account for risks and whether timing is appropriate for investment. This analysis also connects to the Company Opportunity & Threat section, providing industry- level context for company- specific risk factors.

# 5. Investment Time Decision

# Economic Fit Analysis

Economic Fit Analysis Economic Fit Analysis integrates industry conditions, disaster potential, and life cycle positioning to determine whether the current economic environment is favorable for investment in a particular company or sector. This holistic approach helps investors align their timing decisions with broader economic realities.

# Methodology:

Methodology:1. Evaluate industry positioning relative to economic conditions:2. For cyclical industries: Assess current position in the economic cycle and industry- specific cycle3. For defensive industries: Evaluate relative valuation compared to historical ranges4. For growth industries: Analyze sustainability of growth drivers in current economic environment5. Incorporate disaster risk assessment:6. Quantify probability and potential impact of identified disaster scenarios7. Evaluate whether current valuations adequately price in these risks8. Assess company- specific resilience factors relative to industry peers9. Consider industry life cycle implications:10. Early- stage industries: Evaluate timing of adoption acceleration11. Growth- stage industries: Assess sustainability of growth rates12. Mature industries: Analyze consolidation opportunities and dividend potential13. Declining industries: Identify potential turnaround catalysts or cash harvesting opportunities14. Synthesize these factors into an overall economic fit rating:15. Strong fit: Favorable positioning across all three dimensions16. Moderate fit: Mixed positioning with some favorable elements17. Poor fit: Unfavorable positioning across multiple dimensions18. Develop time- based investment scenarios based on the economic fit assessment.

# KPI and Financial Metrics Evaluation

This analysis examines key performance indicators and financial metrics to determine whether current performance trends support investment timing decisions. It focuses on identifying momentum, inflection points, and valuation considerations.

# Methodology:

1. Identify the most relevant KPIs for timing decisions in this specific industry:  
2. Leading indicators of demand or pricing trends  
3. Operational metrics that precede financial performance changes  
4. Sentiment indicators that may signal market perception shifts  
5. Track these KPIs over time to identify:  
6. Acceleration or deceleration trends  
7. Divergence from historical patterns  
8. Correlation with stock price or valuation movements  
9. Analyze financial metrics with timing implications:  
10. Revenue growth trajectory and inflection points  
11. Margin expansion or contraction trends  
12. Cash flow generation and conversion rates  
13. Return on invested capital relative to cost of capital  
14. Compare current metrics to historical ranges and industry benchmarks:  
15. Absolute levels (high/medium/low)  
16. Rate of change (accelerating/stable/decelerating)  
17. Volatility or consistency  
18. Evaluate whether current KPI and financial trends suggest favorable timing for investment.

# Decision Framework Integration

This framework integrates the analyses of Economic Fit, Disaster Management, and Life Cycle Stage to arrive at a comprehensive investment timing decision. It provides a structured approach to weighing multiple factors that influence optimal entry or exit points.

# Methodology:

1. Assign weights to the three major components based on their relevance to the specific industry:2. Economic Fit: Typically weighted higher for cyclical industries3. Disaster Risk: Weighted based on probability and potential impact4. Life Cycle Stage: Weighted based on the pace of industry evolution5. Score each component on a consistent scale (e.g., 1-10):6. Economic Fit: From poor alignment (1) to perfect alignment (10) with current conditions7. Disaster Risk: From high unpriced risk (1) to low or fully priced risk (10)8. Life Cycle: From unfavorable timing (1) to optimal timing (10) within the cycle9. Calculate a weighted timing score.10. Translate the score into a specific position recommendation:11. Buy: High score indicating favorable timing across dimensions12. Accumulate: Moderately high score with some timing concerns13. Hold: Neutral score with mixed timing signals14. Reduce: Moderately low score suggesting deteriorating timing15. Sell: Low score indicating unfavorable timing across dimensions16. Develop time-based scenarios for how the timing score might evolve.

# Position Recommendations

This section translates the timing analysis into specific investment position recommendations, providing actionable guidance on whether to buy, sell, or hold investments for different time horizons.

# Methodology:

1. Differentiate between short-term and long-term positioning:2. Short-term: 0-12 month outlook based on more immediate factors3. Long-term: 1-5 year outlook based on structural and strategic factors4. For short-term positioning, emphasize:5. Technical indicators and momentum6. Near-term catalysts or risks7. Relative valuation compared to recent ranges8. Sentiment indicators and positioning data9. For long-term positioning, emphasize:10. Structural industry trends11. Competitive positioning sustainability12. Long-term growth and return potential13. Strategic value and optionality14. Develop specific position recommendations:15. Buy/Sell/Hold for long-term investment horizon16. Tactical positioning for short-term opportunities17. Include position sizing guidance based on conviction level and risk assessment.18. Establish clear triggers for position reassessment.

# Integration with Other Analysis Sections:

The Investment Time Decision integrates findings from multiple previous sections, particularly Industry Analysis and Disaster Management. It serves as a bridge between the more analytical sections and the final investment decision logic, translating comprehensive analysis into actionable timing recommendations.

# 6. Company Qualitative Analysis

# Founder's History and Background

Understanding the founder's background provides crucial insights into a company's culture, values, and strategic direction. The founder's experience, vision, and leadership style often leave an enduring imprint on the organization, even long after their direct involvement has ended.

# Methodology:

Methodology:1. Research the founder's personal and professional background:2. Educational background and formative experiences3. Prior professional roles and accomplishments4. Entrepreneurial track record with previous ventures5. Personal philosophy and stated values

6. Leadership style and management approach  
7. Analyze the founder's influence on company development:  
8. Original vision and how it has evolved  
9. Key strategic decisions attributed to the founder  
10. Cultural elements established by the founder  
11. Succession planning and leadership transitions  
12. Evaluate the founder's reputation within the industry and broader business community.  
13. Assess the founder's ongoing relationship with the company (if applicable):  
14. Current role and responsibilities  
15. Ownership stake and control mechanisms  
16. Influence on board decisions and strategic direction  
17. Research any controversies or notable achievements associated with the founder.

# Promoter's Holding/Pledging Patterns

Promoter holdings and pledging activities provide important signals about insider confidence, corporate governance, and potential risks. Analyzing these patterns helps investors understand the alignment of interests between promoters and minority shareholders.

# Methodology:

1. Track promoter shareholding patterns over time:

2. Absolute ownership percentage

3. Changes in ownership through purchases, sales, or dilution

4. Distribution among different promoter entities

5. Lock-in provisions and expiration dates

6. Analyze pledging activities:

7. Percentage of promoter holdings that are pledged

8. Changes in pledging levels over time

9. Purpose of pledges (personal borrowing vs. company funding)

10. Financial institutions holding the pledged shares

11. Compare promoter holding and pledging patterns to industry norms.

12. Research any regulatory disclosures or concerns related to promoter transactions.

13. Evaluate the implications of holding/pledging patterns for corporate governance and shareholder alignment.

# Corporate Governance Assessment

Corporate governance encompasses the systems, principles, and processes by which a company is directed and controlled. Strong governance is essential for protecting shareholder interests, ensuring ethical behavior, and supporting long- term value creation.

# Methodology:

1. Evaluate board composition and quality:2. Independence of directors (percentage of independent directors)

3. Diversity in terms of skills, experience, gender, and background  
4. Tenure and refreshment practices  
5. Relevant expertise for industry-specific challenges  
6. Analyze board practices and effectiveness:  
7. Meeting frequency and attendance records  
8. Committee structure and responsibilities  
9. Board evaluation processes  
10. Director compensation and incentive alignment  
11. Assess shareholder rights and treatment:  
12. Voting rights and structures (single vs. dual-class shares)  
13. Related party transaction policies and history  
14. Dividend policies and capital allocation decisions  
15. Minority shareholder protections  
16. Evaluate disclosure quality and transparency:  
17. Financial reporting practices and timeliness  
18. Management discussion quality and candor  
19. Accessibility of information to shareholders  
20. Consistency of communication during challenging periods  
21. Review compliance history and ethical track record:  
22. Regulatory violations or investigations  
23. Litigation history  
24. Whistleblower policies and incidents  
25. Corporate social responsibility initiatives

# C-Level Executives Background Checking

The quality, experience, and integrity of the executive team significantly impact a company's execution capabilities and strategic direction. Thorough background checking of C- level executives helps assess leadership quality and identify potential red flags.

# Methodology:

1. Compile comprehensive profiles of key executives:  
2. Educational background and professional qualifications  
3. Career progression and previous roles  
4. Track record of achievements and failures  
5. Industry reputation and relationships  
6. Compensation history and incentive structures  
7. Verify credentials and representations:  
8. Confirm educational degrees and professional certifications  
9. Validate significant career accomplishments  
10. Cross-check employment history and roles  
11. Research potential concerns:  
12. Involvement in failed businesses or bankruptcies  
13. Regulatory actions or sanctions  
14. Litigation history  
15. Public controversies or ethical issues  
16. Analyze team dynamics and complementary skills:  
17. Balance of expertise across the executive team  
18. Working relationships and tenure together  
19. Succession planning for key positions  
20. Evaluate alignment with company strategy and culture.

# Business Model Analysis

A company's business model defines how it creates, delivers, and captures value. Understanding the business model is fundamental to assessing sustainability, competitive advantage, and growth potential.

# Methodology:

Methodology:1. Identify the core elements of the business model:2. Value proposition: What unique benefits does the company offer customers?3. Customer segments: Which specific markets or customer groups does it target?4. Revenue model: How does the company generate income (subscription, transaction, advertising, etc.)?5. Cost structure: What are the major cost components and their characteristics (fixed vs. variable)?6. Key resources: What critical assets enable the business model?7. Key activities: What processes are essential to delivering the value proposition?8. Partner network: What external relationships are vital to the business?9. Analyze business model characteristics:10. Scalability: Can the model grow without proportional cost increases?11. Recurring revenue: What percentage of revenue is predictable or recurring?12. Network effects: Does the value increase as more users join?13. Switching costs: How difficult is it for customers to change providers?14. Capital intensity: How much investment is required to grow?15. Evaluate business model evolution over time:16. Major pivots or transitions17. Expansion into adjacent models18. Adaptation to market or technological changes19. Compare the business model to competitors and industry norms.

# Pricing Strategy Evaluation

Pricing strategy directly impacts revenue, market positioning, customer perception, and competitive dynamics. Analyzing a company's approach to pricing provides insights into its market power, value proposition, and strategic priorities.

# Methodology:

1. Identify the company's primary pricing approach:  
2. Value-based: Pricing based on perceived customer value  
3. Cost-plus: Pricing based on costs plus desired margin  
4. Competitive: Pricing relative to competitors  
5. Penetration: Low pricing to gain market share  
6. Premium: High pricing to signal quality or exclusivity  
7. Dynamic: Pricing that varies based on demand, timing, or customer segments  
8. Analyze pricing structure and tactics:  
9. Tiered pricing or product versioning  
10. Bundling or unbundling strategies  
11. Discount policies and promotional approaches  
12. Freemium models or loss leaders  
13. Evaluate pricing power and flexibility:  
14. Ability to pass cost increases to customers  
15. Price elasticity of demand  
16. Customer response to historical price changes  
17. Competitive response to pricing moves  
18. Assess alignment between pricing strategy and overall business strategy.  
19. Research pricing trends and innovations within the industry.

# Strategic Fit Assessment

Strategic fit evaluates how well a company's strategy aligns with its capabilities, market opportunities, and external environment. This assessment helps determine whether the company is pursuing a coherent and sustainable strategic direction.

# Methodology:

1. Identify the company's stated strategy:2. Mission and vision statements3. Publicly communicated strategic priorities4. Investment focus areas5. Target markets and customer segments6. Analyze alignment between strategy and internal capabilities:7. Core competencies and how they support the strategy8. Resource allocation patterns9. Organizational structure and its fit with strategic priorities10. Cultural alignment with strategic direction11. Evaluate external alignment:12. Market trends and how strategy addresses them13. Competitive positioning and differentiation14. Customer needs and preferences15. Regulatory environment and compliance requirements16. Assess strategic consistency and coherence:17. Consistency of strategic messaging over time18. Alignment between stated strategy and actual decisions19. Integration across business units or product lines20. Balance between short-term execution and long-term vision

# Company Growth Pattern Analysis

Understanding how a company has historically grown provides insights into its capabilities, strategic preferences, and likely future trajectory. This analysis distinguishes between organic growth generated internally and inorganic growth through acquisitions.

# Methodology:

Methodology:1. Quantify historical growth patterns:2. Overall revenue and profit growth rates3. Organic growth contribution4. Inorganic growth contribution5. Geographic expansion contribution6. New product contribution7. Analyze organic growth capabilities:8. R&D effectiveness and new product development9. Market share gains within existing segments10. Pricing power and its contribution to growth11. Expansion into adjacent markets or customer segments12. Operational scaling capabilities13. Evaluate inorganic growth approach:14. Acquisition frequency and size15. Types of acquisitions (technology, market access, consolidation)16. Post- merger integration track record

17. Financial returns on past acquisitions  
18. Funding approach for acquisitions  
19. Assess sustainability of historical growth patterns.  
20. Identify potential constraints on future growth.

# R&D Investment Trends

Research and Development (R&D) investment reflects a company's commitment to innovation and long- term competitiveness. Analyzing R&D trends helps assess future growth potential and technological leadership.

# Methodology:

1. Quantify R&D investment patterns:  
2. Absolute R&D spending over time  
3. R&D as a percentage of revenue  
4. Comparison to industry benchmarks  
5. Allocation across different research areas or product categories  
6. Evaluate R&D effectiveness:  
7. New product revenue as percentage of total revenue  
8. Patent generation and quality metrics  
9. Time-to-market for new developments  
10. Return on R&D investment  
11. Analyze R&D strategy and focus:  
12. Balance between incremental and disruptive innovation  
13. Internal development versus external partnerships

14. Centralized versus decentralized R&D structure  
15. Geographic distribution of R&D activities  
16. Research major R&D initiatives and their strategic importance.  
17. Assess the company's innovation culture and talent management.

# Technology Adoption Analysis

A company's approach to adopting and leveraging technology significantly impacts its operational efficiency, customer experience, and competitive positioning. This analysis examines how effectively the company embraces technological change.

# Methodology:

1. Assess the company's technology infrastructure:  
2. Core systems and platforms  
3. Technology stack modernity  
4. Technical debt levels  
5. Cloud adoption and digital transformation progress  
6. Evaluate technology governance and strategy:  
7. Technology leadership and reporting structure  
8. Technology investment levels and priorities  
9. Build versus buy decision framework  
10. Technology risk management approach  
11. Analyze adoption of emerging technologies:  
12. Artificial intelligence and machine learning  
13. Internet of Things (IoT)

14. Blockchain or distributed ledger technologies  
15. Automation and robotics  
16. Industry-specific technological innovations  
17. Research technology-driven initiatives and their business impact.  
18. Compare technology adoption approach to industry peers and best practices.

# Integration with Other Analysis Sections:

The Company Qualitative Analysis provides critical context for evaluating the human and strategic elements that drive company performance. These insights should inform the Investment Time Decision and connect to the Company Opportunity & Threat Analysis, particularly regarding management quality and strategic direction.

# 7. Company Opportunity & Threat Analysis

# Mergers & Acquisitions (M&A) Potential

M&A activities can significantly impact a company's growth trajectory, competitive positioning, and shareholder value. This analysis evaluates both the potential for a company to be an acquirer or a target, and the likely implications of such transactions.

# Methodology:

Methodology:1. Assess the company as a potential acquirer:2. Financial capacity for acquisitions (cash reserves, debt capacity, equity valuation)3. Historical M&A strategy and execution track record4. Stated acquisition priorities and target criteria5. Integration capabilities and past successes or failures6. Cultural approach to acquisitions and integration7. Evaluate the company as a potential acquisition target:8. Strategic attractiveness to potential acquirers9. Valuation relative to potential synergies10. Ownership structure and takeover defenses11. Regulatory considerations for potential combinations12. Management and board openness to transactions13. Identify potential acquisition targets or acquirers:14. Strategic fit with potential partners15. Financial compatibility16. Cultural alignment17. Regulatory feasibility18. Analyze potential transaction structures and their implications.19. Estimate value creation or destruction scenarios from potential transactions.

# Promoters Holding & Pledging Trends

Changes in promoter holdings and pledging patterns can signal insider confidence, financial stress, or upcoming strategic shifts. Tracking these trends provides early indicators of potential opportunities or threats.

# Methodology:

Methodology:1. Track historical patterns in promoter holdings:2. Absolute ownership percentage over time3. Timing and size of increases or decreases4. Method of ownership changes (open market, block deals, rights issues)5. Differential patterns among multiple promoters6. Analyze pledging activities and trends:7. Percentage of promoter holdings pledged8. Changes in pledging levels over time9. Timing of significant pledging activities10. Financial institutions involved in pledging arrangements11. Research the stated reasons for significant changes.12. Evaluate the financial implications of current pledging levels:13. Potential margin call scenarios14. Share price levels that might trigger forced selling15. Impact of potential promoter selling on market liquidity16. Compare patterns to industry peers and market conditions.

# New Product Launch Pipeline

The pipeline of upcoming product launches provides visibility into future growth drivers, innovation effectiveness, and strategic direction. This analysis evaluates the potential impact of new products on the company's competitive position and financial performance.

# Methodology:

1. Identify confirmed and rumored new products in development:  
2. Official announcements and roadmaps  
3. Patent filings and regulatory submissions  
4. Industry rumors and expert analysis  
5. Supplier relationships and component orders  
6. Analyze the strategic significance of upcoming launches:  
7. Expansion into new markets or customer segments  
8. Defense of core markets against competitive threats  
9. Potential for cannibalization of existing products  
10. Alignment with broader industry trends  
11. Estimate potential financial impact:  
12. Addressable market size for new products  
13. Likely adoption rates and ramp-up timelines  
14. Margin implications compared to existing portfolio  
15. Required investment for successful launches  
16. Evaluate execution risks and dependencies:  
17. Technical challenges and development status  
18. Supply chain readiness  
19. Regulatory approvals required  
20. Go-to-market capabilities  
21. Compare the pipeline to competitive offerings and industry innovation trends.

# Fraud/Scandal Risk Assessment

Corporate fraud or scandals can devastate shareholder value through direct financial impact, regulatory penalties, reputational damage, and management distraction. This analysis identifies potential vulnerabilities and warning signs.

# Methodology:

1. Evaluate structural risk factors:  
2. Complex business model or accounting practices  
3. Aggressive revenue recognition or other accounting policies  
4. High-pressure performance culture with ambitious targets  
5. Concentrated decision-making power  
6. Weak internal controls or compliance functions  
7. Operations in countries with high corruption indices  
8. Analyze financial warning signs:  
9. Discrepancies between financial metrics (e.g., earnings vs. cash flow)  
10. Unusual accruals or off-balance-sheet arrangements  
11. Frequent auditor changes or qualified audit opinions  
12. Related party transactions  
13. Unexplained changes in key financial ratios  
14. Research governance and oversight quality:  
15. Board independence and expertise  
16. Audit committee effectiveness  
17. Whistleblower policies and procedures  
18. History of regulatory investigations or sanctions  
19. Assess industry-specific fraud risks and precedents.  
20. Evaluate management integrity and ethical culture.

# Stress Test Scenarios

Stress testing evaluates a company's resilience under adverse scenarios, helping investors understand downside risks and the robustness of the business model. This analysis examines how the company might perform under various challenging conditions.

# Methodology:

1. Identify key vulnerability areas specific to the company and industry:  
2. Revenue drivers and potential disruptions  
3. Cost structure and input price sensitivities  
4. Balance sheet risks and refinancing needs  
5. Regulatory dependencies  
6. Competitive threats  
7. Develop specific stress scenarios:  
8. Severe but plausible industry downturns  
9. Disruptive competitive entry  
10. Supply chain disruptions  
11. Regulatory changes or legal challenges  
12. Technology shifts or obsolescence risks  
13. Liquidity crises or credit market disruptions  
14. Model financial impact under each scenario:  
15. Revenue implications  
16. Margin effects  
17. Cash flow consequences  
18. Balance sheet impact  
19. Covenant compliance  
20. Assess management preparedness and contingency plans.  
21. Evaluate historical performance during previous stress periods.

# Integration with Other Analysis Sections:

Integration with Other Analysis Sections:The Company Opportunity & Threat Analysis builds upon insights from the Company Qualitative Analysis and connects directly to the Investment Decision Logic. By identifying specific catalysts and risks, this section helps investors anticipate potential changes in company trajectory that might warrant position adjustments.

# 8. Company Quantitative Analysis

# Valuation Metrics

Valuation MetricsValuation metrics provide standardized measures for comparing companies and assessing whether a stock is potentially undervalued or overvalued. These metrics form the foundation of quantitative investment analysis and help contextualize a company's market pricing.

# Price to Earnings (P/E) Ratio

The P/E ratio is one of the most widely used valuation metrics, comparing a company's share price to its earnings per share. This metric helps investors understand how much they are paying for each dollar of earnings.

# Methodology:

1. Calculate different variants of the P/E ratio:

2. Trailing P/E: Based on reported earnings from the past 12 months  
3. Forward P/E: Based on projected earnings for the next 12 months  
4. Normalized P/E: Based on average earnings over a full business cycle  
5. Compare the company's P/E ratios to:  
6. Historical ranges for the company  
7. Industry peers and averages  
8. Broader market benchmarks  
9. Expected earnings growth rates (PEG ratio)  
10. Analyze factors affecting the P/E ratio:  
11. Earnings growth expectations  
12. Earnings quality and consistency  
13. Balance sheet strength  
14. Industry growth prospects  
15. Interest rate environment  
16. Evaluate whether current P/E levels are justified by fundamentals.

# Price to Book (P/B) Ratio

The P/B ratio compares a company's market value to its book value (net assets). This metric is particularly useful for asset- intensive businesses and financial institutions, providing insight into how the market values a company's assets.

# Methodology:

1. Calculate the P/B ratio:  
2. Market capitalization divided by total book value of equity  
3. Adjust for intangible assets if appropriate for the industry  
4. Compare the company's P/B ratio to:  
5. Historical ranges for the company

6. Industry peers and averages  
7. Return on equity (ROE) levels  
8. Analyze factors affecting the P/B ratio:  
9. Asset quality and composition  
10. Hidden assets or liabilities  
11. Expected return on new investments  
12. Accounting policies affecting book value  
13. Dividend payout policies  
14. Evaluate whether current P/B levels are justified by fundamentals.

# Return on Equity (ROE)

ROE measures a company's profitability relative to shareholders' equity, indicating how efficiently a company uses shareholders' capital to generate profits. This metric is crucial for understanding value creation over time.

# Methodology:

1. Calculate ROE using different approaches:  
2. Basic ROE: Net income divided by average shareholders' equity  
3. DuPont analysis: Breaking ROE into components (profit margin, asset turnover, financial leverage)  
4. Adjusted ROE: Excluding non-recurring items or adjusting for accounting distortions  
5. Track ROE trends over time:  
6. Absolute levels  
7. Stability and consistency  
8. Direction of change  
9. Compare the company's ROE to:

10. Industry peers and averages  
11. Company's own cost of equity  
12. Historical company performance  
13. Analyze factors driving ROE:  
14. Operational efficiency (margins)  
15. Asset utilization (turnover)  
16. Financial leverage  
17. Tax efficiency  
18. Assess the sustainability of current ROE levels.

# Return on Capital Employed (ROCE)

ROCE measures a company's profitability relative to all capital employed (equity and debt), providing insight into how efficiently a company uses all its capital to generate profits. This metric helps evaluate management's capital allocation effectiveness.

# Methodology:

1. Calculate ROCE:  
2. EBIT (Earnings Before Interest and Taxes) divided by Capital Employed  
3. Capital Employed = Total Assets - Current Liabilities  
4. Track ROCE trends over time:  
5. Absolute levels  
6. Stability and consistency  
7. Direction of change  
8. Compare the company's ROCE to:  
9. Industry peers and averages  
10. Company's weighted average cost of capital (WACC)

11. Historical company performance  
12. Analyze factors driving ROCE:  
13. Operating margin  
14. Capital intensity  
15. Working capital management  
16. Fixed asset utilization  
17. Assess the sustainability of current ROCE levels.

# Operational Metrics

EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization)

EBITDA provides a measure of operational profitability before the impact of capital structure, tax jurisdiction, and non- cash expenses. This metric facilitates comparisons of operating performance across companies with different financial structures.

# Methodology:

1. Calculate EBITDA:  
2. Net Income + Interest + Taxes + Depreciation + Amortization  
3. Adjust for non-recurring or non-operational items  
4. Analyze EBITDA trends:  
5. Absolute levels  
6. Growth rates  
7. Margins (EBITDA/Revenue)  
8. Stability and seasonality  
9. Compare the company's EBITDA metrics to:

10. Industry peers and averages  
11. Historical company performance  
12. Management guidance and analyst expectations  
13. Evaluate the quality and sustainability of EBITDA:  
14. Recurring versus non-recurring components  
15. Cash conversion efficiency  
16. Relationship to capital expenditure requirements  
17. Assess the limitations of EBITDA for this specific company.

# Enterprise Value (EV)

Enterprise Value represents the total value of a company, including both equity and debt, minus cash and cash equivalents. This metric provides a more comprehensive view of a company's value than market capitalization alone.

# Methodology:

1. Calculate Enterprise Value:  
2. Market Capitalization + Total Debt - Cash and Cash Equivalents  
3. Include other adjustments as appropriate (minority interests, pension deficits, etc.)  
4. Analyze EV trends over time:  
5. Absolute levels  
6. Relationship to underlying business fundamentals  
7. Changes in components (equity value vs. debt levels)  
8. Compare the company's EV to:  
9. Industry peers and averages  
10. Historical company levels  
11. Sum-of-the-parts or break-up valuations  
12. Evaluate the appropriateness of EV for valuation purposes:

13. Treatment of leases and off-balance-sheet obligations14. Treatment of non-controlling interests15. Adjustments for non-operating assets

# EV/EBITDA Ratio

The EV/EBITDA ratio is a valuation multiple that compares a company's enterprise value to its earnings before interest, taxes, depreciation, and amortization. This metric is widely used for comparing companies with different capital structures and tax situations.

# Methodology:

1. Calculate the EV/EBITDA ratio:2. Enterprise Value divided by EBITDA3. Consider both trailing twelve months (TTM) and forward estimates4. Compare the company's EV/EBITDA ratio to:5. Historical ranges for the company6. Industry peers and averages7. Expected EBITDA growth rates8. Analyze factors affecting the EV/EBITDA ratio:9. EBITDA growth expectations10. EBITDA quality and sustainability11. Capital expenditure requirements12. Industry growth prospects13. Interest rate environment14. Evaluate whether current EV/EBITDA levels are justified by fundamentals.

# Growth Metrics

# Revenue Growth Analysis

Revenue growth is a fundamental indicator of a company's market success and expansion. Analyzing growth patterns provides insight into competitive positioning, market share trends, and long- term business trajectory.

# Methodology:

1. Calculate revenue growth rates using different timeframes:  
2. Year-over-Year (YoY): Current period compared to same period previous year  
3. Quarter-over-Quarter (QoQ): Sequential growth between quarters  
4. Compound Annual Growth Rate (CAGR): Smoothed growth over multiple years  
5. Analyze organic versus inorganic growth:  
6. Adjusting for acquisitions and divestitures  
7. Separating price and volume contributions  
8. Identifying new product or market contributions  
9. Compare the company's growth rates to:  
10. Industry peers and averages  
11. Overall market growth  
12. Management guidance and analyst expectations  
13. Historical company performance  
14. Evaluate growth quality and sustainability:  
15. Growth consistency and volatility  
16. Customer concentration risks  
17. Geographic and product diversification

18. Pricing power versus volume growth

# Year-over-Year (YoY) Comparisons

YoY comparisons evaluate performance against the same period in the previous year, helping to identify trends while controlling for seasonality. This approach provides insight into the company's growth trajectory and competitive momentum.

# Methodology:

1. Calculate YoY changes for key metrics:  
2. Revenue  
3. Gross margin  
4. Operating margin  
5. Net income  
6. Cash flow  
7. Key operational KPIs  
8. Analyze patterns across multiple YoY periods:  
9. Acceleration or deceleration trends  
10. Consistency or volatility  
11. Divergence between different metrics  
12. Adjust for factors affecting comparability:  
13. Accounting changes  
14. One-time events  
15. Calendar effects  
16. Acquisitions or divestitures  
17. Compare YoY performance to:  
18. Industry peers

19. Management guidance  
20. Analyst expectations  
21. Macroeconomic indicators

# Quarter-over-Quarter (QoQ) Comparisons

QoQ comparisons evaluate sequential performance between consecutive quarters, helping to identify immediate momentum and inflection points. This approach provides early signals of changing business trends.

# Methodology:

1. Calculate QoQ changes for key metrics:  
2. Revenue  
3. Gross margin  
4. Operating margin  
5. Net income  
6. Cash flow  
7. Key operational KPIs  
8. Adjust for seasonal patterns:  
9. Develop seasonally adjusted QoQ metrics where appropriate  
10. Compare to typical seasonal patterns  
11. Identify deviations from normal seasonality  
12. Analyze patterns across multiple QoQ periods:  
13. Acceleration or deceleration trends  
14. Consistency or volatility  
15. Early warning signals of change  
16. Compare QoQ performance to:

17. Historical company patterns  
18. Industry peers  
19. Management guidance  
20. Analyst expectations

# Valuation Methodologies

# Discounted Cash Flow (DCF)

DCF valuation estimates the intrinsic value of a company based on projected future cash flows discounted to their present value. This methodology provides a fundamental approach to valuation based on the company's ability to generate cash.

# Methodology:

1. Project future free cash flows:  
2. Develop detailed projections for 5-10 years  
3. Base projections on historical performance, industry trends, and company-specific factors  
4. Consider multiple scenarios (base, upside, downside)  
5. Determine the appropriate discount rate:  
6. Calculate weighted average cost of capital (WACC)  
7. Adjust for company-specific risk factors  
8. Consider country risk premiums for international operations  
9. Estimate terminal value:  
10. Apply perpetuity growth method or exit multiple approach  
11. Ensure terminal growth assumptions are reasonable and sustainable  
12. Consider industry maturity and competitive dynamics

13. Calculate present value:  
14. Discount projected cash flows and terminal value  
15. Sum to determine enterprise value  
16. Subtract debt and add cash to arrive at equity value  
17. Divide by shares outstanding to determine per-share value  
18. Perform sensitivity analysis on key assumptions:  
19. Discount rate  
20. Terminal growth rate  
21. Operating margin  
22. Revenue growth  
23. Capital expenditure requirements

# Relative Valuation

Relative valuation assesses a company's value by comparing its financial metrics to similar companies or industry benchmarks. This approach provides context for valuation based on how the market prices comparable assets.

# Methodology:

1. Identify appropriate peer group:  
2. Companies with similar business models  
3. Comparable size and growth characteristics  
4. Similar geographic exposure  
5. Comparable capital intensity and return profiles  
6. Select relevant valuation multiples:

7. P/E, EV/EBITDA, P/B, P/S, etc.  
8. Consider industry-specific multiples  
9. Use both trailing and forward metrics  
10. Adjust for comparability:  
11. Normalize for accounting differences  
12. Consider differences in growth rates  
13. Adjust for capital structure variations  
14. Account for different business mix  
15. Analyze relative valuation positioning:  
16. Current premium or discount to peers  
17. Historical relative valuation ranges  
18. Justification for valuation differences  
19. Develop target valuation range based on peer multiples.

# Integration with Other Analysis Sections:

The Company Quantitative Analysis provides objective metrics that should be interpreted in the context of the qualitative factors identified in previous sections. These quantitative insights directly inform the Investment Decision Logic by establishing valuation parameters and growth expectations that can be compared to current market pricing.
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
        f"Is the company heavily dependent on a single industry segment? How has the revenue distribution changed over time? Are emerging industries gaining a larger share of the company's revenue? How does the company's industry diversification compare to competitors? Does the company's revenue distribution align with its stated strategic goals?"
        f"Which products are experiencing the highest growth rates?- Are any flagship products showing signs of maturity or decline?- How does the growth of newer products compare to established ones?- What is the company's product pipeline, and how might it affect future revenue distribution?- How do growth rates compare to market growth rates for similar products?"
        f"What percentage of revenue comes from domestic versus international markets?- Which international regions are growing fastest for the company?- How has the geographical distribution changed over time?- What are the company's stated goals for geographical expansion?- How does the company's international presence compare to competitors?- What risks (political, economic, currency) exist in the company's key international markets?"
        f"How is the overall industry divided into meaningful segments?- Which segments are growing, stable, or declining?- How concentrated or fragmented is each segment?- Where does the target company position itself within the industry structure?- Are there underserved segments that represent opportunities?- How are industry boundaries changing or blurring with adjacent industries?"
        f"Is industry demand growing faster or slower than supply?- What are the key drivers of demand in this industry?- Are there supply constraints or oversupply conditions?- How cyclical is demand in this industry?- What leading indicators best predict demand changes?- How elastic is pricing in response to supply- demand shifts?"
        f"Are companies from adjacent industries entering this market?- Are established players in this industry diversifying into new sectors?- What capabilities or assets facilitate successful cross- industry migration?- How are customer needs evolving in ways that might redefine industry boundaries?- What regulatory or technological barriers protect industry boundaries?"
        f"What is the current size of the addressable market? What percentage of the TAM is currently being served? How is the TAM expected to grow over the next 5- 10 years? . What factors could significantly expand or contract the TAM? How does the company's current market share compare to the TAM? What portion of the TAM is realistically addressable given the company's capabilities?"
        f"What is the overall industry CAGR over the past 5 years?  - How does this compare to broader economic growth?  - Which segments are growing faster or slower than the industry average?  - Is the growth rate accelerating, stable, or decelerating?  - What factors are driving growth in high-performing segments?  - How sustainable is the current growth trajectory?"
        f"Which PESTLE factors currently have the greatest impact on the industry?- What upcoming changes in these factors might significantly affect the industry?- How do these factors vary across different geographic markets?- Which factors represent opportunities versus threats?- How well is the company positioned to respond to these external factors?- What leading indicators should be monitored to anticipate changes in these factors?"
        f"How sensitive is the industry to economic downturns?- What is the typical lag between economic changes and industry impact?- Where is the industry currently positioned in its cycle?"
        f"What stage of the life cycle is the industry currently in?- How long has the industry been in this stage, and how long might it remain?- Are different segments at different life cycle stages?- What are the implications of the current stage for competitive dynamics?- What strategies are most appropriate given the life cycle stage?- What factors might accelerate or delay progression to the next stage?"
        f"Where in the value chain is profit concentration increasing or decreasing?- Which business models are gaining or losing economic value?- What factors are driving value migration within the industry?- How might emerging technologies redistribute value in the future?- Where is the company positioned relative to value migration trends?- What strategic moves could position the company to capture migrating value?"
        f"What are the 5- 7 most critical KPIs for this industry? How does the company perform on these KPIs relative to competitors? Are there emerging KPIs gaining importance in the industry? How have benchmark levels for key KPIs changed over time? Which KPIs most strongly correlate with financial performance? What operational metrics serve as leading indicators for financial KPIs?"
        f"Key Questions:- What are typical profit margins at different points in the value chain?- How capital- intensive is the industry, and how is this changing?- What financial characteristics distinguish industry leaders?- How do financial metrics vary across different business models within the industry?- What financial trends are emerging across the industry?- How do financial structures change throughout the industry life cycle?"
        f"Which of the five forces exerts the strongest influence on industry profitability?- How have these forces evolved over the past 5-10 years?- What trends might strengthen or weaken each force in the future?- How do these forces vary across different industry segments?- What strategic implications do these forces have for positioning within the industry?- How might technological or regulatory changes alter the five forces?"
        f"What inherent characteristics make this industry attractive or challenging?- What external developments present the greatest opportunities or threats?- How are industry participants responding to these factors?- Which companies are best positioned to leverage industry strengths and opportunities?- How might industry weaknesses be addressed through innovation or consolidation?- What strategic moves might mitigate industry-level threats?"
        f"Which industry segments represent the most attractive opportunities?- How is the company positioned across different segments?- How have segments evolved within the matrix over time?- What resource allocation strategy is appropriate given the segment distribution?- Which segments are likely to transition between categories in the near future?- How does the company's segment positioning compare to key competitors?"
        f"Which segments warrant increased investment? Which segments should be maintained with selective investment? Which segments are candidates for harvesting or divestment? How might industry attractiveness factors evolve over time? What strategic moves could improve competitive position in key segments? How does the portfolio balance compare to competitors?"
        f"How balanced is the conglomerate's portfolio across different industries?- Which segments contribute most significantly to overall performance?- Are high- weightage segments performing well or underperforming?- How does the conglomerate's resource allocation align with segment performance and potential?- What is the trajectory of each segment's score over time?- How does the overall conglomerate score compare to peer conglomerates?"
        f"Which segments demonstrate the most efficient cost structures? - How do capital intensity and asset utilization vary across segments?  - Are there segments with financial structures significantly different from industry norms?  - How have segment financial structures changed over time?- Do any segments show evidence of benefiting from synergies within the conglomerate?- Which segments have the most sustainable financial structures?"
        f"How diverse are the industry dynamics across the conglomerate's portfolio?- Which segments face the most favorable or challenging industry conditions?- Are there common external factors affecting multiple segments?- How well does the conglomerate's overall strategy account for segment-specific industry dynamics?- Are there opportunities for cross-pollination of best practices between segments?- Does the conglomerate demonstrate superior management capabilities across diverse industries?"
        f"How is the conglomerate's portfolio distributed across the GE matrix?- Is there appropriate balance between growth opportunities and cash-generating businesses?- Which segments should receive priority for capital allocation?- Are there segments that should be considered for divestiture?- How has the positioning of segments changed over time?- Does the conglomerate's actual resource allocation align with what the GE matrix suggests?"
        f"What types of external disruptions pose the greatest threat to this industry?- How has the industry historically responded to major external shocks?- Which companies demonstrated superior resilience during past disruptions?- What structural changes resulted from previous external shocks?- How might future external disruptions differ from historical patterns?- What contingency planning is evident among industry participants?"
        f"How sensitive is industry profitability to tax rate changes? - Which companies have the most tax-efficient structures?  - What tax policy changes are currently under consideration by relevant authorities?  - How might tax changes alter competitive dynamics within the industry?  - Are there tax-driven trends in corporate domicile or structure?  - How do tax considerations influence capital allocation decisions?"
        f"Which ESG factors are most material to this industry's financial performance?  - How are regulatory requirements evolving regarding key ESG issues?  - Which companies are leaders versus laggards on critical ESG metrics?  - How are consumer preferences shifting based on ESG considerations?  - What ESG-related risks could significantly impact industry economics?  - Are there emerging opportunities from ESG trends that companies could capitalize on?"
        f"How sensitive is the industry to changes in political leadership?  - Which political factors have historically had the greatest impact on industry performance?  - What upcoming political events could significantly affect the industry?  - How do different political ideologies or parties approach regulation of this industry?  - Which companies are most exposed to or insulated from political risks?  - How effectively do industry participants manage political relationships and risks?"
        f"What types of misconduct or scandals have historically affected this industry?  - Are there structural characteristics that make the industry vulnerable to certain types of misconduct?  - Which companies demonstrate superior governance practices and ethical cultures?  - What regulatory changes might result from potential scandals?  - How might consumer trust or industry reputation be affected by misconduct?  - What early warning signs might indicate emerging governance problems?"
        f"How well aligned is the industry with current and projected economic conditions?- Are disaster risks adequately reflected in current valuations?- Does the industry's life cycle stage suggest favorable timing for investment?- What catalysts might improve the economic fit in the near to medium term?- How does the economic fit vary across different segments within the industry?- What indicators should be monitored to identify changes in economic fit?"
        f"What do leading KPIs indicate about future financial performance?  - Are there inflection points visible in key metrics?  - How do current financial metrics compare to historical ranges?- Is performance momentum positive, neutral, or negative?- Do operational metrics support or contradict financial trends?- What time lag typically exists between KPI changes and financial impact?"
        f"What is the current integrated timing score for the investment?- Which component has the greatest influence on the timing decision?- What changes would significantly improve or worsen the timing score?- How sensitive is the timing score to changes in individual components?- What monitoring framework should be established to track timing factors?- What catalysts might trigger a reassessment of the timing decision?"
        f"Does the timing analysis support different positions for short- term versus long- term horizons?- What position size is appropriate given the timing conviction and risk assessment?- What specific catalysts or developments would trigger a position change?- How does the recommended position compare to market consensus?- What monitoring framework should be established to track timing factors?- What risk management parameters should accompany the position recommendation?"
        f"How has the founder's background shaped the company's strategic direction?  - What unique insights or advantages did the founder bring to the business?  - How effectively has the founder's vision been institutionalized within the company?  - If the founder has departed, how smooth was the transition and what legacy remains?  - Does the company remain dependent on the founder's continued involvement?  - How does the market perceive the founder's leadership and decision-making?"
        f"Are promoters increasing or decreasing their ownership stake over time?- What percentage of promoter holdings are pledged, and how has this changed?- What do pledging patterns suggest about promoters' financial position?- Have there been any unusual or concerning transactions involving promoter shares?- How aligned are promoter interests with those of minority shareholders?- What risks might high levels of pledging pose to share price stability?"
        f"Does the board have sufficient independence and relevant expertise?  - How effective is the board in providing oversight and strategic guidance?  - Are there any concerning related party transactions or conflicts of interest?  - How transparent is the company in its communications with shareholders?  - Does the company have a history of regulatory compliance issues?  - How well are minority shareholder interests protected?"
        f"Do executives have relevant experience for their current roles?  - What is their track record of performance in previous positions?  - Are there any concerning patterns or incidents in their backgrounds?  - How well does the team work together and complement each other's skills?  - Is executive compensation aligned with shareholder interests?  - What is the depth of talent below the C-suite level?"
        f"What are the most distinctive aspects of the company's business model?- How sustainable is the business model in the face of industry changes?- What competitive advantages are embedded in the business model?-How has the business model evolved, and what drove those changes?- What metrics best capture the health and performance of this business model?- What potential disruptions could threaten the business model?"
        f"How does the company's pricing strategy compare to competitors?- What degree of pricing power does the company possess?- How effectively does pricing communicate the value proposition?- Is the pricing strategy sustainable given cost structures and competitive dynamics?- How might pricing strategy need to evolve as the company or industry matures?- What pricing experiments or innovations has the company implemented?"
        f"How clearly articulated and consistent is the company's strategy? Does the company have the capabilities required to execute its strategy? How well does the strategy address market opportunities and threats? Is there alignment between strategy, resource allocation, and organizational structure? What strategic tensions or trade- offs is the company managing? How adaptable is the strategy to changing market conditions?"
        f"What has been the primary driver of the company's historical growth? How effective has the company been at generating organic growth? What is the company's track record with acquisitions and integration? How sustainable are current growth rates given market size and competition? What new growth vectors is the company developing? How does the company's growth pattern compare to industry peers?"
        f"Is R&D investment growing, stable, or declining relative to revenue?  - How productive is the company's R&D compared to competitors?  - What major innovations are in the pipeline?  - How well does the R&D portfolio align with strategic priorities?  - Does the company have a track record of successfully commercializing R&D?  - What is the company's approach to protecting intellectual property?"
        f"Is the company a technology leader, fast follower, or laggard in its industry?  - How effectively does the company leverage technology for competitive advantage?  - What is the company's track record of successful technology implementation?  - How well integrated is technology strategy with overall business strategy?  - What emerging technologies present opportunities or threats?  - How does the company balance technology innovation with stability and security?"
        f"How likely is the company to pursue significant acquisitions? What types of acquisition targets would align with the company's strategy? How vulnerable is the company to being acquired? What would be the likely premium in a takeover scenario? How might potential M&A activity affect industry structure? What synergies might be realized in potential combinations?"
        f"Are promoters increasing or decreasing their ownership stake?- What might motivate recent changes in promoter holdings?- Is pledging increasing or decreasing, and what does this suggest?- What share price decline would potentially trigger margin calls on pledged shares?- How might changes in promoter holdings affect corporate control?- Do patterns suggest insider confidence or concern about future prospects?"
        f"What major new products are in development?  - How might these products impact the company's competitive positioning?  - What is the potential revenue contribution from the pipeline?  - What risks could delay or derail key product launches?  - How does the pipeline compare to competitor innovation efforts?  - Does the pipeline address emerging customer needs and market trends?"
        f"What aspects of the business model create elevated fraud risk?- Are there financial red flags that warrant further investigation?- How robust are the company's governance and control mechanisms?- Has the company or industry experienced significant fraud cases historically?- How transparent is management about challenges and setbacks?- What would be the potential impact of a major fraud or scandal?"
        f"What scenarios would most severely test the company's business model?- How would the company's financial position withstand severe stress?- What mitigating actions could management take in crisis scenarios?- How has the company performed during previous downturns?- Are there specific trigger events that could precipitate a crisis?- How does the company's resilience compare to key competitors?"
        f"How does the current P/E compare to historical ranges?  - Is the P/E premium or discount relative to peers justified?  - What earnings growth rate is implied by the current P/E?  - How cyclical are earnings, and how does this affect P/E interpretation?  - What catalysts might cause a P/E expansion or contraction?  - How sensitive is the P/E to changes in growth expectations?"
        f"How does the current P/B compare to historical ranges?  - Is the P/B premium or discount relative to peers justified by ROE differences?  - Does book value accurately reflect the true value of assets?  - Are there significant off-balance-sheet assets or liabilities?  - How has management historically allocated capital relative to book value?  - What level of ROE would justify the current P/B ratio?"
        f"How has ROE trended over time, and what has driven changes?  - Which component of the DuPont formula contributes most to ROE?  - Is current ROE sustainable or likely to revert to historical means?  - How does ROE compare to the company's cost of equity?  - Is high ROE achieved through excessive leverage or other risks?  - What investments or strategies could improve future ROE?"
        f"How has ROCE trended over time, and what has driven changes?  - Does ROCE exceed the company's cost of capital, indicating value creation?  - How does ROCE compare to industry peers?  - What investments or strategies could improve future ROCE?  - Is the company effectively allocating incremental capital?  - How cyclical is ROCE, and where are we in the cycle?"
        f"How has EBITDA and EBITDA margin trended over time?  - What factors have driven changes in EBITDA?  - How cyclical is EBITDA, and where are we in the cycle?  - Does EBITDA adequately reflect the company's true operational performance?  - What is the relationship between EBITDA and cash flow?  - How does the company's EBITDA quality compare to peers?"
        f"How has EV changed over time, and what has driven these changes? What portion of EV is represented by debt versus equity? How does the company's capital structure compare to peers? Are there significant non- operating assets or liabilities affecting EV? How might EV be affected by potential corporate actions? What is the relationship between EV and the company's underlying asset base?"
        f"How does the current EV/EBITDA compare to historical ranges? Is the EV/EBITDA premium or discount relative to peers justified? What EBITDA growth rate is implied by the current EV/EBITDA? How does the EV/EBITDA ratio compare to the company's historical M&A multiples? What catalysts might cause an EV/EBITDA expansion or contraction? How does the EV/EBITDA ratio compare to other valuation metrics?"
        f"How has revenue growth trended over time? What are the primary drivers of growth (price, volume, mix, acquisitions)? How does growth compare to the overall market and key competitors? Is growth accelerating, stable, or decelerating? How sustainable is the current growth trajectory? What is the relationship between revenue growth and profitability?"
        f"Are YoY growth rates accelerating, stable, or decelerating?  - How consistent are YoY trends across different metrics?  - What explains significant divergences between different YoY metrics?  - How do YoY comparisons adjust for industry or economic cycles?  - Are there any base effects distorting YoY comparisons?  - What do YoY trends suggest about competitive positioning?"
        f"How does recent QoQ performance compare to historical seasonal patterns? Are there emerging trends visible in QoQ data not yet apparent in YoY comparisons? What explains significant divergences between different QoQ metrics? How volatile are QoQ results, and what drives this volatility? Do QoQ trends suggest an inflection point in the business? How do QoQ results compare to management's internal targets?"
        f"What are the key drivers of value in the DCF model?  - How sensitive is the valuation to changes in key assumptions?  - What growth and profitability assumptions are implied by the current market price?  - How does the DCF valuation compare to market price and other valuation methods?  - What risks or opportunities are not adequately captured in the DCF model?  - How has the DCF valuation changed over time, and what has driven these changes?"
        f"How does the company's valuation compare to appropriate peers?  - Is any premium or discount to peers justified by fundamentals?  - Which valuation metrics are most appropriate for this company and industry?  - How has relative valuation changed over time?  - What catalysts might cause relative valuation to change?  - How do different peer selection criteria affect the relative valuation assessment?"

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

