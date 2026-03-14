from django.contrib import admin
from .models import Item, ItemLog, Match


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display  = ('title', 'status', 'category', 'resolution_status', 'reporter', 'date_reported')
    list_filter   = ('status', 'category', 'resolution_status', 'handover_status')
    search_fields = ('title', 'description', 'location')
    raw_id_fields = ('reporter',)


@admin.register(ItemLog)
class ItemLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'item', 'actor', 'actor_role', 'created_at')
    list_filter  = ('action', 'actor_role')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('found_item', 'lost_item', 'score', 'is_reviewed', 'created_at')
    list_filter  = ('is_reviewed',)
