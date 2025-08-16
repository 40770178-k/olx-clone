from django.urls import path
from .views import (
    HomeView,
    ItemCreateView,
    ItemListView,
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    ItemDetailView,
)

urlpatterns = [
    path('item_list', ItemListView.as_view(), name='item_list'),  # Home page shows items
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('item/<int:pk>/', ItemDetailView.as_view(), name='item_detail'),
    path('post_item/', ItemCreateView.as_view(), name='post_item'),
    path('', HomeView.as_view(), name='home'),
]
