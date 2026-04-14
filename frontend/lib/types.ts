export type Book = {
  id: number;
  title: string;
  author: string;
  rating: number;
  description: string;
  description_preview: string;
  url: string;
  ai_summary: string;
  genre: string;
  sentiment: string;
  created_at: string;
};

export type SourceCitation = {
  title: string;
  author: string;
  url: string;
  excerpt: string;
};

export type QueryResponse = {
  answer: string;
  sources: SourceCitation[];
  session_id: string;
  cached: boolean;
};

export type UploadResponse = {
  message: string;
  task_id: string;
};

export type UploadTaskStatus = {
  task_id: string;
  status: string;
  ready: boolean;
  successful: boolean;
  result: { books_saved: number } | null;
  error?: string;
};
