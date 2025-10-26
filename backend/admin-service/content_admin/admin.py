from django.contrib import admin
from .models import Bloc, BlocItem, AdSlot


class BlocItemInline(admin.TabularInline):
    model = BlocItem
    extra = 1


@admin.register(Bloc)
class BlocAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'visible', 'order', 'start_at', 'end_at']
    list_filter = ['type', 'visible', 'source_type']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BlocItemInline]


@admin.register(AdSlot)
class AdSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'type', 'active', 'current_impressions', 'max_impressions']
    list_filter = ['position', 'type', 'active']
    prepopulated_fields = {'slug': ('name',)}
