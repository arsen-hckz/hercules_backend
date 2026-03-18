from django.contrib import admin
from .models import Post, PostMedia, Like, Comment


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'likes_count', 'comments_count']
    inlines = [PostMediaInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
