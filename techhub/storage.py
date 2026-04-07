# techhub/storage.py
import urllib.parse
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.db import connection
from django.utils.deconstruct import deconstructible

@deconstructible
class NeonDatabaseStorage(Storage):
    def _create_table_if_not_exists(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS techhub_media (
                name VARCHAR(255) PRIMARY KEY,
                content_type VARCHAR(100),
                data BYTEA,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def _save(self, name, content):
        file_bytes = content.read()
        content_type = getattr(content, 'content_type', 'application/octet-stream')
        # If it's a Django file wrapper, it might have content_type, otherwise guess or default
        if not hasattr(content, 'content_type'):
            import mimetypes
            guessed_type, _ = mimetypes.guess_type(name)
            content_type = guessed_type or 'application/octet-stream'

        with connection.cursor() as cursor:
            self._create_table_if_not_exists(cursor)
            cursor.execute('''
                INSERT INTO techhub_media (name, content_type, data) 
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data, content_type = EXCLUDED.content_type
            ''', [name, content_type, file_bytes])
        return name

    def _open(self, name, mode='rb'):
        with connection.cursor() as cursor:
            self._create_table_if_not_exists(cursor)
            cursor.execute('SELECT data FROM techhub_media WHERE name = %s', [name])
            row = cursor.fetchone()
            if row:
                return ContentFile(row[0])
            raise FileNotFoundError(f"File {name} not found in database.")

    def exists(self, name):
        with connection.cursor() as cursor:
            self._create_table_if_not_exists(cursor)
            cursor.execute('SELECT 1 FROM techhub_media WHERE name = %s', [name])
            return cursor.fetchone() is not None

    def url(self, name):
        # Allow slashes to be part of the URL path natively
        return f'/db-media/{name}'
