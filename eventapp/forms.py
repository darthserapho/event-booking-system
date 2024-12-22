from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

User = get_user_model()

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

from django import forms
from .models import Event, EventCategory, Ticket

class EventForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=EventCategory.objects.all(), empty_label="Select a Category")

    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'category', 'image']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['tickets_available','price_early_bird','price_general','price_vip']
        
TicketFormSet = inlineformset_factory(
    Event,
    Ticket,
    form=TicketForm,
    extra=1, 
    can_delete=False
)