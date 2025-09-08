# import asyncio
# from scraping.crawling.crawl import process_link
# from scraping.crawling.top_down_search_links import run_search
# from Research_agent.bottom_up import run_search
# from scraping.data_collect_summarize import summarized_data

# async def crawl_and_save(company_name):
#     print("🔍 Searching for links...")
#     links = run_search(company_name)
#     print(f"🌐 Found {len(links)} links.")

#     tasks = [process_link(link, company_name) for link in links]
#     await asyncio.gather(*tasks)
#     print("✅ Crawling and saving raw data complete.")

# def summarize(company_name):
#     print("📝 Summarizing collected data...")
#     # summarized_data.py runs on import, so just import it
#     import scraping.data_collect_summarize.summarized_data as sd
#     sd.summarize_company(company_name)
#     print("✅ Summarization complete.")

# if __name__ == "__main__":
#     company = "Keystone Realtors Limited"
#     asyncio.run(crawl_and_save(company))
#     summarize(company)


import asyncio
from scraping.crawling.crawl import process_link
from Research_agent.top_down.top_down_search_links import run_search as top_down_search
from Research_agent.bottom_up.bottom_up_search import run_search as bottom_up_search
from Research_agent.top_down.top_down_summarize import summarize_company as top_down_summarize
from Research_agent.bottom_up.bottom_up_summarize import summarize_company as bottom_up_summarize

async def parallel_search(company_name):
    """Run both top-down and bottom-up searches concurrently"""
    print("\n🔍 Starting parallel searches...")
    print("├─ Running top-down analysis")
    print("└─ Running bottom-up analysis")
    
    # Run both searches in parallel
    top_down_links = top_down_search(company_name)
    bottom_up_links = bottom_up_search(company_name)
    
    # Combine and deduplicate links
    all_links = list(set(top_down_links + bottom_up_links))
    print(f"\n🌐 Found {len(all_links)} unique links")
    
    # Process all links concurrently
    tasks = [process_link(link, company_name) for link in all_links]
    await asyncio.gather(*tasks)
    print("✅ Crawling and saving raw data complete")

def parallel_summarize(company_name):
    """Generate both top-down and bottom-up summaries"""
    print("\n📊 Generating summaries...")
    print("├─ Running top-down summarization")
    top_down_summarize(company_name)
    print("└─ Running bottom-up summarization")
    bottom_up_summarize(company_name)
    print("✅ Both summaries complete")

if __name__ == "__main__":
    company = "Keystone Realtors Limited"
    
    # Run the full pipeline
    asyncio.run(parallel_search(company))
    parallel_summarize(company)