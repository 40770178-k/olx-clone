from django.views.generic import ListView, FormView, DetailView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from .forms import ItemForm, UserRegistrationForm
from .models import Item
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView

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
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class ItemDetailView(DetailView):
        model = Item
        template_name = 'item_detail.html'
        context_object_name = 'item'

class ItemListView(ListView):
    model = Item
    template_name = 'item_list.html'
    ordering = ['-posted_on']