import asyncio
import logging
import time
from typing import Optional
from crawl4ai import AsyncWebCrawler
from scraping.data_collect_summarize.raw_data import save_raw_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceOptimizedCrawler:
    def __init__(self, max_concurrent=6, delay_between_requests=0.5, timeout=10):
        """
        Initialize crawler with resource optimization settings.
        
        Args:
            max_concurrent: Maximum concurrent requests (reduced from default)
            delay_between_requests: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.max_concurrent = max_concurrent
        self.delay_between_requests = delay_between_requests
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.last_request_time = 0
        
    async def _rate_limit(self):
        """Implement rate limiting to reduce CPU load."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay_between_requests:
            wait_time = self.delay_between_requests - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

    async def process_link(self, url: str, company_name: str) -> bool:
        """
        Process a single link with resource optimization.
        
        Returns:
            bool: Success status
        """
        async with self.semaphore:  # Limit concurrent requests
            try:
                await self._rate_limit()  # Rate limiting
                
                extraction_prompt = (
                    f"Extract only the parts of the article that are directly related to the company named '{company_name}'. "
                    "Ignore general market commentary, unrelated companies, or boilerplate site content. "
                    "Your goal is to extract a company-specific summary from the article content. "
                    "Do not include data about other companies, sectors, or general economic commentary."
                )
                
                # Configure crawler with resource-friendly settings
                crawler_config = {
                    'headless': True,  # Reduce memory usage
                    'browser_type': 'chromium',  # Most efficient option
                    'verbose': False,  # Reduce logging overhead
                    'delay_before_return_html': 0.5,  # Minimal delay
                }
                
                async with AsyncWebCrawler(**crawler_config) as crawler:
                    # Use timeout to prevent hanging requests
                    result = await asyncio.wait_for(
                        crawler.arun(
                            url=url, 
                            instructions=extraction_prompt,
                            word_count_threshold=50,  # Skip very short content
                            bypass_cache=False,  # Use cache when possible
                            process_iframes=False,  # Reduce processing load
                            remove_overlay_elements=True,  # Clean content faster
                        ),
                        timeout=self.timeout
                    )
                    
                    raw_content = result.markdown
                    
                    # Quick content validation to avoid processing empty/low-quality content
                    if len(raw_content.strip()) < 100:
                        logger.warning(f"Skipping {url}: Content too short")
                        return False
                    
                    logger.info(f"📄 Extracted from: {url} ({len(raw_content)} chars)")
                    
                    # Save to database (this runs in the background)
                    await asyncio.get_event_loop().run_in_executor(
                        None, save_raw_data, company_name, url, raw_content
                    )
                    
                    logger.info("✅ Saved to MongoDB")
                    return True
                    
            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout processing {url}")
                return False
            except Exception as e:
                logger.error(f"❌ Error processing {url}: {str(e)[:100]}")
                return False
            finally:
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

    async def process_multiple_links(self, url_company_pairs: list) -> dict:
        """
        Process multiple links with optimized resource usage.
        
        Args:
            url_company_pairs: List of (url, company_name) tuples
            
        Returns:
            dict: Results summary
        """
        start_time = time.time()
        total_links = len(url_company_pairs)
        successful = 0
        failed = 0
        
        logger.info(f"🚀 Starting processing {total_links} links with max_concurrent={self.max_concurrent}")
        
        # Process in batches to prevent memory buildup
        batch_size = min(10, self.max_concurrent * 3)
        
        for i in range(0, total_links, batch_size):
            batch = url_company_pairs[i:i + batch_size]
            logger.info(f"📦 Processing batch {i//batch_size + 1}/{(total_links-1)//batch_size + 1}")
            
            # Process batch
            tasks = [self.process_link(url, company) for url, company in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count results
            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                elif result:
                    successful += 1
                else:
                    failed += 1
            
            # Memory cleanup between batches
            await asyncio.sleep(0.5)
            
            # Progress logging
            processed = i + len(batch)
            logger.info(f"📊 Progress: {processed}/{total_links} ({processed/total_links*100:.1f}%)")
        
        elapsed_time = time.time() - start_time
        
        return {
            'total_processed': total_links,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_links if total_links > 0 else 0,
            'elapsed_time': elapsed_time,
            'avg_time_per_link': elapsed_time / total_links if total_links > 0 else 0
        }


# ====================== BACKWARD COMPATIBILITY FUNCTIONS ======================

async def process_link(url: str, company_name: str) -> bool:
    """
    Single link processing function with optimized settings.
    Maintains backward compatibility with your existing main.py imports.
    """
    crawler = ResourceOptimizedCrawler(max_concurrent=1, delay_between_requests=1.0)
    return await crawler.process_link(url, company_name)


async def process_links_batch(url_company_pairs: list, max_concurrent: int = 2) -> dict:
    """
    Batch processing function for multiple links.
    
    Args:
        url_company_pairs: List of (url, company_name) tuples
        max_concurrent: Maximum concurrent requests (keep low for CPU optimization)
    """
    crawler = ResourceOptimizedCrawler(
        max_concurrent=max_concurrent,
        delay_between_requests=1.5,  # Increased delay for stability
        timeout=20  # Reasonable timeout
    )
    
    return await crawler.process_multiple_links(url_company_pairs)


# ====================== LEGACY FUNCTION (for existing code compatibility) ======================

# Your original function is preserved for any existing imports
# but now internally uses the optimized crawler
async def process_link_legacy(url, company_name):
    """
    Legacy function that maintains your original signature.
    Now internally uses optimized crawler.
    """
    extraction_prompt = (
        f"Extract only the parts of the article that are directly related to the company named '{company_name}'. "
        "Ignore general market commentary, unrelated companies, or boilerplate site content. "
        "Your goal is to extract a company-specific summary from the article content. "
        "Do not include data about other companies, sectors, or general economic commentary."
    )
    
    # Use optimized crawler instead of direct AsyncWebCrawler
    crawler = ResourceOptimizedCrawler(max_concurrent=1, delay_between_requests=1.0, timeout=15)
    
    try:
        success = await crawler.process_link(url, company_name)
        if success:
            print(f"\n📄 Extracted from: {url}")
            print("✅ Saved to MongoDB")
        return success
    except Exception as e:
        print(f"❌ Error processing {url}: {e}")
        return False


# ====================== EXAMPLE USAGE ======================

async def main():
    """Example usage of the optimized crawler."""
    # Example data
    links_to_process = [
        ("https://example1.com/article1", "Company A"),
        ("https://example2.com/article2", "Company B"),
        # ... more links
    ]
    
    # Process with resource optimization
    results = await process_links_batch(links_to_process, max_concurrent=2)
    
    print(f"""
    📊 Processing Results:
    ✅ Successful: {results['successful']}
    ❌ Failed: {results['failed']}
    📈 Success Rate: {results['success_rate']:.1%}
    ⏱️ Total Time: {results['elapsed_time']:.1f}s
    ⚡ Avg per link: {results['avg_time_per_link']:.1f}s
    """)


if __name__ == "__main__":
    asyncio.run(main())