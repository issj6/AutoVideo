from django.shortcuts import render
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ViewSet
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView

from common import res
from common.res import Res
from users import ser
from users.models import User
from users.ser import MyTokenObtainPairSerializer


# Create your views here.


class RegisterView(ViewSet):
    """
    注册视图
    """
    authentication_classes = []
    permission_classes = []

    def register(self, request):
        # 验证账号是否被注册
        username = request.data.get('username')
        if User.objects.filter(username=username).first():
            return Res(400, "账号已存在")

        # 创建序列化器，验证并注册
        serializer = ser.RegisterSerializer(data=request.data)
        if serializer.is_valid():
            User.objects.create_user(**request.data)
            return Res(200, "注册成功", serializer.data)
        return Res(200, "账号密码验证失败", serializer.errors)


class LoginTokenObtainPairView(TokenObtainPairView):
    """
    登录视图
    """
    authentication_classes = []
    permission_classes = []

    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserView(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = ser.UserSerializer

    @action(detail=False, methods=['get'], url_path="balance")
    def get_balance(self, request):
        return Response({"code": 200, "data": request.user.balance})
