from django.views.generic import ListView, FormView, DetailView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages as django_messages
from .forms import (
    ItemForm,
    UserRegistrationForm,
    ProfileForm,
    ItemImageForm,
    DeliveryConfirmationImageForm,
    ComplaintForm,
    SellerRatingForm,
    EscrowBankDetailsForm,
)
from .models import (
    Item,
    Profile,
    Favorite,
    Conversation,
    Message,
    ItemImage,
    Escrow,
    DeliveryConfirmationImage,
    Complaint,
    SellerRating,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from django.conf import settings
import base64
import hashlib
import json
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
        if self.request.user.is_authenticated and self.request.user == self.object.posted_by:
            context['seller_latest_escrow'] = Escrow.objects.filter(
                item=self.object,
                seller=self.request.user,
                status='funded'
            ).order_by('-created_at').first()
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['seller_latest_funded_escrow'] = Escrow.objects.filter(
            item=self.object,
            seller=self.request.user,
            status='funded'
        ).order_by('-created_at').first()
        return ctx


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
        ctx["conversation_escrow"] = Escrow.objects.filter(conversation=conv).order_by("-created_at").first()
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
        escrow = self.object
        user = self.request.user
        ctx['confirmation_form'] = DeliveryConfirmationImageForm()
        ctx['complaint_form'] = ComplaintForm()
        existing_rating = SellerRating.objects.filter(escrow=escrow, buyer=user).first()
        ctx['rating_form'] = SellerRatingForm(instance=existing_rating)
        ctx['existing_rating'] = existing_rating
        bank_meta = None
        if escrow.notes:
            try:
                notes_data = json.loads(escrow.notes)
                bank_meta = notes_data.get("bank_meta")
            except (TypeError, json.JSONDecodeError):
                bank_meta = None
        ctx['bank_meta'] = bank_meta
        ctx['has_confirmation_photo'] = escrow.confirmation_images.exists()
        return ctx


def _create_and_redirect_escrow(request, item, buyer, seller, conversation=None):
    """Shared logic for creating escrow and redirecting to prototype funding flow."""
    existing = Escrow.objects.filter(
        item=item, buyer=buyer, seller=seller, status='pending'
    ).first()
    if existing:
        return redirect('escrow-fund', pk=existing.pk)

    escrow = Escrow.objects.create(
        item=item,
        conversation=conversation,
        buyer=buyer,
        seller=seller,
        amount=item.price,
        status='pending',
    )

    django_messages.info(request, "Prototype mode: enter bank details to simulate funding.")
    return redirect('escrow-fund', pk=escrow.pk)


def _obfuscate_text(value):
    """Prototype-only obfuscation to avoid storing bank details in plain text."""
    value_bytes = value.encode("utf-8")
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    xored = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(value_bytes))
    return base64.urlsafe_b64encode(xored).decode("ascii")


class EscrowPrototypeFundView(LoginRequiredMixin, TemplateView):
    template_name = 'escrow_fund.html'

    def get(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Not authorized.")
            return redirect('escrow-list')
        if escrow.status != 'pending':
            return redirect('escrow-detail', pk=escrow.pk)
        return render(request, self.template_name, {'escrow': escrow, 'form': EscrowBankDetailsForm()})

    def post(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Not authorized.")
            return redirect('escrow-list')
        if escrow.status != 'pending':
            return redirect('escrow-detail', pk=escrow.pk)

        form = EscrowBankDetailsForm(request.POST)
        if not form.is_valid():
            django_messages.error(request, "Please provide valid bank details.")
            return render(request, self.template_name, {'escrow': escrow, 'form': form})

        details = form.cleaned_data
        encrypted_payload = {key: _obfuscate_text(str(val)) for key, val in details.items()}

        account_number = details.get('account_number', '')
        masked_account = f"{'*' * max(0, len(account_number) - 4)}{account_number[-4:]}" if account_number else '****'
        bank_meta = {
            'account_name': details.get('account_name'),
            'bank_name': details.get('bank_name'),
            'account_number_masked': masked_account,
            'branch': details.get('branch'),
            'bank_code': details.get('bank_code'),
            'swift_code': details.get('swift_code') or 'N/A',
        }
        escrow.notes = json.dumps({'bank_encrypted': encrypted_payload, 'bank_meta': bank_meta, 'mode': 'prototype'})
        escrow.status = 'funded'
        escrow.funded_at = timezone.now()
        escrow.save(update_fields=['notes', 'status', 'funded_at'])

        django_messages.success(request, "Prototype escrow funded. No real money was moved.")
        return redirect('escrow-detail', pk=escrow.pk)


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

        if not escrow.confirmation_images.exists():
            django_messages.error(
                request,
                "Upload at least one delivery confirmation photo before confirming receipt and releasing payment."
            )
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
            django_messages.error(request, "Ship action is available only after escrow is funded.")
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


class UploadDeliveryConfirmationView(LoginRequiredMixin, TemplateView):
    """Buyer uploads delivery confirmation images."""

    def post(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Only the buyer can upload confirmation images.")
            return redirect('escrow-list')

        form = DeliveryConfirmationImageForm(request.POST, request.FILES)
        if form.is_valid():
            delivery_image = form.save(commit=False)
            delivery_image.escrow = escrow
            delivery_image.buyer = request.user
            delivery_image.save()
            django_messages.success(request, "Confirmation image uploaded.")
        else:
            django_messages.error(request, "Please upload a valid image file.")
        return redirect('escrow-detail', pk=escrow.pk)


class SubmitEscrowComplaintView(LoginRequiredMixin, TemplateView):
    """Buyer submits a complaint with optional evidence."""

    def post(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Only the buyer can submit complaints.")
            return redirect('escrow-list')

        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.item = escrow.item
            complaint.escrow = escrow
            complaint.buyer = request.user
            complaint.save()
            django_messages.success(request, "Complaint submitted. Support will review your evidence.")
        else:
            django_messages.error(request, "Please provide valid complaint details.")
        return redirect('escrow-detail', pk=escrow.pk)


class RateSellerView(LoginRequiredMixin, TemplateView):
    """Buyer rates seller after successful completion."""

    def post(self, request, *args, **kwargs):
        escrow = get_object_or_404(Escrow, pk=kwargs['pk'])
        if escrow.buyer != request.user:
            django_messages.error(request, "Only the buyer can rate the seller.")
            return redirect('escrow-list')

        existing_rating = SellerRating.objects.filter(escrow=escrow, buyer=request.user).first()
        form = SellerRatingForm(request.POST, instance=existing_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.escrow = escrow
            rating.item = escrow.item
            rating.buyer = request.user
            rating.seller = escrow.seller
            rating.save()
            django_messages.success(request, "Seller rating saved.")
        else:
            django_messages.error(request, "Please choose a valid star rating.")
        return redirect('escrow-detail', pk=escrow.pk)
