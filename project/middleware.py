# middleware.py
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from jwt import decode as jwt_decode
from django.conf import settings
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extract the token from the query string
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", None)
        special_token = query_string.get("special_token", None)

        if token:
            try:
                # Decode the token and authenticate the user
                decoded_data = jwt_decode(token[0], settings.SECRET_KEY, algorithms=["HS256"])
                scope["user"] = await get_user(decoded_data["user_id"])
            except Exception as e:
                # If the token is invalid, set the user as anonymous
                scope["user"] = AnonymousUser()
        elif special_token == settings.SPECIAL_TOKEN:
            scope["user"] = User.objects.get(username="gate_controller")
        else:
            scope["user"] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
