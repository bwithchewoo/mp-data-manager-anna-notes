from django import forms
from .models import ExternalPortal

class RemotePortalMigrationForm(forms.Form):
    portal = forms.ModelChoiceField(label='External Portal', queryset=ExternalPortal.objects.all())