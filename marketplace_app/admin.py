from django.contrib import admin
from .models import Item

# Register your models here.
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'location', 'price', 'posted_by', 'posted_on']
    list_filter = ['category', 'posted_on', 'location']
    search_fields = ['title', 'description', 'location']
    ordering = ['-posted_on']
    readonly_fields = ['posted_on']
