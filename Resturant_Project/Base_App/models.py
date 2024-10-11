from django.db import models

# Create your models here.
class ItemList(models.Model):
    Category_name = models.CharField(max_length=15)

    def __str__(self):
        return self.Category_name
    

class Items(models.Model):
    Item_name = models.CharField(max_length=40)
    description = models.TextField(blank=False)
    Price = models.IntegerField()
    Category = models.ForeignKey(ItemList, related_name='Name', on_delete=models.CASCADE)
    Image = models.ImageField(upload_to='items/')

    def __str__(self):
        return self.Item_name

class AboutUs(models.Model):
    Description = models.TextField(blank=False)

from django.db import models

class Feedback(models.Model):
    user_name = models.CharField(max_length=255)
    description = models.TextField()
    rating = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='feedback_images/', blank=True, null=True)  # Make image field optional

    def __str__(self):
        return f'{self.user_name} - {self.rating}'
