"""
Cloudinary service for handling image uploads and deletions.
"""
import logging
import base64
from io import BytesIO
from django.conf import settings

logger = logging.getLogger(__name__)


def is_cloudinary_configured():
    """Check if Cloudinary is properly configured."""
    return bool(
        settings.CLOUDINARY_CLOUD_NAME and 
        settings.CLOUDINARY_API_KEY and 
        settings.CLOUDINARY_API_SECRET
    )


def upload_photo(file_data, folder='issue_photos', resource_type='image'):
    """
    Upload a photo to Cloudinary.
    
    Args:
        file_data: Either a file object, base64 string, or URL
        folder: Cloudinary folder to store the image
        resource_type: Type of resource (image, video, etc.)
    
    Returns:
        dict with 'url' and 'public_id' on success
        None on failure
    """
    if not is_cloudinary_configured():
        logger.warning("Cloudinary is not configured, using placeholder")
        return {
            'url': 'https://via.placeholder.com/400x300?text=Photo+Upload+Disabled',
            'public_id': 'placeholder'
        }
    
    try:
        import cloudinary.uploader
        
        # Prepare upload options
        options = {
            'folder': folder,
            'resource_type': resource_type,
            'transformation': [
                {'width': 1200, 'height': 1200, 'crop': 'limit'},  # Max size
                {'quality': 'auto:good'},  # Auto quality optimization
                {'fetch_format': 'auto'}  # Auto format for browser
            ]
        }
        
        # Handle different input types
        if isinstance(file_data, str):
            if file_data.startswith('data:'):
                # Base64 data URL
                result = cloudinary.uploader.upload(file_data, **options)
            elif file_data.startswith('http'):
                # URL
                result = cloudinary.uploader.upload(file_data, **options)
            else:
                # Assume raw base64
                result = cloudinary.uploader.upload(
                    f"data:image/jpeg;base64,{file_data}",
                    **options
                )
        else:
            # File object
            result = cloudinary.uploader.upload(file_data, **options)
        
        logger.info(f"Photo uploaded to Cloudinary: {result.get('public_id')}")
        
        return {
            'url': result.get('secure_url') or result.get('url'),
            'public_id': result.get('public_id')
        }
        
    except Exception as e:
        logger.error(f"Error uploading photo to Cloudinary: {str(e)}")
        return None


def delete_photo(public_id, resource_type='image'):
    """
    Delete a photo from Cloudinary.
    
    Args:
        public_id: The Cloudinary public ID of the image
        resource_type: Type of resource
    
    Returns:
        True on success, False on failure
    """
    if not is_cloudinary_configured():
        logger.warning("Cloudinary is not configured")
        return True  # Return success for placeholder images
    
    if public_id == 'placeholder':
        return True  # Skip placeholder images
    
    try:
        import cloudinary.uploader
        
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        
        if result.get('result') == 'ok':
            logger.info(f"Photo deleted from Cloudinary: {public_id}")
            return True
        else:
            logger.warning(f"Failed to delete photo from Cloudinary: {public_id}, result: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting photo from Cloudinary: {str(e)}")
        return False


def get_photo_url(public_id, width=None, height=None, crop='fill'):
    """
    Generate a Cloudinary URL with optional transformations.
    
    Args:
        public_id: The Cloudinary public ID
        width: Desired width
        height: Desired height
        crop: Crop mode (fill, fit, limit, etc.)
    
    Returns:
        Transformed URL string
    """
    if not is_cloudinary_configured():
        return f"https://via.placeholder.com/{width or 400}x{height or 300}"
    
    if public_id == 'placeholder':
        return f"https://via.placeholder.com/{width or 400}x{height or 300}"
    
    try:
        import cloudinary
        
        transformations = []
        if width or height:
            transform = {'crop': crop}
            if width:
                transform['width'] = width
            if height:
                transform['height'] = height
            transformations.append(transform)
        
        url, _ = cloudinary.CloudinaryImage(public_id).build_url(transformation=transformations)
        return url
        
    except Exception as e:
        logger.error(f"Error generating Cloudinary URL: {str(e)}")
        return None


def upload_multiple_photos(files, folder='issue_photos'):
    """
    Upload multiple photos to Cloudinary.
    
    Args:
        files: List of file objects or base64 strings
        folder: Cloudinary folder
    
    Returns:
        List of dicts with 'url' and 'public_id' for successful uploads
    """
    results = []
    for file_data in files:
        result = upload_photo(file_data, folder=folder)
        if result:
            results.append(result)
    return results

