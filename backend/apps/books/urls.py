from django.urls import path

from .views import BookDetailView, BookListView, QueryView, RecommendBooksView, UploadBooksView, UploadTaskStatusView

urlpatterns = [
    path("books/", BookListView.as_view(), name="book-list"),
    path("books/upload/", UploadBooksView.as_view(), name="book-upload"),
    path("books/upload/<str:task_id>/status/", UploadTaskStatusView.as_view(), name="book-upload-task-status"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book-detail"),
    path("books/<int:pk>/recommend/", RecommendBooksView.as_view(), name="book-recommend"),
    path("query/", QueryView.as_view(), name="query"),
]
