from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_name', 'description', 'material']
    
class CustomUserCreationForm(UserCreationForm):  # Custom user creation form
    class Meta(UserCreationForm.Meta):
        model = UserCreationForm.Meta.model
        fields = UserCreationForm.Meta.fields
