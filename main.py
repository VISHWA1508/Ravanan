import asyncio
from scraping.crawling.crawl import process_link
from scraping.crawling.search_links import run_search
from scraping.data_collect_summarize import summarized_data

async def crawl_and_save(company_name):
    print("🔍 Searching for links...")
    links = run_search(company_name)
    print(f"🌐 Found {len(links)} links.")

    tasks = [process_link(link, company_name) for link in links]
    await asyncio.gather(*tasks)
    print("✅ Crawling and saving raw data complete.")

def summarize(company_name):
    print("📝 Summarizing collected data...")
    # summarized_data.py runs on import, so just import it
    import scraping.data_collect_summarize.summarized_data as sd
    sd.summarize_company(company_name)
    print("✅ Summarization complete.")

if __name__ == "__main__":
    company = "Zomato"
    asyncio.run(crawl_and_save(company))
    summarize(company)