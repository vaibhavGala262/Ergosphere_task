from __future__ import annotations

import random
import time
from dataclasses import dataclass
from functools import wraps
from typing import Iterable
from uuid import uuid4

import chromadb
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.db.models import QuerySet
from google import genai
from openai import OpenAI
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from sentence_transformers import SentenceTransformer
from webdriver_manager.chrome import ChromeDriverManager

from apps.books.models import Book, BookChunk


@dataclass
class ChunkPayload:
    text: str
    order: int


def _is_rate_limited_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {429, 503}:
        return True
    message = str(exc).lower()
    return any(
        token in message
        for token in [
            "429",
            "503",
            "rate limit",
            "resource_exhausted",
            "too many requests",
            "service unavailable",
            "quota",
        ]
    )


def _with_rate_limit_retries(max_attempts: int = 3, base_delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if not _is_rate_limited_error(exc) or attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2**attempt) + random.uniform(0.1, 0.6)
                    time.sleep(delay)
            return func(*args, **kwargs)

        return wrapper

    return decorator


class EmbeddingService:
    def __init__(self) -> None:
        self.provider = (settings.EMBEDDING_PROVIDER or "sentence-transformers").strip().lower()
        self.model_name = settings.EMBEDDING_MODEL
        self._client = None
        self._openai = None
        self._gemini = None

    def _get_sentence_model(self) -> SentenceTransformer:
        if self._client is None:
            self._client = SentenceTransformer(self.model_name)
        return self._client

    def _get_openai(self) -> OpenAI:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")
        if self._openai is None:
            self._openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

    def _get_gemini(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        if self._gemini is None:
            self._gemini = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._gemini

    @staticmethod
    def _extract_gemini_embeddings(response) -> list[list[float]]:
        # Supports current and slightly older/alternate SDK response shapes.
        if hasattr(response, "embeddings") and response.embeddings:
            return [list(item.values) for item in response.embeddings if hasattr(item, "values")]
        if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
            return [list(response.embedding.values)]
        return []

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider == "openai":
            model_name = settings.OPENAI_EMBEDDING_MODEL or self.model_name
            response = self._embed_openai(model_name, texts)
            return [row.embedding for row in response.data]
        if self.provider == "gemini":
            model_name = settings.GEMINI_EMBEDDING_MODEL or self.model_name
            response = self._embed_gemini(model_name, texts)
            embeddings = self._extract_gemini_embeddings(response)
            if embeddings:
                return embeddings
            raise ValueError("Gemini embedding response did not include vector values.")
        return self._get_sentence_model().encode(texts, normalize_embeddings=True).tolist()

    @_with_rate_limit_retries()
    def _embed_openai(self, model_name: str, texts: list[str]):
        return self._get_openai().embeddings.create(model=model_name, input=texts)

    @_with_rate_limit_retries()
    def _embed_gemini(self, model_name: str, texts: list[str]):
        return self._get_gemini().models.embed_content(model=model_name, contents=texts)


class ChromaService:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(name="book_chunks")

    def upsert_chunks(self, book: Book, chunks: list[ChunkPayload], embeddings: list[list[float]]) -> None:
        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict] = []
        for chunk, embedding in zip(chunks, embeddings):
            embedding_id = f"book-{book.id}-chunk-{chunk.order}-{uuid4().hex[:8]}"
            ids.append(embedding_id)
            docs.append(chunk.text)
            metas.append({"book_id": book.id, "title": book.title, "author": book.author, "url": book.url})
            BookChunk.objects.create(
                book=book,
                chunk_text=chunk.text,
                embedding_id=embedding_id,
                chunk_order=chunk.order,
            )
        self.collection.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)

    def query(self, embedding: list[float], top_k: int = 4) -> dict:
        try:
            return self.collection.query(query_embeddings=[embedding], n_results=top_k)
        except Exception:
            return {"documents": [[]], "metadatas": [[]]}


class SemanticChunker:
    def __init__(self, max_chars: int = 320, overlap_sentences: int = 1) -> None:
        self.max_chars = max_chars
        self.overlap_sentences = overlap_sentences
        self.embedder = EmbeddingService()

    def chunk(self, text: str) -> list[ChunkPayload]:
        sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".") if sentence.strip()]
        if not sentences:
            return []
        sentence_embeddings = self.embedder.embed(sentences)
        chunks: list[ChunkPayload] = []
        current: list[str] = []
        order = 0

        for index, sentence in enumerate(sentences):
            current.append(sentence)
            joined = ". ".join(current)
            next_similarity_drop = False
            if index < len(sentences) - 1:
                current_vec = sentence_embeddings[index]
                next_vec = sentence_embeddings[index + 1]
                cosine = sum(a * b for a, b in zip(current_vec, next_vec))
                next_similarity_drop = cosine < 0.55
            if len(joined) >= self.max_chars or next_similarity_drop:
                chunks.append(ChunkPayload(text=joined.strip() + ".", order=order))
                order += 1
                current = current[-self.overlap_sentences :].copy() if self.overlap_sentences else []

        if current:
            chunks.append(ChunkPayload(text=". ".join(current).strip() + ".", order=order))

        deduped: list[ChunkPayload] = []
        seen = set()
        for chunk in chunks:
            if chunk.text not in seen:
                seen.add(chunk.text)
                deduped.append(chunk)
        return deduped


