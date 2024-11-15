from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Property(models.Model):
    PROPERTY_SOURCES = [
        ("rightmove", "Rightmove"),
        ("zoopla", "Zoopla"),
        ("onthemarket", "OnTheMarket"),
    ]

    LISTING_TYPES = [
        ("sale", "Sale"),
        ("letting", "Letting"),
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
    time_on_market = models.CharField(max_length=255, null=True, blank=True)
    features = models.TextField(blank=True, null=True)
    listing_type = models.CharField(
        max_length=10, choices=LISTING_TYPES, null=True, blank=True
    )
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

    class Meta:
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")


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
    user_phone_number = models.CharField(max_length=20)
    property_id = models.IntegerField(null=True, blank=True)  # ID from main app
    scraped_property_id = models.IntegerField(
        null=True, blank=True
    )  # ID from scraper app
    task_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job for {self.url} - {self.status}"

    class Meta:
        verbose_name = _("ScrapingJob")
        verbose_name_plural = _("ScrapingJobs")
