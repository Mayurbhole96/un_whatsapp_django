from django import forms


class CreateInstanceForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label='Instance Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Sales Line, Support Line, Personal',
            'class': 'form-control',
        }),
    )


class SendMessageForm(forms.Form):
    number = forms.CharField(
        max_length=20,
        label='WhatsApp Number',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 919876543210 (country code, no + or spaces)',
            'class': 'form-control',
        }),
    )
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Type your message...',
            'class': 'form-control',
        }),
    )
