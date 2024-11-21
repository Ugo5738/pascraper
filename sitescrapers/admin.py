from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from sitescrapers.models import Property, ScrapingJob


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "source",
        "address",
        "price",
        "bedrooms",
        "bathrooms",
        "house_type",
        "agent",
        "created_at",
        "updated_at",
    )
    list_filter = ("source", "house_type", "agent", "created_at", "updated_at")
    search_fields = ("address", "description", "agent")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "source",
                    "url",
                    "address",
                    "price",
                    "bedrooms",
                    "bathrooms",
                    "size",
                    "house_type",
                    "agent",
                )
            },
        ),
        ("Details", {"fields": ("description", "images", "floorplans")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def view_on_site(self, obj):
        return obj.url


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
    list_display = ("url", "status", "created_at", "updated_at", "property_link")
    list_filter = ("status", "created_at", "updated_at")
    search_fields = (
        "url",
    )  # Removed property__address since there's no direct relationship
    readonly_fields = ("created_at", "updated_at")

    def property_link(self, obj):
        if obj.scraped_property_id:  # Using scraped_property_id instead of property
            try:
                property_obj = Property.objects.get(id=obj.scraped_property_id)
                url = reverse(
                    "admin:sitescrapers_property_change",  # Updated to use correct app name
                    args=[obj.scraped_property_id],
                )
                return format_html('<a href="{}">{}</a>', url, property_obj.address)
            except Property.DoesNotExist:
                return "-"
        return "-"

    property_link.short_description = "Associated Property"

    def get_queryset(self, request):
        return super().get_queryset(
            request
        )  # Removed select_related since there's no direct relationship


# Optional: Create a custom admin site
class RealEstateAdminSite(admin.AdminSite):
    site_header = "Real Estate Admin"
    site_title = "Real Estate Admin Portal"
    index_title = "Welcome to Real Estate Admin Portal"


real_estate_admin_site = RealEstateAdminSite(name="real_estate_admin")
real_estate_admin_site.register(Property, PropertyAdmin)
real_estate_admin_site.register(ScrapingJob, ScrapingJobAdmin)
