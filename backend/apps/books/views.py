from uuid import uuid4

from django.core.cache import cache
from django.db.models import Q
from celery.result import AsyncResult
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.services import RecommendationService, RAGService
from apps.ai.tasks import scrape_books_task

from .models import Book, ChatHistory
from .serializers import BookSerializer, QuerySerializer, UploadSerializer


class BookListView(generics.ListAPIView):
    serializer_class = BookSerializer

    def get_queryset(self):
        queryset = Book.objects.all()
        search = self.request.query_params.get("search")
        genre = self.request.query_params.get("genre")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(author__icontains=search))
        if genre:
            queryset = queryset.filter(genre__iexact=genre)
        return queryset.distinct()


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class RecommendBooksView(APIView):
    def get(self, request, pk: int):
        books = RecommendationService().recommend(book_id=pk)
        return Response(BookSerializer(books, many=True).data)


class UploadBooksView(APIView):
    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = scrape_books_task.delay(**serializer.validated_data)
        return Response({"message": "Scraping started", "task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class UploadTaskStatusView(APIView):
    def get(self, request, task_id: str):
        task = AsyncResult(task_id)
        payload = {
            "task_id": task_id,
            "status": task.status,
            "ready": task.ready(),
            "successful": task.successful() if task.ready() else False,
            "result": task.result if task.ready() and not isinstance(task.result, Exception) else None,
        }
        if task.failed():
            payload["error"] = str(task.result)
        return Response(payload)


class QueryView(APIView):
    def post(self, request):
        serializer = QuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        session_id = payload.get("session_id") or str(uuid4())
        cache_key = f"qa:{session_id}:{payload['question']}:{payload['top_k']}"
        cached = cache.get(cache_key)
        if cached:
            return Response({**cached, "session_id": session_id, "cached": True})

        answer = RAGService().answer_question(payload["question"], top_k=payload["top_k"])
        ChatHistory.objects.create(
            session_id=session_id,
            question=payload["question"],
            answer=answer["answer"],
            sources=answer["sources"],
        )
        cache.set(cache_key, answer, timeout=1800)
        return Response({**answer, "session_id": session_id, "cached": False})
