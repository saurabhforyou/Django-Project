from django import forms

#models
from .models import Document

#forms

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('name', 'document')

class SearchForm(forms.Form):
    search = forms.CharField(max_length=255, required=False)
