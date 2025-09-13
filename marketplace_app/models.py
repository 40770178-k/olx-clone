from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


class Item(models.Model):
    CATEGORIES = (
        ('Electronics', 'Electronics'),
        ('Clothing', 'Clothing'),
        ('Furniture', 'Furniture'),
        ('Books', 'Books'),
        ('Sports', 'Sports'),
        ('Others', 'Others'),
    )
    category = models.CharField(max_length=50, choices=CATEGORIES, default='Others')
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100, default='Not specified')

    # ✅ Main image
    image = models.ImageField(upload_to='images/', blank=True, null=True)

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_items")
    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ✅ Extra gallery images
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="item_images/")

    def __str__(self):
        return f"Image for {self.item.title}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')

    def __str__(self):
        return f"{self.user.username} saved {self.item.title}"


class Conversation(models.Model):
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="conversations")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_buyer")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_seller")
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("item", "buyer", "seller")
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        return f"Conv(item={self.item_id}, buyer={self.buyer_id}, seller={self.seller_id})"

    def touch(self):
        self.last_message_at = timezone.now()
        self.save(update_fields=["last_message_at"])


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Msg(conv={self.conversation_id}, sender={self.sender_id}, at={self.created_at})"
