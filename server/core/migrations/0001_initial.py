# server/core/migrations/0001_initial.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RAGChunk',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('chunk_type', models.CharField(choices=[('profile', 'Profile'), ('document', 'Document')], max_length=20)),
                ('source', models.CharField(max_length=100)),
                ('embedding', models.JSONField(blank=True, default=list, help_text='embedding vector as json array')),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rag_chunks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'rag_chunks',
                'managed': True,
            },
        ),
        migrations.AddIndex(
            model_name='ragchunk',
            index=models.Index(fields=['user', 'chunk_type'], name='rag_chunks_user_id_chunk_type_idx'),
        ),
        migrations.AddIndex(
            model_name='ragchunk',
            index=models.Index(fields=['user', 'source'], name='rag_chunks_user_id_source_idx'),
        ),
        migrations.AddIndex(
            model_name='ragchunk',
            index=models.Index(fields=['updated_at'], name='rag_chunks_updated_at_idx'),
        ),
    ]