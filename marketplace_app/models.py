from django.db import models
from django.contrib.auth.models import User 

# Create your models here.
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
    image = models.ImageField(upload_to='images/')
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    posted_on = models.DateTimeField(auto_now_add=True)
    user_profile = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_items', null=True)

    def __str__(self):
        return self.title
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)  # NEW



class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')  # prevent duplicate favorites

    def __str__(self):
        return f"{self.user.username} saved {self.item.title}"
