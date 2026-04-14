import { Book, QueryResponse, UploadResponse, UploadTaskStatus } from "@/lib/types";

const API_BASE_URL =
  typeof window === "undefined"
    ? process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api"
    : process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listBooks(search = "", genre = ""): Promise<Book[]> {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (genre) params.set("genre", genre);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return fetchJson<Book[]>(`/books/${suffix}`);
  },
  getBook(id: string): Promise<Book> {
    return fetchJson<Book>(`/books/${id}/`);
  },
  recommendBooks(id: string): Promise<Book[]> {
    return fetchJson<Book[]>(`/books/${id}/recommend/`);
  },
  query(question: string, sessionId = ""): Promise<QueryResponse> {
    return fetchJson<QueryResponse>("/query/", {
      method: "POST",
      body: JSON.stringify({ question, session_id: sessionId })
    });
  },
  uploadBooks(pages = 2, startUrl = ""): Promise<UploadResponse> {
    return fetchJson<UploadResponse>("/books/upload/", {
      method: "POST",
      body: JSON.stringify({ pages, start_url: startUrl || undefined })
    });
  },
  getUploadTaskStatus(taskId: string): Promise<UploadTaskStatus> {
    return fetchJson<UploadTaskStatus>(`/books/upload/${taskId}/status/`);
  }
};
