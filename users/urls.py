# urls.py

from django.urls import path
from .views import SignupAPIView, LoginAPIView, AddFriendAPIView

urlpatterns = [
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('add_friend/', AddFriendAPIView.as_view(), name='add_friend'),
]
