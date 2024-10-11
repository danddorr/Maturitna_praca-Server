from django.contrib import admin
from .models import *

class GateStateHistoryAdmin(admin.ModelAdmin):
    list_display = ('gate_state', 'created_at')
    list_filter = ('gate_state', 'created_at')
    search_fields = ('gate_state', 'created_at')

class TriggerHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'trigger_agent', 'trigger_type', 'created_at')
    list_filter = ('user', 'trigger_agent', 'trigger_type', 'created_at')
    search_fields = ('user', 'trigger_agent', 'trigger_type', 'created_at')

admin.site.register(GateStateHistory, GateStateHistoryAdmin)
admin.site.register(TriggerHistory, TriggerHistoryAdmin)
