from celery import shared_task

from .services import BookIngestionService, SeleniumScraperService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def scrape_books_task(self, pages: int = 1, start_url: str | None = None):
    scraped = SeleniumScraperService().scrape(pages=pages, start_url=start_url)
    books = BookIngestionService().ingest_scraped_books(scraped)
    return {"books_saved": len(books)}
