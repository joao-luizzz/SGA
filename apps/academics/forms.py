from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Curso, Disciplina

class BaseSGAForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class CursoForm(BaseSGAForm):
    class Meta:
        model = Curso
        fields = ['nome', 'codigo', 'descricao', 'ativo']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Descrição opcional do curso...')}),
            'nome': forms.TextInput(attrs={'placeholder': _('Ex: Análise e Desenvolvimento de Sistemas')}),
            'codigo': forms.TextInput(attrs={'placeholder': _('Ex: ADS')}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise forms.ValidationError(_("O código do curso é obrigatório."))
        
        # Validação de código único
        qs = Curso.objects.filter(codigo=codigo)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise forms.ValidationError(_("Já existe um curso cadastrado com este código."))
            
        return codigo


class DisciplinaForm(BaseSGAForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'codigo', 'carga_horaria', 'curso', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': _('Ex: Programação Orientada a Objetos')}),
            'codigo': forms.TextInput(attrs={'placeholder': _('Ex: ADS-POO')}),
            'carga_horaria': forms.NumberInput(attrs={'placeholder': _('Ex: 80')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permite selecionar apenas cursos ativos ao criar/editar uma disciplina
        self.fields['curso'].queryset = Curso.objects.filter(ativo=True)
        # Se for edição e o curso da disciplina estiver inativo, inclui ele para não quebrar o form
        if self.instance and self.instance.pk and self.instance.curso:
            if not self.instance.curso.ativo:
                self.fields['curso'].queryset = Curso.objects.filter(pk=self.instance.curso.pk) | self.fields['curso'].queryset

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise forms.ValidationError(_("O código da disciplina é obrigatório."))
            
        # Validação de código único
        qs = Disciplina.objects.filter(codigo=codigo)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise forms.ValidationError(_("Já existe uma disciplina cadastrada com este código."))
            
        return codigo

    def clean_carga_horaria(self):
        carga_horaria = self.cleaned_data.get('carga_horaria')
        if carga_horaria is not None and carga_horaria <= 0:
            raise forms.ValidationError(_("A carga horária deve ser maior que zero."))
        return carga_horaria
