from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'status', 'category', 'description', 'location_description', 'image', 'handover_status', 'handover_details', 'receiver_name', 'receiver_contact']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'location_description': forms.TextInput(attrs={'placeholder': 'E.g., Library 2nd Floor, Cafeteria...'}),
        }
