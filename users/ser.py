from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users import models
from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = models.User
        fields = ['username', 'password', 'email', 'phone', 'balance']

    def validate(self, attrs):
        if attrs.get("password") and len(attrs.get("password")) < 5:
            raise ValidationError("密码长度太短")

        return attrs

    # def create(self, validated_data):
    #     print(123)
    #     if not User.objects.filter(username=validated_data.get('username')).first():
    #         raise ValidationError("账号重复")
    #
    #     user = models.User.objects.create_user(**validated_data)
    #
    #     return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        user = User.objects.filter(username=attrs['username']).first()
        if not user or not user.check_password(attrs['password']):
            return {"code": 400, "msg": "账号密码错误"}

        if user.is_active != 1:
            return {"code": 400, "msg": "账号不存在"}

        data = super().validate(attrs)
        user_info = {
            "user_id": user.id,
            "username": user.username,
            "balance": user.balance
        }
        # 添加自定义响应数据
        res = {"code": 200, "msg": "登录成功", "data": {"token": data, "user_info": user_info}}
        return res


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = models.User
        fields = ['username', 'password', 'email', 'phone', 'balance']
