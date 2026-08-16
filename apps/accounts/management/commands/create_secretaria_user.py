import getpass
from django.core.management.base import BaseCommand, CommandError
from accounts.models import CustomUser, UserRole
from accounts.services import create_user_by_admin

class Command(BaseCommand):
    help = "Cria com segurança o primeiro usuário do perfil Secretaria."

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='E-mail do usuário da Secretaria')
        parser.add_argument('--full-name', type=str, help='Nome completo do usuário')
        parser.add_argument('--password', type=str, help='Senha inicial do usuário')
        parser.add_argument(
            '--no-must-change',
            action='store_true',
            help='Não forçar a troca de senha no primeiro acesso'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        full_name = options.get('full_name')
        password = options.get('password')
        must_change = not options.get('no_must_change')

        if not email:
            email = input("E-mail da Secretaria: ").strip()
        if not full_name:
            full_name = input("Nome completo: ").strip()
        if not password:
            password = getpass.getpass("Senha inicial: ").strip()
            confirm_password = getpass.getpass("Confirme a senha inicial: ").strip()
            if password != confirm_password:
                raise CommandError("As senhas informadas não coincidem.")

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise CommandError(f"Usuário com o e-mail '{email}' já existe no sistema.")

        try:
            user = create_user_by_admin(
                email=email,
                full_name=full_name,
                role=UserRole.SECRETARIA,
                password=password,
                must_change_password=must_change
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Usuário da Secretaria '{user.full_name}' ({user.email}) criado com sucesso!"
                )
            )
        except Exception as e:
            raise CommandError(f"Erro ao criar usuário: {str(e)}")
