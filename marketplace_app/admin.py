

from django.contrib import admin
from .models import Item, Conversation, Message, ItemImage

# Register your models here.
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'location', 'price', 'posted_by', 'posted_on']
    list_filter = ['category', 'posted_on', 'location']
    search_fields = ['title', 'description', 'location']
    ordering = ['-posted_on']
    readonly_fields = ['posted_on']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'buyer', 'seller', 'last_message_at', 'created_at']
    list_filter = ['created_at', 'last_message_at']
    search_fields = ['item__title', 'buyer__username', 'seller__username']
    ordering = ['-last_message_at', '-created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'short_content', 'created_at', 'read']
    list_filter = ['created_at', 'read']
    search_fields = ['conversation__id', 'sender__username', 'content']
    ordering = ['-created_at']

    def short_content(self, obj):
        return (obj.content[:60] + '…') if len(obj.content) > 60 else obj.content
    short_content.short_description = 'content'


@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'image']
    list_filter = ['item__category', 'item__posted_on']
    search_fields = ['item__title']
    ordering = ['-id']
