"""
Django admin configuration for core app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as translation

from core.models import User


class UserAdmin(BaseUserAdmin):
    """
    Django admin configuration for user model
    """
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (translation('Login Bilgisi'), {'fields': ('email', 'password', 'name')}),
        (translation('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (translation('Important dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ('last_login',)
    add_fieldsets = (
        (None, {
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser'
            ),
            'classes': ('wide',),
        }),
    )


admin.site.register(User, UserAdmin)
