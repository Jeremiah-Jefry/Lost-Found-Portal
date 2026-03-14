from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'role', 'is_active', 'created_at')
    list_filter   = ('role', 'is_active')

    # first_name/last_name are removed from the model — define fieldsets from scratch
    fieldsets = (
        (None,             {'fields': ('username', 'password')}),
        ('Contact',        {'fields': ('email',)}),
        ('Portal Role',    {'fields': ('role',)}),
        ('Permissions',    {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates',{'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
