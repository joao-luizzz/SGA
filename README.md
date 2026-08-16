# SGA — Sistema de Gestão Acadêmica

O **SGA (Sistema de Gestão Acadêmica)** é um sistema monólito web desenvolvido em Django para instituições de ensino superior. O projeto centraliza rotinas administrativas da secretaria e pedagógicas da coordenação, permitindo que os alunos gerenciem matrículas, horários e notas.

---

## 🛠️ Stack Tecnológica (Fase 1)

* **Linguagem**: Python 3.12+
* **Framework Web**: Django 5.1+ (Django Templates + HTMX)
* **Estilização**: Bootstrap 5 + Bootstrap Icons
* **Banco de Dados**: PostgreSQL 16
* **Testes**: pytest + pytest-django
* **Ambiente**: Docker & Docker Compose

---

## 📁 Estrutura do Projeto

```text
/home/joao/Projects/SGA/
├── config/             # Configurações do Django (settings, urls, wsgi, asgi)
├── apps/
│   ├── accounts/       # Autenticação, CustomUser (Email), Perfis e RBAC
│   ├── academics/      # Módulo acadêmico (Cursos, Disciplinas, Turmas - Placeholder)
│   ├── enrollment/     # Módulo de matrículas (Placeholder)
│   ├── assessments/    # Módulo de notas e avaliações (Placeholder)
│   └── attendance/     # Módulo de frequência e presença (Placeholder)
├── templates/          # Templates base, componentes, erros 403/404 e dashboards por perfil
├── static/             # Arquivos estáticos (CSS, JS, imagens)
├── tests/              # Suíte de testes automatizados com Pytest
├── requirements/       # Requisitos base e de desenvolvimento local
├── docker-compose.yml  # Orquestração dos serviços Web e PostgreSQL
├── Dockerfile          # Imagem container da aplicação
├── .env.example        # Modelo seguro de variáveis de ambiente
├── pytest.ini          # Configuração do Pytest
├── manage.py
└── README.md
```

---

## 👥 Perfis de Usuário & Permissões (RBAC)

O sistema possui 4 perfis de usuário obrigatórios:

1. **`ALUNO`**: Acesso exclusivo aos dados próprios, boletim e faltas.
2. **`PROFESSOR`**: Acesso às turmas em que está alocado, diário de classe e lançamento de notas/frequência.
3. **`SECRETARIA`**: Acesso a cadastros administrativos, status do aluno e matrículas.
4. **`COORDENACAO`**: Acesso à matriz curricular, cursos, disciplinas, turmas e alocação docente.

---

## 🚀 Como Executar o Projeto

### 1. Clonar e Configurar Variáveis de Ambiente

```bash
git clone https://github.com/joao-luizzz/SGA.git
cd SGA

# Criar o arquivo .env a partir do modelo .env.example
cp .env.example .env
```

### 2. Executar via Docker Compose

```bash
# Subir os containers do PostgreSQL e da Aplicação Django
docker compose up --build -d

# Executar as migrações do banco de dados
docker compose exec web python manage.py migrate

# Verificar status dos serviços
docker compose ps
```

A aplicação estará acessível em: `http://localhost:8000`

---

## 🔐 Criando o Primeiro Usuário da Secretaria

Por ser um sistema fechado sem auto-cadastro público, o primeiro usuário administrativo da **Secretaria** deve ser gerado pelo comando seguro de gerenciamento:

```bash
# Modo Interativo (solicita e-mail, nome e senha):
docker compose exec web python manage.py create_secretaria_user

# Ou Modo Não-Interativo via argumentos:
docker compose exec web python manage.py create_secretaria_user \
  --email admin@sga.edu.br \
  --full-name "Secretaria Principal" \
  --password "SuaSenhaSegura123!"
```

> **Nota**: Novos usuários criados por este comando possuem `must_change_password=True` ativado por padrão. No primeiro login, o sistema redirecionará obrigatoriamente para a tela de alteração de senha antes de permitir o uso do painel.

---

## 🧪 Executando os Testes Automatizados

Os testes do sistema foram implementados com **Pytest** e **pytest-django**:

```bash
# Executar todos os testes via Docker Compose
docker compose exec web pytest

# Executar os testes localmente (com ambiente virtual ativo)
pytest -v
```

### Cobertura de Testes Incluída:
* ✅ Criação e validação do modelo `CustomUser` (login por e-mail e hash nativo Django);
* ✅ Autenticação de credenciais válidas e bloqueio de usuários inativos;
* ✅ Redirecionamento obrigatório para troca de senha no primeiro acesso;
* ✅ Bloqueio de acesso entre perfis (RBAC com resposta HTTP 403);
* ✅ Fluxo de logout e encerramento de sessão.

---

## 📌 Escopo e Rastreabilidade das Issues

Esta entrega aborda e encerra as seguintes tarefas:

* **Closes #1**: Inicialização da fundação técnica, estrutura Django e ambiente Docker Compose com PostgreSQL.
* **Closes #2**: Implementação da aplicação `accounts` com `CustomUser` (e-mail como login), 4 perfis (`ALUNO`, `PROFESSOR`, `SECRETARIA`, `COORDENACAO`), regra de troca obrigatória de senha e comando seguro de seed da Secretaria.
* **Closes #6**: Sistema de autenticação por sessão, RBAC com decorators/mixins, templates Bootstrap 5 + HTMX, páginas customizadas de erro 403/404 e dashboards por perfil.
