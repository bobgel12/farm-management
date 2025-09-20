"""
Custom static file serving for React app
"""
import os
import mimetypes
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

@require_http_methods(["GET"])
@cache_control(max_age=31536000)  # 1 year cache
def serve_static_file(request, path):
    """Serve static files directly with proper MIME types"""
    print(f"🔍 Static file request: {path}")
    
    # Try staticfiles directory first (where collectstatic puts files)
    static_file_path = os.path.join(settings.STATIC_ROOT, path)
    print(f"📁 Trying staticfiles path: {static_file_path}")
    
    if not os.path.exists(static_file_path):
        print(f"❌ Not found in staticfiles, trying static directories...")
        # Try static directory (where React build is copied)
        for static_dir in settings.STATICFILES_DIRS:
            alt_path = os.path.join(static_dir, path)
            print(f"📁 Trying static dir path: {alt_path}")
            if os.path.exists(alt_path):
                static_file_path = alt_path
                print(f"✅ Found in static dir: {alt_path}")
                break
        else:
            print(f"❌ File not found in any static directory")
            raise Http404(f"Static file not found: {path}")
    else:
        print(f"✅ Found in staticfiles: {static_file_path}")
    
    # Read the file
    try:
        with open(static_file_path, 'rb') as f:
            content = f.read()
        print(f"✅ File read successfully, size: {len(content)} bytes")
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        raise Http404(f"Error reading file: {str(e)}")
    
    # Determine content type based on file extension
    content_type, _ = mimetypes.guess_type(static_file_path)
    if not content_type:
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
        elif path.endswith('.svg'):
            content_type = 'image/svg+xml'
        else:
            content_type = 'application/octet-stream'
    
    print(f"📄 Content type: {content_type}")
    response = HttpResponse(content, content_type=content_type)
    response['Cache-Control'] = 'public, max-age=31536000'
    return response
