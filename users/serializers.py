# serializers.py

from rest_framework import serializers
from users.models import User, Friends


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


class FriendSerializer(serializers.Serializer):
    user_1_id = serializers.IntegerField(required=True)
    username = serializers.CharField(required=False)
    mobile = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    def create(self, validated_data):
        user_1 = User.objects.get(id=validated_data['user_1_id'])
        user_2 = None
        if validated_data.get('mobile'):
            user_2 = User.objects.filter(mobile=validated_data['mobile']).first()
        elif validated_data.get('email'):
            user_2 = User.objects.filter(email=validated_data['email']).first()

        if not user_2:
            # Create a user with a dummy password
            signup_data = {
                "username": validated_data["username"],
                "mobile": validated_data["mobile"],
                "email": validated_data["email"],
                "password": "dummy1"
            }
            user_serializer = SignupSerializer(data=signup_data)
            user_serializer.is_valid(raise_exception=True)
            user_2 = user_serializer.save()

        # Check if the friend relation already exists
        if Friends.objects.filter(user_1=user_1, user_2=user_2).exists() or Friends.objects.filter(user_1=user_2,
                                                                                                   user_2=user_1).exists():
            raise serializers.ValidationError("Friend relation already exists.")

        # Update Friends table
        friend, created = Friends.objects.get_or_create(user_1=user_1, user_2=user_2)

        return friend
