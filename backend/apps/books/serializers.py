from rest_framework import serializers

from .models import Book, ChatHistory


class BookSerializer(serializers.ModelSerializer):
    description_preview = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "description",
            "description_preview",
            "url",
            "ai_summary",
            "genre",
            "sentiment",
            "created_at",
        ]

    def get_description_preview(self, obj: Book) -> str:
        return f"{obj.description[:160]}..." if len(obj.description) > 160 else obj.description


class UploadSerializer(serializers.Serializer):
    pages = serializers.IntegerField(min_value=1, max_value=50, default=1)
    start_url = serializers.URLField(required=False)


class QuerySerializer(serializers.Serializer):
    question = serializers.CharField()
    session_id = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(min_value=1, max_value=10, default=4)


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ["id", "session_id", "question", "answer", "sources", "timestamp"]
