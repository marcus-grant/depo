# Notes During Development

## Django Rest Framework Changes

API client support implementation is likely easier through
the Django REST Framework (**DRF**).
It includes both token-based and session-based authentication.
Looking over documentation, it seems something like this could be used:

```python filename="core/views.py"
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload(request):
    """
    API endpoint for file uploads.
    Only authenticated users can access this endpoint.
    """
    # Process the file upload (for example, store the file and return its URL)
    return Response({'status': 'uploaded'})
```

Just include `rest_framework` modules and
create separate view functions for API endpoints.
Then use the `@api_view` decorator for
marking the view as an API endpoint for POST requests.
After that, use the @permission_classes decorator to
specify which user-permissions are authorized to access the endpoint.
In this case the `isAuthenticated` permission class is used to
ensure only authenticated users can access the endpoint.

To make these API endpoints accessible, include them in the `urls.py` file.

```python filename="core/urls.py"
# ...other imports...
from .views import api_upload

urlpatterns = [
    # ...other paths...
    path('api/upload/', api_upload, name='api_upload'),
]
```

It's probably good to explicitly separate out API-specific views.
This way, view-logic becomes much more modular and internally simple.
Prepending `api/` to a route is simple enough to do for any client.
It also makes it simple to version the API with a prefix like `v1/`.
