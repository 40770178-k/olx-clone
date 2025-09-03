from django.views.generic import ListView, FormView, DetailView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from .forms import ItemForm, UserRegistrationForm
from .models import Item
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

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
        return super().form_valid(form)
    
class ItemDetailView(DetailView):
        model = Item
        template_name = 'item_detail.html'
        context_object_name = 'item'

class ItemListView(ListView):
    model = Item
    template_name = 'item_list.html'
    ordering = ['-posted_on']

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
    
class ItemUpdateView(UserPassesTestMixin, UpdateView):
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