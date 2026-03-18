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
    MessageListView,
    SendMessageView,
    SendMessageApiView,
    EscrowListView,
    EscrowDetailView,
    InitiateEscrowFromItemView,
    InitiateEscrowFromConversationView,
    EscrowCheckoutView,
    EscrowSuccessView,
    ConfirmReceiptView,
    MarkShippedView,
    EscrowDisputeView,
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
    path("conversations/<int:conversation_pk>/send/", SendMessageApiView.as_view(), name="send_message_api"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("item/<int:pk>/start-conversation/", StartConversationView.as_view(), name="start-conversation"),
    path('messages/', MessageListView.as_view(), name='message_list'),
    path('send_message/<int:conversation_id>/', SendMessageView.as_view(), name='send_message'),

    # Escrow payments
    path('escrow/', EscrowListView.as_view(), name='escrow-list'),
    path('escrow/<int:pk>/', EscrowDetailView.as_view(), name='escrow-detail'),
    path('item/<int:item_pk>/escrow/', InitiateEscrowFromItemView.as_view(), name='escrow-initiate-item'),
    path('conversations/<int:conversation_pk>/escrow/', InitiateEscrowFromConversationView.as_view(), name='escrow-initiate-conversation'),
    path('escrow/<int:pk>/checkout/', EscrowCheckoutView.as_view(), name='escrow-checkout'),
    path('escrow/<int:pk>/success/', EscrowSuccessView.as_view(), name='escrow-success'),
    path('escrow/<int:pk>/confirm-receipt/', ConfirmReceiptView.as_view(), name='escrow-confirm-receipt'),
    path('escrow/<int:pk>/mark-shipped/', MarkShippedView.as_view(), name='escrow-mark-shipped'),
    path('escrow/<int:pk>/dispute/', EscrowDisputeView.as_view(), name='escrow-dispute'),
]
