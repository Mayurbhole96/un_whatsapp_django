import whatsapp_app.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='WhatsAppInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instance_id', models.CharField(default=whatsapp_app.models.generate_instance_id, editable=False, max_length=64, unique=True)),
                ('token', models.CharField(default=whatsapp_app.models.generate_token, editable=False, max_length=64, unique=True)),
                ('name', models.CharField(default='My WhatsApp', max_length=100)),
                ('is_connected', models.BooleanField(default=False)),
                ('linked_number', models.CharField(blank=True, max_length=50, null=True)),
                ('push_name', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_checked', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='MessageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient_number', models.CharField(max_length=50)),
                ('message_body', models.TextField()),
                ('status', models.CharField(choices=[('sent', 'Sent'), ('failed', 'Failed')], max_length=10)),
                ('error_detail', models.TextField(blank=True, null=True)),
                ('whatsapp_message_id', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='whatsapp_app.whatsappinstance')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
