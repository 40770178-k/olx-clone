from django.urls import path
from .views import (
    EditProfileView,
    HomeView,
    ItemCreateView,
    ItemListView,
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    ItemDetailView,
    UserprofileView,
    ItemDeleteView,
    ItemUpdateView,
    FavoriteListView,
    AddFavoriteView,
    RemoveFavoriteView,
    InboxView,
    ConversationDetailView,
    StartConversationView,
    AddItemImageView,
    DeleteItemImageView,
)

urlpatterns = [
    # Home & auth
    path('', HomeView.as_view(), name='home'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),

    # Items
    path('item_list/', ItemListView.as_view(), name='item_list'),
    path('post_item/', ItemCreateView.as_view(), name='post_item'),
    path('item/<int:pk>/', ItemDetailView.as_view(), name='item_detail'),
    path('item/<int:pk>/edit/', ItemUpdateView.as_view(), name='item_edit'),
    path('item/<int:pk>/delete/', ItemDeleteView.as_view(), name='item_delete'),
    
    # Item Images
    path('item/<int:item_pk>/add-image/', AddItemImageView.as_view(), name='add_item_image'),
    path('image/<int:pk>/delete/', DeleteItemImageView.as_view(), name='delete_item_image'),

    # Profiles (specific routes BEFORE dynamic username)
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),
    path('profile/<str:username>/', UserprofileView.as_view(), name='user_profile'),

    # Favorites
    path("favorites/", FavoriteListView.as_view(), name="favorite_list"),
    path("favorites/add/<int:pk>/", AddFavoriteView.as_view(), name="add_favorite"),
    path("favorites/remove/<int:pk>/", RemoveFavoriteView.as_view(), name="remove_favorite"),

    # Conversations & Messages
    path("inbox/", InboxView.as_view(), name="inbox"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("item/<int:pk>/start-conversation/", StartConversationView.as_view(), name="start-conversation"),
]