class LLMService:
    def __init__(self) -> None:
        self.provider = (settings.LLM_PROVIDER or "openai").strip().lower()
        self.model = settings.OPENAI_CHAT_MODEL or "gpt-4o-mini"
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.gemini = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

    def complete(self, prompt: str, system: str = "You are a precise assistant for book analysis.") -> str:
        if self.provider == "openai" and self.client:
            response = self._complete_openai(prompt, system)
            return response.choices[0].message.content or ""
        if self.provider == "gemini" and self.gemini:
            response = self._complete_gemini(prompt, system)
            if hasattr(response, "text") and response.text:
                return response.text
        return (
            "LLM provider not configured. Set OPENAI_API_KEY for OpenAI or GEMINI_API_KEY for Gemini."
        )

    @_with_rate_limit_retries(max_attempts=2, base_delay=0.8)
    def _complete_openai(self, prompt: str, system: str):
        return self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )

    @_with_rate_limit_retries(max_attempts=2, base_delay=0.8)
    def _complete_gemini(self, prompt: str, system: str):
        gemini_model = settings.GEMINI_CHAT_MODEL or "gemini-2.5-flash"
        combined_prompt = f"System instruction: {system}\n\nUser prompt: {prompt}"
        return self.gemini.models.generate_content(model=gemini_model, contents=combined_prompt)


class BookIntelligenceService:
    genres = ["Fantasy", "Mystery", "Romance", "Science Fiction", "Historical Fiction", "Non-fiction"]

    def __init__(self) -> None:
        self.llm = LLMService()

    def summarize(self, description: str) -> str:
        prompt = f"Summarize this book description in 3 concise bullet-style sentences:\n{description}"
        try:
            summary = self.llm.complete(prompt).strip()
            if summary:
                return summary
        except Exception:
            pass
        sentences = [line.strip() for line in description.replace("\n", " ").split(".") if line.strip()]
        fallback = ". ".join(sentences[:3]).strip()
        return (fallback + ".") if fallback else "Summary unavailable."

    def classify_genre(self, description: str) -> str:
        prompt = (
            f"Choose the single best genre from {', '.join(self.genres)} "
            f"for this description. Return only the genre.\n{description}"
        )
        try:
            result = self.llm.complete(prompt).strip()
        except Exception:
            return "General"
        return result if result in self.genres else "General"

    def sentiment(self, description: str) -> str:
        positive_words = {"hope", "love", "joy", "wonder", "friendship", "inspiring"}
        negative_words = {"fear", "war", "loss", "pain", "betrayal", "dark"}
        score = sum(word in description.lower() for word in positive_words) - sum(
            word in description.lower() for word in negative_words
        )
        if score > 0:
            return "Positive"
        if score < 0:
            return "Dark"
        return "Neutral"


class RAGService:
    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.chroma = ChromaService()
        self.llm = LLMService()

    def index_book(self, book: Book) -> None:
        if book.chunks.exists():
            return
        chunks = SemanticChunker().chunk(book.description)
        if not chunks:
            return
        embeddings = self.embedder.embed([chunk.text for chunk in chunks])
        self.chroma.upsert_chunks(book, chunks, embeddings)

    def answer_question(self, question: str, top_k: int = 4) -> dict:
        try:
            query_embedding = self.embedder.embed([question])[0]
        except Exception:
            return {
                "answer": "The AI service is currently rate-limited. Please retry in a moment.",
                "sources": [],
            }
        result = self.chroma.query(query_embedding, top_k=top_k)
        documents = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        if not documents:
            return {"answer": "No indexed book context is available yet. Scrape and ingest books first.", "sources": []}
        context = "\n\n".join(
            f"Source: {meta['title']} by {meta['author']} ({meta['url']})\n{doc}"
            for doc, meta in zip(documents, metas)
        )
        prompt = (
            "Answer the user question using the provided context only. "
            "If the answer is uncertain, say so.\n\n"
            f"Question: {question}\n\nContext:\n{context}"
        )
        try:
            answer = self.llm.complete(prompt)
        except Exception:
            answer = "The AI service is currently rate-limited. Please retry in a moment."
        sources = [
            {"title": meta["title"], "author": meta["author"], "url": meta["url"], "excerpt": doc[:180]}
            for doc, meta in zip(documents, metas)
        ]
        return {"answer": answer, "sources": sources}


class RecommendationService:
    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.chroma = ChromaService()

    def recommend(self, book_id: int, top_k: int = 4) -> QuerySet[Book]:
        book = Book.objects.get(pk=book_id)
        try:
            query_embedding = self.embedder.embed([book.description])[0]
        except Exception:
            return Book.objects.none()
        result = self.chroma.query(query_embedding, top_k=top_k + 1)
        ids: list[int] = []
        for meta in result.get("metadatas", [[]])[0]:
            related_book_id = meta.get("book_id")
            if related_book_id and related_book_id != book.id and related_book_id not in ids:
                ids.append(related_book_id)
        return Book.objects.filter(id__in=ids[:top_k])


