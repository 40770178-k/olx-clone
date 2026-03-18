from django.views.generic import ListView, FormView, DetailView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages as django_messages
from .forms import ItemForm, UserRegistrationForm, ProfileForm, ItemImageForm
from .models import Item, Profile, Favorite, Conversation, Message, ItemImage, Escrow
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from .escrow_services import (
    is_stripe_configured,
    create_escrow_checkout_session,
    capture_escrow_payment,
    cancel_escrow_payment,
    get_payment_intent_from_session,
)

class HomeView(TemplateView):
    template_name = 'home.html'

class UserRegisterView(FormView):
    template_name = 'register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
    
class UserLoginView(LoginView):
    template_name = 'login.html'

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('home')



class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'post_item.html'
    success_url = reverse_lazy('item_list')

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        response = super().form_valid(form)
        
        # Handle multiple image uploads
        extra_images = self.request.FILES.getlist('extra_images')
        for image in extra_images:
            ItemImage.objects.create(item=self.object, image=image)
        
        return response
    
class ItemDetailView(DetailView):
    model = Item
    template_name = 'item_detail.html'
    context_object_name = 'item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_favorited'] = Favorite.objects.filter(
                user=self.request.user, 
                item=self.object
            ).exists()
        else:
            context['is_favorited'] = False
        if self.request.user.is_authenticated and self.request.user != self.object.posted_by:
            convo = Conversation.objects.filter(item=self.object, buyer=self.request.user, seller=self.object.posted_by).first()
            if convo:
                context['conversation_id'] = convo.id
        
        # Add extra images to context
        context['extra_images'] = self.object.images.all()
        return context

class ItemListView(ListView):
    model = Item
    template_name = "item_list.html"
    context_object_name = "items"

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )

        # Location filter
        location = self.request.GET.get("location")
        if location and location.lower() != "all":
            queryset = queryset.filter(location__icontains=location)

        # Price filter
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Sorting
        sort = self.request.GET.get("sort")
        if sort == "newest":
            queryset = queryset.order_by("-posted_on")
        elif sort == "price_low":
            queryset = queryset.order_by("price")
        elif sort == "price_high":
            queryset = queryset.order_by("-price")

        return queryset

    

