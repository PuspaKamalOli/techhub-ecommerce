# techhub/views.py
from django.http import HttpResponse, Http404
from django.db import connection

def serve_neon_db_media(request, path):
    """
    Renders an image natively from the NeonDB PostgreSQL techhub_media table.
    """
    with connection.cursor() as cursor:
        try:
            # We don't need to create the table here, it should exist if files were saved
            cursor.execute('SELECT data, content_type FROM techhub_media WHERE name = %s', [path])
            row = cursor.fetchone()
            if row:
                data, content_type = row
                # Fallback content_type if missing
                if not content_type:
                    import mimetypes
                    content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
                
                # Setup response with aggressive catching since DB hits for images are expensive
                response = HttpResponse(data, content_type=content_type)
                response['Cache-Control'] = 'public, max-age=31536000' # 1 year cache
                return response
        except Exception as e:
            pass
            
    raise Http404("Media file not found in Database")
