import asyncio
from scraping.crawling.crawl import process_link
from scraping.crawling.search_links import run_search
from scraping.data_collect_summarize import summarized_data

async def crawl_and_save(company_name):
    print("🔍 Searching for links...")
    links = run_search()
    print(f"🌐 Found {len(links)} links.")

    tasks = [process_link(link) for link in links]
    await asyncio.gather(*tasks)
    print("✅ Crawling and saving raw data complete.")

def summarize():
    print("📝 Summarizing collected data...")
    # summarized_data.py runs on import, so just import it
    import scraping.data_collect_summarize.summarized_data
    print("✅ Summarization complete.")

if __name__ == "__main__":
    company = "Ultratech Cement full search"
    asyncio.run(crawl_and_save(company))
    summarize()