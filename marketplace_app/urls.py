from django.urls import path
from .views import (
    HomeView,
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    ItemDetailView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('item/<int:pk>/', ItemDetailView.as_view(), name='item_detail'),
]
# This file defines the URL patterns for the marketplace application.
# It includes paths for the home page, user registration, login, logout, and item detail