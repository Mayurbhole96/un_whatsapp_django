import json

from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .forms import CreateInstanceForm, SendMessageForm
from .models import WhatsAppInstance, MessageLog
from .services import (
    create_instance,
    get_qr,
    get_status,
    send_message,
    logout_instance,
    WhatsAppServiceError,
)


class InstanceListView(View):
    """Homepage: list every WhatsApp instance, create new ones."""
    template_name = 'whatsapp_app/instance_list.html'

    def get(self, request):
        instances = WhatsAppInstance.objects.all().order_by('-created_at')
        form = CreateInstanceForm()
        return render(request, self.template_name, {'instances': instances, 'form': form})

    def post(self, request):
        form = CreateInstanceForm(request.POST)
        if form.is_valid():
            instance = WhatsAppInstance.objects.create(name=form.cleaned_data['name'])
            try:
                create_instance(instance.instance_id, instance.token, instance.name)
                django_messages.success(
                    request, f'Instance "{instance.name}" created. Scan its QR code to link it.'
                )
                return redirect('whatsapp_app:qr', instance_id=instance.instance_id)
            except WhatsAppServiceError as exc:
                instance.delete()
                django_messages.error(request, f'Could not create instance: {exc}')
        instances = WhatsAppInstance.objects.all().order_by('-created_at')
        return render(request, self.template_name, {'instances': instances, 'form': form})


class InstanceDeleteView(View):
    def post(self, request, instance_id):
        instance = get_object_or_404(WhatsAppInstance, instance_id=instance_id)
        try:
            logout_instance(instance.instance_id, instance.token)
        except WhatsAppServiceError:
            pass  # instance may already be gone from the Node side; still remove locally
        instance.delete()
        django_messages.success(request, 'Instance removed.')
        return redirect('whatsapp_app:instance_list')


class QRView(View):
    """Shows the QR code for ONE instance so it can be linked (scanned in)."""
    template_name = 'whatsapp_app/qr.html'

    def get(self, request, instance_id):
        instance = get_object_or_404(WhatsAppInstance, instance_id=instance_id)
        context = {'instance': instance}
        try:
            qr_data = get_qr(instance.instance_id, instance.token)
            status_data = get_status(instance.instance_id, instance.token)
            context['qr_status'] = qr_data.get('status')
            context['qr_image'] = qr_data.get('qr')
            context['is_ready'] = status_data.get('ready')
            context['info'] = status_data.get('info')

            info = status_data.get('info') or {}
            instance.is_connected = bool(status_data.get('ready'))
            instance.push_name = info.get('pushname') or instance.push_name
            instance.linked_number = info.get('wid') or instance.linked_number
            instance.save(update_fields=['is_connected', 'push_name', 'linked_number', 'last_checked'])
        except WhatsAppServiceError as exc:
            context['service_error'] = str(exc)
        return render(request, self.template_name, context)


class SendMessageView(View):
    """Form + handler for sending a WhatsApp message through ONE instance."""
    template_name = 'whatsapp_app/send_message.html'

    def get(self, request, instance_id):
        instance = get_object_or_404(WhatsAppInstance, instance_id=instance_id)
        form = SendMessageForm()
        return render(request, self.template_name, {'form': form, 'instance': instance})

    def post(self, request, instance_id):
        instance = get_object_or_404(WhatsAppInstance, instance_id=instance_id)
        form = SendMessageForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data['number']
            message = form.cleaned_data['message']
            try:
                print(instance.instance_id,":instance_id, ", instance.token,":token, ", number,":number, ", message)
                result = send_message(instance.instance_id, instance.token, number, message)
                MessageLog.objects.create(
                    instance=instance,
                    recipient_number=number,
                    message_body=message,
                    status='sent',
                    whatsapp_message_id=result.get('messageId', ''),
                )
                django_messages.success(request, 'Message sent successfully!')
                return redirect('whatsapp_app:message_list')
            except WhatsAppServiceError as exc:
                MessageLog.objects.create(
                    instance=instance,
                    recipient_number=number,
                    message_body=message,
                    status='failed',
                    error_detail=str(exc),
                )
                django_messages.error(request, f'Failed to send message: {exc}')
        return render(request, self.template_name, {'form': form, 'instance': instance})


class MessageListView(View):
    template_name = 'whatsapp_app/message_list.html'

    def get(self, request):
        logs = MessageLog.objects.select_related('instance').all()[:100]
        return render(request, self.template_name, {'logs': logs})


@method_decorator(csrf_exempt, name='dispatch')
class SendMessageAPIView(View):
    """
    Token-authenticated API endpoint for external systems/scripts —
    no Django login required, just the instance's token.

    POST /api/instances/<instance_id>/send/
    Header: Authorization: Token <instance token>
    Body (JSON): {"number": "919876543210", "message": "Hello"}

    Example:
        curl -X POST http://localhost:8000/api/instances/inst_abc123/send/ \
             -H "Authorization: Token <TOKEN>" \
             -H "Content-Type: application/json" \
             -d '{"number": "919876543210", "message": "Hello from the API"}'
    """

    def post(self, request, instance_id):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Token '):
            return JsonResponse(
                {'success': False, 'error': 'Missing or malformed Authorization header (expected "Token <token>")'},
                status=401,
            )
        token = auth.split('Token ', 1)[1].strip()

        instance = WhatsAppInstance.objects.filter(instance_id=instance_id, token=token).first()
        if not instance:
            return JsonResponse({'success': False, 'error': 'Invalid instance id or token'}, status=401)

        try:
            payload = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON body'}, status=400)

        number = payload.get('number')
        message = payload.get('message')
        if not number or not message:
            return JsonResponse(
                {'success': False, 'error': '"number" and "message" are required'}, status=400
            )

        try:
            result = send_message(instance.instance_id, instance.token, number, message)
            MessageLog.objects.create(
                instance=instance,
                recipient_number=number,
                message_body=message,
                status='sent',
                whatsapp_message_id=result.get('messageId', ''),
            )
            return JsonResponse({'success': True, 'messageId': result.get('messageId')})
        except WhatsAppServiceError as exc:
            MessageLog.objects.create(
                instance=instance,
                recipient_number=number,
                message_body=message,
                status='failed',
                error_detail=str(exc),
            )
            return JsonResponse({'success': False, 'error': str(exc)}, status=502)
