from django.views.generic import TemplateView, FormView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from .forms import UserRegistrationForm
from .models import Item


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

class ItemDetailView(DetailView):
    model = Item
    template_name = 'item_detail.html'
    context_object_name = 'item'

