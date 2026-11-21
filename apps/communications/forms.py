from django import forms
from django.utils.translation import gettext_lazy as _
from academics.models import Curso, Turma
from accounts.models import UserRole
from .models import Comunicado, EscopoComunicado


class ComunicadoForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = ['titulo', 'conteudo', 'escopo', 'papel_destino', 'curso', 'turma', 'publicar_em', 'expirar_em', 'ativo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do comunicado'}),
            'conteudo': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Escreva aqui o conteúdo do comunicado'}),
            'escopo': forms.Select(attrs={'class': 'form-select', 'id': 'id_escopo'}),
            'papel_destino': forms.Select(attrs={'class': 'form-select'}),
            'curso': forms.Select(attrs={'class': 'form-select'}),
            'turma': forms.Select(attrs={'class': 'form-select'}),
            'publicar_em': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expirar_em': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Ajusta formatos para o input datetime-local
        if self.instance and self.instance.pk:
            if self.instance.publicar_em:
                self.initial['publicar_em'] = self.instance.publicar_em.strftime('%Y-%m-%dT%H:%M')
            if self.instance.expirar_em:
                self.initial['expirar_em'] = self.instance.expirar_em.strftime('%Y-%m-%dT%H:%M')

        # Se for Secretaria, limita as opções de escopo para GERAL e PAPEL
        if user and user.role == 'SECRETARIA' and not user.is_superuser:
            self.fields['escopo'].choices = [
                (EscopoComunicado.GERAL, _('Geral (Todos)')),
                (EscopoComunicado.PAPEL, _('Por Perfil')),
            ]
            self.fields['curso'].widget = forms.HiddenInput()
            self.fields['turma'].widget = forms.HiddenInput()
            self.fields['curso'].required = False
            self.fields['turma'].required = False

        self.fields['curso'].queryset = Curso.objects.filter(ativo=True)
        self.fields['turma'].queryset = Turma.objects.filter(ativo=True).select_related('disciplina')
        self.fields['papel_destino'].required = False
        self.fields['curso'].required = False
        self.fields['turma'].required = False
        self.fields['publicar_em'].required = False
        self.fields['expirar_em'].required = False
