from django.contrib import admin
from .models import Matricula

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'turma', 'status', 'created_at')
    list_filter = ('status', 'turma__disciplina', 'turma__periodo_letivo')
    search_fields = ('aluno__full_name', 'aluno__email', 'turma__disciplina__nome')
    autocomplete_fields = ('aluno', 'turma')
    readonly_fields = ('created_at', 'updated_at')
