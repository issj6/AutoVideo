from rest_framework import exceptions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.utils.translation import gettext_lazy as _


class MyJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            # return None
            raise AuthenticationFailed({"code": 401, "msg": "认证失败，请重新登录"})

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            # return None
            raise AuthenticationFailed({"code": 401, "msg": "认证失败，请重新登录"})

        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken as e:
            raise AuthenticationFailed(
                {"code": 401, "msg": e.detail.get('messages')[0].get('message', "token认证失败")})

        return self.get_user(validated_token), validated_token
