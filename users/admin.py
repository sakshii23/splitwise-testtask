from django.contrib import admin
from .models import User
from django.contrib.admin.decorators import register


# Register all models to the admin site

@register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ("username", "email", "mobile")
    list_display = ["id", "username", "email", "mobile"]
    readonly_fields = ["username", "email", "password", "mobile"]
