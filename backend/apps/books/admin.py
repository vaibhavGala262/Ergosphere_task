from django.contrib import admin

from .models import Book, BookChunk, ChatHistory

admin.site.register(Book)
admin.site.register(BookChunk)
admin.site.register(ChatHistory)
