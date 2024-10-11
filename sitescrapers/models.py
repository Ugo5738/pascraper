from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models


class Property(models.Model):
    PROPERTY_SOURCES = [
        ("rightmove", "Rightmove"),
        ("zoopla", "Zoopla"),
        ("onthemarket", "OnTheMarket"),
    ]

    source = models.CharField(max_length=20, choices=PROPERTY_SOURCES)
    url = models.URLField(unique=True)
    address = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.PositiveIntegerField(null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    house_type = models.CharField(max_length=100, null=True, blank=True)
    agent = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField()
    images = ArrayField(models.URLField(), blank=True)
    floorplans = ArrayField(models.URLField(), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be a positive number.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.source} - {self.address}"


class ScrapingJob(models.Model):
    JOB_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    url = models.URLField()
    source = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=JOB_STATUS_CHOICES, default="pending"
    )
    callback_url = models.URLField(null=True, blank=True)
    property_id = models.IntegerField(null=True, blank=True)
    task_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job for {self.url} - {self.status}"
