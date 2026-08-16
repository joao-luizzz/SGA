import pytest
from django.core.exceptions import ValidationError
from accounts.models import CustomUser, UserRole

@pytest.mark.django_db
class TestCustomUserModel:
    def test_create_user_success(self):
        user = CustomUser.objects.create_user(
            email="TESTE@SGA.EDU.BR",
            full_name="Maria Silva",
            role=UserRole.ALUNO,
            password="Password123!"
        )
        assert user.email == "teste@sga.edu.br"
        assert user.full_name == "Maria Silva"
        assert user.role == UserRole.ALUNO
        assert user.is_active is True
        assert user.must_change_password is False
        assert user.check_password("Password123!") is True
        assert str(user) == "Maria Silva (teste@sga.edu.br) - Aluno"

    def test_create_user_missing_email(self):
        with pytest.raises(ValueError, match="O endereço de e-mail é obrigatório"):
            CustomUser.objects.create_user(
                email="",
                full_name="Sem Email",
                role=UserRole.ALUNO,
                password="Password123!"
            )

    def test_create_superuser(self):
        admin = CustomUser.objects.create_superuser(
            email="admin@sga.edu.br",
            full_name="Super Admin",
            password="AdminPassword123!"
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == UserRole.COORDENACAO
