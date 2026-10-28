from django.contrib import admin
from .models import WhatsAppInstance, MessageLog


@admin.register(WhatsAppInstance)
class WhatsAppInstanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'instance_id', 'is_connected', 'linked_number', 'push_name', 'created_at')
    readonly_fields = ('instance_id', 'token', 'created_at', 'last_checked')
    list_filter = ('is_connected',)
    search_fields = ('name', 'instance_id', 'linked_number')


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_number', 'instance', 'status', 'created_at')
    list_filter = ('status', 'instance')
    search_fields = ('recipient_number', 'message_body')
