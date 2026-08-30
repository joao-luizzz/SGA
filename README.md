# SGA — Sistema de Gestão Acadêmica

O **SGA (Sistema de Gestão Acadêmica)** é um monólito Django para instituições de ensino superior. O projeto centraliza rotinas administrativas e pedagógicas; alunos consultam as próprias matrículas, notas, médias e frequência.

---

## 🛠️ Stack Tecnológica (Fase 1)

* **Linguagem**: Python 3.12+
* **Framework Web**: Django 5.1+ (Django Templates + HTMX)
* **Estilização**: Bootstrap 5 + Bootstrap Icons
* **Banco de Dados**: PostgreSQL 16
* **Testes**: pytest + pytest-django
* **Ambiente**: Docker & Docker Compose

---

## 📚 Documentação

A documentação técnica e funcional está em [`/docs`](docs/). Para a entrega, consulte o [roteiro de demonstração e checklist](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md).

---

## 📁 Estrutura do Projeto

```text
/home/joao/Projects/SGA/
├── config/             # Configurações do Django (settings, urls, wsgi, asgi)
├── apps/
│   ├── accounts/       # Autenticação, CustomUser (Email), Perfis e RBAC
│   ├── academics/      # Cursos, Disciplinas, Turmas e alocação docente
│   ├── enrollment/     # Matrícula administrativa e controle de vagas
│   ├── assessments/    # Notas, médias, situação e boletim
│   └── attendance/     # Chamada, frequência e auditoria
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

1. **`ALUNO`**: Consulta exclusiva das próprias matrículas, notas, médias, situação e frequência.
2. **`PROFESSOR`**: Acesso às turmas em que está alocado, diário de classe e lançamento de notas/frequência.
3. **`SECRETARIA`**: Acesso a cadastros administrativos, status do aluno e matrículas.
4. **`COORDENACAO`**: Acesso a cursos, disciplinas, turmas e alocação docente.

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

### Dados de demonstração

```bash
docker compose exec web python manage.py seed_demo
```

O comando é idempotente e cria os quatro perfis, uma turma completa e cenários de aprovação direta, exame e reprovação por falta. As credenciais estão no [roteiro de demonstração](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md).

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

### Cobertura de testes incluída

- `CustomUser`, autenticação, primeira senha e RBAC.
- CRUD acadêmico e separação entre Secretaria e Coordenação.
- Matrícula administrativa, vagas, duplicidade ativa e nova tentativa após cancelamento/trancamento.
- Chamada, frequência, notas, médias, Exame Final e situações acadêmicas.
- Isolamento de turmas do Professor e boletim do Aluno.
- Transações em lote e auditoria imutável de notas e faltas.
- Seed idempotente e fluxo ponta a ponta do MVP.

---

## Escopo da Fase 1

O MVP usa `CustomUser`, Django Templates, Bootstrap 5, HTMX, PostgreSQL/Docker Compose e Pytest. `Disciplina` liga-se diretamente a `Curso`; horários ficam em `Turma.horarios`; `Nota` liga-se à `Matricula` e usa os tipos `P1`, `P2`, `TRABALHO` e `EXAME`. Média, frequência, vagas e situação são calculadas.

Auto-matrícula, materiais, calendário, comunicados, recuperação de senha, transferências, documentos, financeiro, aplicativo mobile, integrações externas e pré-requisitos permanecem no roadmap.
