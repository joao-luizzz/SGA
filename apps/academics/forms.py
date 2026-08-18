from django import forms
from django.utils.translation import gettext_lazy as _
import re
from accounts.models import CustomUser
from .models import Curso, Disciplina, Turma

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


class TurmaForm(BaseSGAForm):
    class Meta:
        model = Turma
        fields = ['disciplina', 'periodo_letivo', 'horarios', 'sala', 'vagas_maximas', 'professor', 'ativo']
        widgets = {
            'periodo_letivo': forms.TextInput(attrs={'placeholder': _('Ex: 2026/1')}),
            'horarios': forms.TextInput(attrs={'placeholder': _('Ex: SEG 19:00-20:40 / QUA 20:50-22:30')}),
            'sala': forms.TextInput(attrs={'placeholder': _('Ex: Sala 302, Bloco B')}),
            'vagas_maximas': forms.NumberInput(attrs={'placeholder': _('Ex: 40')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra apenas disciplinas ativas no momento de nova criação/edição
        self.fields['disciplina'].queryset = Disciplina.objects.filter(ativo=True)
        # Se for edição e a disciplina atual já estiver inativa, inclui ela para não quebrar o formulário
        if self.instance and self.instance.pk and self.instance.disciplina:
            if not self.instance.disciplina.ativo:
                self.fields['disciplina'].queryset = Disciplina.objects.filter(pk=self.instance.disciplina.pk) | self.fields['disciplina'].queryset
        
        # Filtra apenas professores ativos para alocação
        self.fields['professor'].queryset = CustomUser.objects.filter(role='PROFESSOR', is_active=True)
        # Se for edição e o professor alocado estiver inativo, mantém ele na lista para preservar histórico
        if self.instance and self.instance.pk and self.instance.professor:
            if not self.instance.professor.is_active:
                self.fields['professor'].queryset = CustomUser.objects.filter(pk=self.instance.professor.pk) | self.fields['professor'].queryset

    def clean_vagas_maximas(self):
        vagas_maximas = self.cleaned_data.get('vagas_maximas')
        if vagas_maximas is not None and vagas_maximas <= 0:
            raise forms.ValidationError(_("A quantidade de vagas máximas deve ser maior que zero."))
        return vagas_maximas

    def clean_periodo_letivo(self):
        periodo_letivo = self.cleaned_data.get('periodo_letivo', '').strip()
        if not re.match(r'^\d{4}/[1-2]$', periodo_letivo):
            raise forms.ValidationError(_("O período letivo deve seguir o formato AAAA/N (ex: 2026/1)."))
        return periodo_letivo
