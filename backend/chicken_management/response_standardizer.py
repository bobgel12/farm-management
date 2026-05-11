"""
API Response Standardization Middleware & Utilities

Ensures all API responses follow a consistent envelope format:
{
    "success": true,
    "data": {...},
    "meta": {
        "timestamp": "2026-05-11T10:30:00Z",
        "freshness": {
            "source_timestamp": "...",
            "age_seconds": 60,
            "is_stale": false
        }
    },
    "error": null
}

This fixes iOS data retrieval issues caused by inconsistent response formats.
"""

import json
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status


class StandardizedResponse(Response):
    """
    Custom Response class that wraps all data in a standardized envelope format.

    Usage in views:
        return StandardizedResponse(
            data={"farm_id": 1, "name": "Farm 1"},
            status_code=200
        )
    """

    def __init__(self, data=None, status_code=200, error=None, meta=None, **kwargs):
        # Extract the raw data
        response_data = {
            "success": status_code < 400,
            "data": data,
            "meta": self._build_meta(meta),
            "error": error if status_code >= 400 else None
        }

        # Call parent with standardized data
        super().__init__(
            data=response_data,
            status=status_code,
            **kwargs
        )

    @staticmethod
    def _build_meta(meta_dict=None):
        """Build standardized metadata object."""
        meta = meta_dict or {}
        return {
            "timestamp": timezone.now().isoformat(),
            "freshness": {
                "source_timestamp": meta.get("source_timestamp"),
                "age_seconds": meta.get("age_seconds"),
                "is_stale": meta.get("is_stale", False),
                "refresh_state": meta.get("refresh_state", "fresh"),
                "can_refresh_now": meta.get("can_refresh_now", False),
            },
            "pagination": meta.get("pagination"),
        }


class StandardizeResponseMiddleware:
    """
    Middleware that wraps all non-standardized responses in the envelope format.

    This ensures backward compatibility - responses that are already standardized
    won't be double-wrapped.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only wrap API responses
        if not request.path.startswith('/api/'):
            return response

        # Skip if already standardized
        if self._is_standardized(response):
            return response

        # Skip static files and non-JSON responses
        if response.get('Content-Type', '').startswith('application/json'):
            response = self._wrap_response(response)

        return response

    @staticmethod
    def _is_standardized(response):
        """Check if response is already in standardized format."""
        try:
            if not hasattr(response, 'data') or not isinstance(response.data, dict):
                return False

            required_keys = {'success', 'data', 'meta', 'error'}
            return required_keys == set(response.data.keys())
        except:
            return False

    @staticmethod
    def _wrap_response(response):
        """Wrap response data in standardized envelope."""
        try:
            original_data = response.data
            is_success = response.status_code < 400

            wrapped_data = {
                "success": is_success,
                "data": original_data if is_success else None,
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "freshness": {
                        "source_timestamp": None,
                        "age_seconds": None,
                        "is_stale": False,
                        "refresh_state": "fresh",
                        "can_refresh_now": False,
                    },
                    "pagination": None,
                },
                "error": original_data if not is_success else None,
            }

            response.data = wrapped_data
        except Exception as e:
            # If wrapping fails, return original response
            pass

        return response


def paginated_response(queryset, serializer_class, page_size=20):
    """
    Helper function to create standardized paginated responses.

    Usage:
        return paginated_response(houses, HouseSerializer, page_size=20)
    """
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginator.page_size = page_size
    paginated_data = paginator.paginate_queryset(queryset, None)
    serializer = serializer_class(paginated_data, many=True)

    return StandardizedResponse(
        data=serializer.data,
        meta={
            "pagination": {
                "count": paginator.page.paginator.count,
                "page": paginator.page.number,
                "page_size": page_size,
                "has_next": paginator.page.has_next(),
                "has_previous": paginator.page.has_previous(),
            }
        }
    )


def envelope_response(data=None, status_code=200, error=None, meta=None):
    """
    Convenience function to create a standardized response.

    Usage:
        return envelope_response(
            data={"farm_id": 1},
            meta={"source_timestamp": "2026-05-11T10:00:00Z"}
        )
    """
    return StandardizedResponse(
        data=data,
        status_code=status_code,
        error=error,
        meta=meta
    )
