from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from .models import CustomUser

class GateStateHistoryAdmin(admin.ModelAdmin):
    list_display = ('gate_state', 'timestamp')
    list_filter = ('gate_state', 'timestamp')
    search_fields = ('gate_state', 'timestamp')

class TriggerHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'trigger_agent', 'trigger_type', 'timestamp')
    list_filter = ('user', 'trigger_agent', 'trigger_type', 'timestamp')
    search_fields = ('user', 'trigger_agent', 'trigger_type', 'timestamp')

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_admin', 'can_open_vehicle', 'can_open_pedestrian', 'can_close_gate')}),
    )
    list_display = ('username', 'is_admin', 'can_open_vehicle', 'can_open_pedestrian', 'can_close_gate')
    search_fields = ('username',)
    list_filter = ('is_admin', 'can_open_vehicle', 'can_open_pedestrian', 'can_close_gate')

admin.site.register(GateStateHistory, GateStateHistoryAdmin)
admin.site.register(TriggerHistory, TriggerHistoryAdmin)
admin.site.register(CustomUser, UserAdmin)
