from django.contrib import admin
from .models import Cat, Collection

@admin.register(Cat)
class CatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'birth_year', 'owner', 'image')
    list_filter = ('color', 'owner')
    search_fields = ('name', 'owner__username')
    raw_id_fields = ('owner',)

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'owner', 'views_count', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'owner__username', 'description')
    filter_horizontal = ('cats', 'likes')
    raw_id_fields = ('owner',)