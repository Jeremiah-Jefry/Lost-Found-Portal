from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'status', 'description', 'location_description', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'location_description': forms.TextInput(attrs={'placeholder': 'E.g., Library 2nd Floor, Cafeteria...'}),
        }
