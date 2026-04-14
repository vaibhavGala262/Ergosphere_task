from celery import shared_task
from celery.utils.log import get_task_logger

from .services import BookIngestionService, SeleniumScraperService

logger = get_task_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def scrape_books_task(self, pages: int = 1, start_url: str | None = None):
    self.update_state(state="STARTED", meta={"phase": "scraping", "message": "Starting scraper"})
    logger.info("Scrape task %s started (pages=%s)", self.request.id, pages)
    self.update_state(
        state="PROGRESS",
        meta={
            "phase": "scraping",
            "message": "Initializing browser and loading first page",
            "scraped_pages": 0,
            "total_pages": pages,
        },
    )

    def on_scrape_progress(page_number: int, total_pages: int, current_url: str):
        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "scraping",
                "message": f"Scraping page {page_number}/{total_pages}",
                "scraped_pages": page_number,
                "total_pages": total_pages,
                "current_url": current_url,
            },
        )

    scraped = SeleniumScraperService().scrape(pages=pages, start_url=start_url, progress_callback=on_scrape_progress)
    self.update_state(
        state="PROGRESS",
        meta={
            "phase": "ingestion",
            "message": f"Scraped {len(scraped)} records. Starting ingestion.",
            "scraped": len(scraped),
            "processed": 0,
        },
    )

    def on_progress(processed: int, total: int, book):
        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "ingestion",
                "message": f"Processed {processed}/{total}: {book.title}",
                "scraped": total,
                "processed": processed,
            },
        )

    books = BookIngestionService().ingest_scraped_books(scraped, progress_callback=on_progress)
    logger.info("Scrape task %s completed (saved=%s)", self.request.id, len(books))
    return {"books_saved": len(books)}
