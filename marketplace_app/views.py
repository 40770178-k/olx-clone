from django.views.generic import ListView, FormView, DetailView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from .forms import ItemForm, UserRegistrationForm, ProfileForm, ItemImageForm
from .models import Item, Profile, Favorite, Conversation, Message, ItemImage
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from django.db.models import Q

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
        ctx["messages"] = conv.messages.all()
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
    
