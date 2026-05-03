from django.contrib import admin
from .models import (
    Item,
    Conversation,
    Message,
    ItemImage,
    Escrow,
    Complaint,
    DeliveryConfirmationImage,
    SellerRating,
)

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


@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'buyer', 'seller', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['item__title', 'buyer__username', 'seller__username']
    ordering = ['-created_at']
    actions = ['approve_escrow', 'reject_escrow','funded_escrow', 'disputed_escrow', 'cancelled_escrow']

    def approve_escrow(self, request, queryset):
        queryset.update(status='approved')

    def reject_escrow(self, request, queryset):
        queryset.update(status='rejected')

    def funded_escrow(self, request, queryset):
        queryset.update(status='funded')

    def disputed_escrow(self, request, queryset):
        queryset.update(status='disputed')

    def cancelled_escrow(self, request, queryset):
        queryset.update(status='cancelled')

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['item', 'buyer', 'created_at', 'is_resolved']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['item__title', 'buyer__username']
    ordering = ['-created_at']

    def approve_complaint(self, request, queryset):
        for complaint in queryset:
            complaint.is_resolved = True
            complaint.save()
        self.message_user(request, 'Selected complaints have been approved.')
    approve_complaint.short_description = 'Approve selected complaints'

    actions = [approve_complaint]


@admin.register(DeliveryConfirmationImage)
class DeliveryConfirmationImageAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'buyer', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['escrow__id', 'buyer__username', 'escrow__item__title']
    ordering = ['-uploaded_at']


@admin.register(SellerRating)
class SellerRatingAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'seller', 'buyer', 'stars', 'created_at']
    list_filter = ['stars', 'created_at']
    search_fields = ['seller__username', 'buyer__username', 'item__title']
    ordering = ['-created_at']
