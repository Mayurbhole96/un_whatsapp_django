import secrets
import uuid

from django.db import models


def generate_instance_id():
    return f"inst_{uuid.uuid4().hex[:12]}"


def generate_token():
    return secrets.token_urlsafe(32)


class WhatsAppInstance(models.Model):
    """One linked WhatsApp session. Each instance has its own QR pairing
    and its own API token used to authenticate send requests (both from
    the Django UI and from external callers hitting the token API)."""
    instance_id = models.CharField(max_length=64, unique=True, default=generate_instance_id, editable=False)
    token = models.CharField(max_length=64, unique=True, default=generate_token, editable=False)
    name = models.CharField(max_length=100, default='My WhatsApp')
    is_connected = models.BooleanField(default=False)
    linked_number = models.CharField(max_length=50, blank=True, null=True)
    push_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({'connected' if self.is_connected else 'disconnected'})"

    def regenerate_token(self):
        self.token = generate_token()
        self.save(update_fields=['token'])


class MessageLog(models.Model):
    """Audit log of every message send attempt, tied to the instance used."""
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    instance = models.ForeignKey(
        WhatsAppInstance, on_delete=models.CASCADE, related_name='messages', null=True, blank=True
    )
    recipient_number = models.CharField(max_length=50)
    message_body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_detail = models.TextField(blank=True, null=True)
    whatsapp_message_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient_number} - {self.status}"
