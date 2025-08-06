import asyncio
from crawl4ai import AsyncWebCrawler
from scraping.data_collect_summarize.raw_data import save_raw_data




async def process_link(url, company_name):
    extraction_prompt = (
    f"Extract only the parts of the article that are directly related to the company named '{company_name}'. "
    "Ignore general market commentary, unrelated companies, or boilerplate site content. "
    "Your goal is to extract a company-specific summary from the article content. "
    "Do not include data about other companies, sectors, or general economic commentary."
)
    async with AsyncWebCrawler() as crawler:
        try:
            result = await crawler.arun(url=url, instructions=extraction_prompt)
            raw_content = result.markdown
            print(f"\n📄 Extracted from: {url}\n{raw_content[:300]}...\n")
            save_raw_data(company_name, url, raw_content)
            print("✅ Saved to MongoDB")
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")

