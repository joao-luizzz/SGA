from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import CustomUser, UserRole
from academics.models import Curso, Disciplina, Turma
from assessments.models import TipoAvaliacao
from assessments.services import lancar_notas_em_lote
from attendance.models import Falta
from attendance.services import registrar_chamada
from enrollment.models import Matricula, StatusMatricula


DEMO_PASSWORD = 'SgaDemo2026!'


class Command(BaseCommand):
    help = 'Cria ou atualiza dados idempotentes para demonstração do MVP.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=DEMO_PASSWORD,
            help='Senha definida para todas as contas de demonstração.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        usuarios = {
            'secretaria': self._usuario(
                'secretaria.demo@sga.edu.br', 'Secretaria Demo', UserRole.SECRETARIA, password
            ),
            'coordenacao': self._usuario(
                'coordenacao.demo@sga.edu.br', 'Coordenação Demo', UserRole.COORDENACAO, password
            ),
            'professor': self._usuario(
                'professor.demo@sga.edu.br', 'Professor Demo', UserRole.PROFESSOR, password
            ),
            'aprovado': self._usuario(
                'aluno.aprovado@sga.edu.br', 'Aluno Aprovado Direto', UserRole.ALUNO, password
            ),
            'exame': self._usuario(
                'aluno.exame@sga.edu.br', 'Aluno Elegível ao Exame', UserRole.ALUNO, password
            ),
            'falta': self._usuario(
                'aluno.falta@sga.edu.br', 'Aluno Reprovado por Falta', UserRole.ALUNO, password
            ),
        }

        curso, _ = Curso.objects.update_or_create(
            codigo='ADS-DEMO',
            defaults={
                'nome': 'Análise e Desenvolvimento de Sistemas — Demo',
                'descricao': 'Curso criado pelo seed de demonstração do MVP.',
                'ativo': True,
            },
        )
        disciplina, _ = Disciplina.objects.update_or_create(
            codigo='ES-DEMO',
            defaults={
                'nome': 'Engenharia de Software — Demo',
                'carga_horaria': 80,
                'curso': curso,
                'ativo': True,
            },
        )
        turma, _ = Turma.objects.update_or_create(
            disciplina=disciplina,
            periodo_letivo='2026/2',
            defaults={
                'horarios': 'SEG 19:00-21:00, QUA 19:00-21:00',
                'sala': 'Laboratório 01',
                'vagas_maximas': 30,
                'professor': usuarios['professor'],
                'ativo': True,
            },
        )

        matriculas = {
            chave: self._matricula_ativa(aluno, turma)
            for chave, aluno in (
                ('aprovado', usuarios['aprovado']),
                ('exame', usuarios['exame']),
                ('falta', usuarios['falta']),
            )
        }
        lancar_notas_em_lote(usuarios['professor'], turma, {
            matriculas['aprovado'].pk: {
                TipoAvaliacao.P1: Decimal('8.00'),
                TipoAvaliacao.P2: Decimal('7.00'),
                TipoAvaliacao.TRABALHO: Decimal('9.00'),
            },
            matriculas['exame'].pk: {
                TipoAvaliacao.P1: Decimal('5.00'),
                TipoAvaliacao.P2: Decimal('5.00'),
                TipoAvaliacao.TRABALHO: Decimal('5.00'),
            },
            matriculas['falta'].pk: {
                TipoAvaliacao.P1: Decimal('8.00'),
                TipoAvaliacao.P2: Decimal('8.00'),
                TipoAvaliacao.TRABALHO: Decimal('8.00'),
            },
        })

        for indice in range(4):
            data_aula = date(2026, 8, 3) + timedelta(days=indice * 7)
            presencas_esperadas = {
                usuarios['aprovado'].pk: True,
                usuarios['exame'].pk: True,
                usuarios['falta'].pk: indice < 2,
            }
            existentes = {
                falta.aluno_id: falta.presente
                for falta in Falta.objects.filter(turma=turma, data_aula=data_aula)
            }
            if existentes != presencas_esperadas:
                registrar_chamada(
                    usuarios['professor'], turma, data_aula, presencas_esperadas
                )

        self.stdout.write(self.style.SUCCESS('Dados de demonstração do MVP prontos.'))
        self.stdout.write(f'Senha das contas demo: {password}')

    @staticmethod
    def _usuario(email, full_name, role, password):
        usuario, _ = CustomUser.objects.update_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'role': role,
                'is_active': True,
                'must_change_password': False,
            },
        )
        usuario.set_password(password)
        usuario.save(update_fields=['password'])
        return usuario

    @staticmethod
    def _matricula_ativa(aluno, turma):
        matricula = Matricula.objects.filter(
            aluno=aluno,
            turma=turma,
            status=StatusMatricula.ATIVA,
        ).first()
        if matricula is None:
            matricula = Matricula.objects.create(
                aluno=aluno,
                turma=turma,
                status=StatusMatricula.ATIVA,
            )
        return matricula
