"""
Custom static file serving views for debugging
"""
import os
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def serve_static_file(request, path):
    """Serve static files directly for debugging"""
    # Construct the full path to the static file
    static_file_path = os.path.join(settings.STATIC_ROOT, path)
    
    # Check if file exists
    if not os.path.exists(static_file_path):
        # Try in STATICFILES_DIRS
        for static_dir in settings.STATICFILES_DIRS:
            alt_path = os.path.join(static_dir, path)
            if os.path.exists(alt_path):
                static_file_path = alt_path
                break
        else:
            raise Http404(f"Static file not found: {path}")
    
    # Read the file
    try:
        with open(static_file_path, 'rb') as f:
            content = f.read()
    except Exception as e:
        raise Http404(f"Error reading file: {str(e)}")
    
    # Determine content type
    if path.endswith('.js'):
        content_type = 'application/javascript'
    elif path.endswith('.css'):
        content_type = 'text/css'
    elif path.endswith('.json'):
        content_type = 'application/json'
    elif path.endswith('.png'):
        content_type = 'image/png'
    elif path.endswith('.jpg') or path.endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif path.endswith('.ico'):
        content_type = 'image/x-icon'
    else:
        content_type = 'application/octet-stream'
    
    response = HttpResponse(content, content_type=content_type)
    response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    return response