class SeleniumScraperService:
    def __init__(self, base_url: str | None = None, retries: int = 3) -> None:
        self.base_url = base_url or settings.SCRAPER_BASE_URL
        self.retries = retries

    def _driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if settings.SELENIUM_REMOTE_URL:
            driver = webdriver.Remote(command_executor=settings.SELENIUM_REMOTE_URL, options=options)
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)
            return driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        return driver

    def scrape(self, pages: int = 1, start_url: str | None = None, progress_callback=None) -> list[dict]:
        url = start_url or self.base_url
        books: list[dict] = []
        try:
            driver = self._driver()
        except Exception:
            for page_number in range(1, pages + 1):
                if progress_callback:
                    progress_callback(page_number, pages, url)
                html = self._scrape_page(url)
                books.extend(self._extract_books(html, url))
                next_url = self._find_next_url(html, url)
                if not next_url:
                    break
                url = next_url
            return books

        try:
            for page_number in range(1, pages + 1):
                if progress_callback:
                    progress_callback(page_number, pages, url)
                html = self._scrape_with_driver(driver, url)
                books.extend(self._extract_books(html, url))
                next_url = self._find_next_url(html, url)
                if not next_url:
                    break
                url = next_url
        finally:
            driver.quit()
        return books

    def _scrape_with_driver(self, driver, url: str) -> str:
        last_error = None
        for attempt in range(self.retries):
            try:
                driver.get(url)
                time.sleep(1)
                return driver.page_source
            except WebDriverException as exc:
                last_error = exc
                time.sleep(2**attempt)
        raise last_error

    def _scrape_page(self, url: str) -> str:
        last_error = None
        for attempt in range(self.retries):
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(2**attempt)
        raise last_error

    def _find_next_url(self, html: str, page_url: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        next_anchor = soup.select_one("li.next a")
        if not next_anchor:
            return None
        return requests.compat.urljoin(page_url, next_anchor.get("href", ""))

    def _extract_books(self, html: str, page_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for card in soup.select("article.product_pod"):
            title_node = card.select_one("h3 a")
            rating_node = card.select_one("p.star-rating")
            title = title_node.get("title", title_node.text.strip())
            if settings.SCRAPER_ENRICH_EXTERNAL:
                description = self._fetch_description(title_node.get("href", ""))
                author = self._resolve_author(title)
            else:
                description = "Description unavailable."
                author = "Unknown Author"
            results.append(
                {
                    "title": title,
                    "author": author,
                    "rating": self._rating_to_float(rating_node.get("class", [])),
                    "description": description,
                    "url": requests.compat.urljoin(page_url, title_node.get("href", "")),
                }
            )
        return results

    def _resolve_author(self, title: str) -> str:
        try:
            response = requests.get(
                "https://openlibrary.org/search.json",
                params={"title": title, "limit": 1},
                timeout=8,
            )
            response.raise_for_status()
            docs = response.json().get("docs", [])
            if docs and docs[0].get("author_name"):
                return docs[0]["author_name"][0]
        except requests.RequestException:
            pass
        return "Unknown Author"

    def _fetch_description(self, book_url: str) -> str:
        absolute_url = requests.compat.urljoin(self.base_url, book_url)
        try:
            response = requests.get(absolute_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            node = soup.select_one("#product_description ~ p")
            return node.text.strip() if node else "Description unavailable."
        except requests.RequestException:
            return "Description unavailable."

    def _rating_to_float(self, class_names: Iterable[str]) -> float:
        mapping = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0}
        for name in class_names:
            if name in mapping:
                return mapping[name]
        return 0.0


class BookIngestionService:
    def __init__(self) -> None:
        self.intelligence = BookIntelligenceService()
        self.rag = RAGService()

    def ingest_scraped_books(self, records: list[dict], progress_callback=None) -> list[Book]:
        saved_books = []
        total = len(records)
        for index, record in enumerate(records, start=1):
            book, created = Book.objects.get_or_create(
                url=record["url"],
                defaults={
                    "title": record["title"],
                    "author": record["author"],
                    "rating": record["rating"],
                    "description": record["description"],
                },
            )
            if created:
                if settings.INGEST_ENABLE_LLM:
                    book.ai_summary = self.intelligence.summarize(book.description)
                    book.genre = self.intelligence.classify_genre(book.description)
                else:
                    preview = [line.strip() for line in book.description.replace("\n", " ").split(".") if line.strip()]
                    book.ai_summary = (". ".join(preview[:2]).strip() + ".") if preview else "Summary unavailable."
                    book.genre = "General"
                book.sentiment = self.intelligence.sentiment(book.description)
                book.save(update_fields=["ai_summary", "genre", "sentiment"])
                if settings.INGEST_ENABLE_EMBEDDINGS:
                    try:
                        self.rag.index_book(book)
                    except Exception:
                        # Preserve successful scrape even if embedding provider is temporarily throttled.
                        pass
            saved_books.append(book)
            if progress_callback:
                progress_callback(index, total, book)
        return saved_books
