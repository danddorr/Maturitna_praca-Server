from django.contrib import admin
from .models import *

class GateStateHistoryAdmin(admin.ModelAdmin):
    list_display = ('gate_state', 'timestamp')
    list_filter = ('gate_state', 'timestamp')
    search_fields = ('gate_state', 'timestamp')

class TriggerHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'trigger_agent', 'trigger_type', 'timestamp')
    list_filter = ('user', 'trigger_agent', 'trigger_type', 'timestamp')
    search_fields = ('user', 'trigger_agent', 'trigger_type', 'timestamp')

admin.site.register(GateStateHistory, GateStateHistoryAdmin)
admin.site.register(TriggerHistory, TriggerHistoryAdmin)
