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

    def __str__(self):
        return self.title