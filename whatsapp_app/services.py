"""
Thin client for the Node.js whatsapp-web.js bridge service.
Every per-instance call is authenticated with that instance's token via the
X-API-Token header, matching what the Node service enforces.
"""
import requests
from django.conf import settings


class WhatsAppServiceError(Exception):
    """Raised when the Node bridge service is unreachable or returns an error."""


def _base_url():
    return settings.NODE_SERVICE_URL.rstrip('/')


def _headers(token):
    return {"X-API-Token": token}


def create_instance(instance_id, token, name):
    try:
        resp = requests.post(
            f"{_base_url()}/instances",
            json={"instanceId": instance_id, "token": token, "name": name},
            timeout=10,
        )
        data = resp.json()
        if resp.status_code >= 400:
            raise WhatsAppServiceError(data.get('error', 'Could not create instance'))
        return data
    except requests.RequestException as exc:
        raise WhatsAppServiceError(f"Could not reach WhatsApp service: {exc}")


def get_qr(instance_id, token):
    try:
        resp = requests.get(
            f"{_base_url()}/instances/{instance_id}/qr", headers=_headers(token), timeout=10
        )
        if resp.status_code >= 400:
            raise WhatsAppServiceError(resp.json().get('error', 'Could not fetch QR code'))
        return resp.json()
    except requests.RequestException as exc:
        raise WhatsAppServiceError(f"Could not reach WhatsApp service: {exc}")


def get_status(instance_id, token):
    try:
        resp = requests.get(
            f"{_base_url()}/instances/{instance_id}/status", headers=_headers(token), timeout=10
        )
        if resp.status_code >= 400:
            raise WhatsAppServiceError(resp.json().get('error', 'Could not fetch status'))
        return resp.json()
    except requests.RequestException as exc:
        raise WhatsAppServiceError(f"Could not reach WhatsApp service: {exc}")


def send_message(instance_id, token, number, message):
    try:
        resp = requests.post(
            f"{_base_url()}/instances/{instance_id}/send-message",
            headers=_headers(token),
            json={"number": number, "message": message},
            timeout=20,
        )
        data = resp.json()
        if resp.status_code >= 400:
            raise WhatsAppServiceError(data.get('error', 'Unknown error from WhatsApp service'))
        return data
    except requests.RequestException as exc:
        raise WhatsAppServiceError(f"Could not reach WhatsApp service: {exc}")


def logout_instance(instance_id, token):
    try:
        resp = requests.post(
            f"{_base_url()}/instances/{instance_id}/logout", headers=_headers(token), timeout=10
        )
        data = resp.json()
        if resp.status_code >= 400:
            raise WhatsAppServiceError(data.get('error', 'Could not logout instance'))
        return data
    except requests.RequestException as exc:
        raise WhatsAppServiceError(f"Could not reach WhatsApp service: {exc}")
