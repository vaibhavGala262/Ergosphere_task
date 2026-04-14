from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("author", models.CharField(max_length=255)),
                ("rating", models.FloatField(default=0.0)),
                ("description", models.TextField()),
                ("url", models.URLField(unique=True)),
                ("ai_summary", models.TextField(blank=True)),
                ("genre", models.CharField(blank=True, max_length=100)),
                ("sentiment", models.CharField(blank=True, max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ChatHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(db_index=True, max_length=120)),
                ("question", models.TextField()),
                ("answer", models.TextField()),
                ("sources", models.JSONField(blank=True, default=list)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.CreateModel(
            name="BookChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chunk_text", models.TextField()),
                ("embedding_id", models.CharField(max_length=255, unique=True)),
                ("chunk_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "book",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chunks", to="books.book"),
                ),
            ],
            options={"ordering": ["chunk_order"]},
        ),
    ]
