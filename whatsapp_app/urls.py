from django.urls import path
from . import views

app_name = 'whatsapp_app'

urlpatterns = [
    path('', views.InstanceListView.as_view(), name='instance_list'),
    path('instances/<str:instance_id>/qr/', views.QRView.as_view(), name='qr'),
    path('instances/<str:instance_id>/send/', views.SendMessageView.as_view(), name='send_message'),
    path('instances/<str:instance_id>/delete/', views.InstanceDeleteView.as_view(), name='instance_delete'),
    path('messages/', views.MessageListView.as_view(), name='message_list'),

    # Token-authenticated API for external callers (no browser session needed).
    path('api/instances/<str:instance_id>/send/', views.SendMessageAPIView.as_view(), name='api_send_message'),
]