class UserprofileView(ListView):
    model = Item
    template_name = 'user_profile.html'
    context_object_name = 'items'
    paginate_by = 10  # optional, if you want pagination later

    def get_queryset(self):
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username)
        return Item.objects.filter(posted_by=user).order_by('-posted_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        context['profile_user'] = get_object_or_404(User, username=username)
        return context
    
class ItemUpdateView(LoginRequiredMixin,UserPassesTestMixin, UpdateView):
    model = Item
    fields = ['title', 'description', 'price', 'location', 'image']
    template_name = 'item_edit.html'

    def get_success_url(self):
        return reverse_lazy('item_detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        return self.get_object().posted_by == self.request.user


class ItemDeleteView(UserPassesTestMixin, DeleteView):
    model = Item
    template_name = 'item_delete.html'
    success_url = reverse_lazy('item_list')

    def test_func(self):
        return self.get_object().posted_by == self.request.user
    
class EditProfileView(UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'edit_profile.html'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_success_url(self):
        return reverse_lazy('user_profile', kwargs={'username': self.request.user.username})
    
class AddFavoriteView(LoginRequiredMixin, CreateView):
    model = Favorite
    fields = []  # no form, we just set user & item in code

    def post(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=kwargs["pk"])
        Favorite.objects.get_or_create(user=request.user, item=item)
        return redirect("item_detail", pk=item.pk)
    
class RemoveFavoriteView(LoginRequiredMixin, DeleteView):
    model = Favorite

    def get_object(self, queryset=None):
        item = get_object_or_404(Item, pk=self.kwargs["pk"])
        return Favorite.objects.get(user=self.request.user, item=item)

    def post(self, request, *args, **kwargs):
        fav = self.get_object()
        fav.delete()
        return redirect("item_detail", pk=self.kwargs["pk"])
    
class FavoriteListView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = "favorite_list.html"
    context_object_name = "favorites"

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("item")


class InboxView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "inbox.html"   # one folder before templates
    context_object_name = "conversations"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(buyer=user) | Q(seller=user)).select_related("item", "buyer", "seller").prefetch_related("messages")

class ConversationDetailView(LoginRequiredMixin, TemplateView):
    template_name = "conversation_detail.html"  # one folder before templates

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        conv_id = self.kwargs.get("pk")
        conv = get_object_or_404(Conversation, pk=conv_id)
        user = self.request.user
        # ensure the user is part of the conversation
        if not (conv.buyer == user or conv.seller == user):
            raise PermissionError("Not allowed")
        # mark unread messages from other side as read
        conv.messages.filter(read=False).exclude(sender=user).update(read=True)
        ctx["conversation"] = conv
        ctx["messages"] = conv.messages.order_by("created_at")
        return ctx


class StartConversationView(LoginRequiredMixin, TemplateView):
    template_name = "conversation_detail.html"

    def post(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=kwargs.get("pk"))
        seller = item.posted_by
        buyer = request.user
        if buyer == seller:
            return redirect("item_detail", pk=item.pk)
        conv, created = Conversation.objects.get_or_create(item=item, buyer=buyer, seller=seller)
        return redirect("conversation-detail", pk=conv.pk)


class AddItemImageView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ItemImage
    form_class = ItemImageForm
    template_name = 'add_image.html'

    def form_valid(self, form):
        item = get_object_or_404(Item, pk=self.kwargs['item_pk'])
        form.instance.item = item
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('item_detail', kwargs={'pk': self.kwargs['item_pk']})

    def test_func(self):
        item = get_object_or_404(Item, pk=self.kwargs['item_pk'])
        return item.posted_by == self.request.user


class DeleteItemImageView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ItemImage
    template_name = 'delete_image.html'

    def get_success_url(self):
        return reverse_lazy('item_detail', kwargs={'pk': self.object.item.pk})

    def test_func(self):
        return self.get_object().item.posted_by == self.request.user
    

class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'message_list.html'
    context_object_name = 'messages'

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(conversation__buyer=user) | Q(conversation__seller=user)).order_by('-created_at')

class SendMessageView(LoginRequiredMixin, CreateView):
    model = Message
    fields = ['content']
    template_name = 'send_message.html'

    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.conversation = get_object_or_404(Conversation, id=self.kwargs['conversation_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('conversation-detail', kwargs={'pk': self.object.conversation.id})


class SendMessageApiView(LoginRequiredMixin, TemplateView):
    """JSON API for sending messages - fallback when WebSocket is disconnected."""

    def post(self, request, *args, **kwargs):
        conv = get_object_or_404(Conversation, pk=kwargs['conversation_pk'])
        if conv.buyer != request.user and conv.seller != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=403)

        content = (request.POST.get('content') or '').strip()
        if not content:
            return JsonResponse({'error': 'Message is required'}, status=400)

        msg = Message.objects.create(conversation=conv, sender=request.user, content=content)
        conv.touch()

        return JsonResponse({
            'id': msg.id,
            'sender_id': request.user.id,
            'sender_username': str(request.user),
            'message': msg.content,
            'created_at': msg.created_at.isoformat(),
            'conversation_id': conv.id,
        })


# ============ Escrow Payment Views ============

class EscrowListView(LoginRequiredMixin, ListView):
    model = Escrow
    template_name = 'escrow_list.html'
    context_object_name = 'escrows'

    def get_queryset(self):
        user = self.request.user
        return Escrow.objects.filter(Q(buyer=user) | Q(seller=user)).select_related('item', 'buyer', 'seller').order_by('-created_at')


class EscrowDetailView(LoginRequiredMixin, DetailView):
    model = Escrow
    template_name = 'escrow_detail.html'
    context_object_name = 'escrow'

    def get_queryset(self):
        user = self.request.user
        return Escrow.objects.filter(Q(buyer=user) | Q(seller=user))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stripe_configured'] = is_stripe_configured()
        return ctx


def _create_and_redirect_escrow(request, item, buyer, seller, conversation=None):
    """Shared logic for creating escrow and redirecting to Stripe."""
    existing = Escrow.objects.filter(
        item=item, buyer=buyer, seller=seller, status='pending'
    ).first()
    if existing:
        return redirect('escrow-checkout', pk=existing.pk)

    escrow = Escrow.objects.create(
        item=item,
        conversation=conversation,
        buyer=buyer,
        seller=seller,
        amount=item.price,
        status='pending',
    )

    if not is_stripe_configured():
        django_messages.warning(
            request,
            "Stripe is not configured. Set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY. "
            "Escrow created in demo mode."
        )
        return redirect('escrow-detail', pk=escrow.pk)

    session, err = create_escrow_checkout_session(escrow, request)
    if err:
        django_messages.error(request, f"Payment error: {err}")
        return redirect('escrow-detail', pk=escrow.pk)

    escrow.stripe_checkout_session_id = session.id
    escrow.save()
    return redirect(session.url)


class InitiateEscrowFromItemView(LoginRequiredMixin, TemplateView):
    """Start escrow payment from item page."""

    def post(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=kwargs['item_pk'])
        if request.user == item.posted_by:
            django_messages.error(request, "You cannot buy your own item.")
            return redirect('item_detail', pk=item.pk)
        return _create_and_redirect_escrow(
            request, item, request.user, item.posted_by, conversation=None
        )


class InitiateEscrowFromConversationView(LoginRequiredMixin, TemplateView):
    """Start escrow payment from conversation page (buyer only)."""

    def post(self, request, *args, **kwargs):
        conv = get_object_or_404(Conversation, pk=kwargs['conversation_pk'])
        if conv.buyer != request.user:
            django_messages.error(request, "Only the buyer can initiate escrow payment.")
            return redirect('conversation-detail', pk=conv.pk)
        if conv.seller == request.user:
            django_messages.error(request, "You cannot buy your own item.")
            return redirect('conversation-detail', pk=conv.pk)
        return _create_and_redirect_escrow(
            request, conv.item, conv.buyer, conv.seller, conversation=conv
        )


class EscrowCheckoutView(LoginRequiredMixin, TemplateView):
    """Redirect existing pending escrow to Stripe Checkout."""

    def get(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Not authorized.")
            return redirect('escrow-list')
        if escrow.status != 'pending':
            return redirect('escrow-detail', pk=escrow.pk)

        if not is_stripe_configured():
            return redirect('escrow-detail', pk=escrow.pk)

        session, err = create_escrow_checkout_session(escrow, request)
        if err:
            django_messages.error(request, f"Payment error: {err}")
            return redirect('escrow-detail', pk=escrow.pk)

        escrow.stripe_checkout_session_id = session.id
        escrow.save()
        return redirect(session.url)


class EscrowSuccessView(LoginRequiredMixin, TemplateView):
    """Handle return from Stripe Checkout - update escrow with PaymentIntent."""

    def get(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            return redirect('escrow-list')

        session_id = request.GET.get('session_id')
        if session_id and escrow.status == 'pending':
            pi_id = get_payment_intent_from_session(session_id)
            if pi_id:
                escrow.stripe_payment_intent_id = pi_id
                escrow.status = 'funded'
                escrow.funded_at = timezone.now()
                escrow.save()
                django_messages.success(request, "Payment received! Funds are held in escrow until you confirm receipt.")

        return redirect('escrow-detail', pk=escrow.pk)


class ConfirmReceiptView(LoginRequiredMixin, TemplateView):
    """Buyer confirms they received the item - capture payment and release to seller."""

    def post(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Not authorized.")
            return redirect('escrow-list')
        if escrow.status not in ('funded', 'shipped'):
            django_messages.error(request, "Cannot confirm receipt in current state.")
            return redirect('escrow-detail', pk=escrow.pk)

        success, err = capture_escrow_payment(escrow)
        if success:
            escrow.status = 'completed'
            escrow.completed_at = timezone.now()
            escrow.save()
            django_messages.success(request, "Transaction complete! Funds have been released to the seller.")
        else:
            django_messages.error(request, f"Capture failed: {err}")

        return redirect('escrow-detail', pk=escrow.pk)


class MarkShippedView(LoginRequiredMixin, TemplateView):
    """Seller marks item as shipped."""

    def post(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.seller != request.user:
            django_messages.error(request, "Not authorized.")
            return redirect('escrow-list')
        if escrow.status != 'funded':
            django_messages.error(request, "Cannot mark shipped in current state.")
            return redirect('escrow-detail', pk=escrow.pk)

        escrow.status = 'shipped'
        escrow.save()
        django_messages.success(request, "Marked as shipped. Buyer can confirm receipt when they receive it.")
        return redirect('escrow-detail', pk=escrow.pk)


class EscrowDisputeView(LoginRequiredMixin, TemplateView):
    """Buyer opens a dispute - cancel payment (refund)."""

    def post(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Not authorized.")
            return redirect('escrow-list')
        if escrow.status not in ('funded', 'shipped'):
            django_messages.error(request, "Cannot dispute in current state.")
            return redirect('escrow-detail', pk=escrow.pk)

        success, err = cancel_escrow_payment(escrow)
        if success:
            escrow.status = 'refunded'
            escrow.save()
            django_messages.success(request, "Dispute opened. Payment has been cancelled and you will be refunded.")
        else:
            django_messages.error(request, f"Could not cancel payment: {err}")

        return redirect('escrow-detail', pk=escrow.pk)
