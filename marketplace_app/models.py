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

    # Main image
    image = models.ImageField(upload_to='images/', blank=True, null=True)

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_items")
    posted_on = models.DateTimeField(auto_now_add=True)

    # Add is_shipped field to track shipment status
    is_shipped = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# Extra gallery images
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

    def __str__(self):
        return f'Message from {self.sender.username} in conversation {self.conversation.id}'


class Escrow(models.Model):
    """Escrow transaction - funds held until buyer confirms receipt."""
    STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('funded', 'Funded (Held)'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )

    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="escrows")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="escrows", null=True, blank=True)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="escrows_as_buyer")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="escrows_as_seller")

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    funded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Escrow #{self.id}: {self.item.title} - {self.get_status_display()}'


class Complaint(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='complaints')
    escrow = models.ForeignKey("Escrow", on_delete=models.CASCADE, related_name='complaints', null=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    details = models.TextField(blank=True)
    proof_video = models.FileField(upload_to='complaint_proofs/', blank=True, null=True)
    proof_image = models.ImageField(upload_to='complaint_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f'Complaint for {self.item.title} by {self.buyer.username}'


class DeliveryConfirmationImage(models.Model):
    escrow = models.ForeignKey("Escrow", on_delete=models.CASCADE, related_name="confirmation_images")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="delivery_confirmation_images")
    image = models.ImageField(upload_to="delivery_confirmations/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Delivery image for escrow #{self.escrow_id}"


class SellerRating(models.Model):
    escrow = models.OneToOneField("Escrow", on_delete=models.CASCADE, related_name="seller_rating")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="seller_ratings")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_ratings")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_ratings")
    stars = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(stars__gte=1) & models.Q(stars__lte=5),
                name="seller_rating_stars_between_1_and_5",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.stars} stars for {self.seller.username} by {self.buyer.username}"
