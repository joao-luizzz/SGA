import copy
import pytest
from django.template.context import BaseContext
from accounts.models import CustomUser, UserRole

# Monkeypatch Python 3.14 compatibility for Django template context copying in tests
def _base_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    if hasattr(self, 'dicts'):
        duplicate.dicts = self.dicts[:]
    return duplicate

BaseContext.__copy__ = _base_context_copy


@pytest.fixture
def password():
    return "SenhaSegura123!"

@pytest.fixture
def user_aluno(db, password):
    return CustomUser.objects.create_user(
        email="aluno@sga.edu.br",
        full_name="Aluno Teste",
        role=UserRole.ALUNO,
        password=password,
        must_change_password=False
    )

@pytest.fixture
def user_professor(db, password):
    return CustomUser.objects.create_user(
        email="professor@sga.edu.br",
        full_name="Professor Teste",
        role=UserRole.PROFESSOR,
        password=password,
        must_change_password=False
    )

@pytest.fixture
def user_secretaria(db, password):
    return CustomUser.objects.create_user(
        email="secretaria@sga.edu.br",
        full_name="Secretaria Teste",
        role=UserRole.SECRETARIA,
        password=password,
        must_change_password=False
    )

@pytest.fixture
def user_coordenacao(db, password):
    return CustomUser.objects.create_user(
        email="coordenacao@sga.edu.br",
        full_name="Coordenacao Teste",
        role=UserRole.COORDENACAO,
        password=password,
        must_change_password=False
    )

@pytest.fixture
def user_inactive(db, password):
    return CustomUser.objects.create_user(
        email="inativo@sga.edu.br",
        full_name="Usuario Inativo",
        role=UserRole.ALUNO,
        password=password,
        is_active=False
    )

@pytest.fixture
def user_must_change_pw(db, password):
    return CustomUser.objects.create_user(
        email="novo@sga.edu.br",
        full_name="Usuario Primeiro Acesso",
        role=UserRole.ALUNO,
        password=password,
        must_change_password=True
    )
