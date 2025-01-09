# middleware.py
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from jwt import decode as jwt_decode
from django.conf import settings
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(user_id=None, special_token=None):
    try:
        if user_id:
            return User.objects.get(id=user_id)
        elif special_token:
            return User.objects.get(special_token=special_token)
    except User.DoesNotExist:
        return AnonymousUser()
    
@database_sync_to_async
def check_special_token(special_token):
    return User.objects.filter(special_token=special_token).exists()
        
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
                scope["user"] = await get_user(user_id = decoded_data["user_id"])
            except Exception as e:
                # If the token is invalid, set the user as anonymous
                scope["user"] = AnonymousUser()
        elif special_token and await check_special_token(special_token[0]):
            scope["user"] = await get_user(special_token = special_token[0])
        else:
            scope["user"] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
