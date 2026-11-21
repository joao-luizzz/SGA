from django import forms
from .models import MaterialAcademico


class MaterialForm(forms.ModelForm):
    class Meta:
        model = MaterialAcademico
        fields = ['titulo', 'descricao', 'arquivo', 'link']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Slides da Aula 01'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição ou orientações sobre o material'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://exemplo.com/recurso'}),
        }
        help_texts = {
            'arquivo': 'Arquivos permitidos: PDF, DOCX, PPTX, ZIP, imagens, etc. (Máx: 20MB). Envie um arquivo OU informe um link.',
            'link': 'Informe uma URL válida caso o material esteja hospedado externamente.',
        }
