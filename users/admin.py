from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'goal', 'is_staff']
    list_filter = ['goal', 'is_staff', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'avatar', 'bio', 'date_of_birth', 'gender')}),
        ('Body Stats', {'fields': ('height_cm', 'weight_kg')}),
        ('Goals', {'fields': ('goal', 'target_weight_kg', 'goal_deadline', 'activity_level')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'username', 'password1', 'password2')}),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
