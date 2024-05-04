# serializers.py

from rest_framework import serializers
from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'mobile', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


# serializers.py


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = User.objects.filter(email=email).first()
            if user and user.check_password(password):
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                return user
            else:
                raise serializers.ValidationError('Incorrect emaiil or password.')
        else:
            raise serializers.ValidationError('Must include "email" and "password".')
