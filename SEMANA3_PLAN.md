# 📋 Plano de Trabalho: Semana 3 — Calendário, Grade e Conflitos de Horário (#33)

Este documento divide e organiza as entregas da **Semana 3** em partes lógicas de desenvolvimento incremental para garantir qualidade, rastreabilidade, cobertura de testes e commits limpos.

---

## 🗺️ Visão Geral do Backlog (#33)
* **Objetivo:** Evoluir as turmas e a grade horária com validações rígidas de conflito.
* **Sub-issues envolvidas:**
  - 🛠️ **#44** Modelar horários e grade acadêmica
  - 👁️ **#45** Exibir calendário por perfil
  - 🧪 **#46** Testar regras da grade acadêmica
  - ⚙️ **#57** Criar montagem da grade pela coordenação
  - 🛑 **#58** Validar conflitos de professor e turma (e sala)

---

## 🗂️ Fatiamento em Partes de Trabalho

#### 🟥 Parte 1: Modelagem e Migração de Dados (#44)
*Modelar a estrutura relacional de grade horária substituindo gradualmente o formato textual atual de `Turma.horarios`.*

- [x] **1.1. Criar Modelo `HorarioTurma`** em `apps/academics/models.py`:
  - `turma` (ForeignKey para `Turma`)
  - `dia_semana` (CharField com escolhas: `SEG`, `TER`, `QUA`, `QUI`, `SEX`, `SAB`, `DOM`)
  - `hora_inicio` (TimeField)
  - `hora_fim` (TimeField)
  - *Meta:* Constraint de unicidade por `turma` + `dia_semana` + `hora_inicio` + `hora_fim`.
- [x] **1.2. Criar Modelo `EventoCalendario`** (Opcional/Futuro se necessário, focado em eventos gerais da instituição):
  - `titulo`, `descricao`, `tipo`, `inicio` (DateTimeField), `fim` (DateTimeField), `escopo` (GERAL, CURSO, TURMA, PAPEL), `autor` (FK para `CustomUser`), `ativo`.
- [x] **1.3. Estratégia de Migração Segura de `Turma.horarios`:**
  - Criar migração de dados que interprete a string de horários existente (usando `parse_horarios_lista`) e popule `HorarioTurma` de forma reversível.
  - Manter compatibilidade temporária (com leitura de `Turma.horarios` herdando/populando do novo modelo se necessário, ou migração direta isolada).
- [x] **1.4. Validar e Aplicar Migrações** no banco de dados local.

---

### 🟨 Parte 2: Regras de Negócio, Serviços e Testes de Conflitos (#58 e #46)
*Implementar validadores robustos em `services.py`/`selectors.py` e garantir 100% de cobertura nos testes do pytest antes de construir as telas.*

- [ ] **2.1. Criar Validações de Conflito em `apps/academics/services.py`:**
  - **Inconsistência de intervalo:** Rejeitar se `hora_inicio >= hora_fim`.
  - **Conflito de Professor:** Impedir alocação do mesmo professor em turmas/horários sobrepostos no mesmo período letivo (**RN09**).
  - **Conflito de Turma:** Impedir alocação da mesma turma em disciplinas/horários sobrepostos no mesmo período letivo.
  - **Conflito de Sala:** Impedir que uma mesma sala de aula receba mais de uma turma no mesmo dia e intervalo de horário.
- [ ] **2.2. Escrever Testes Automatizados em `tests/test_academics/` (#46):**
  - Testar conflitos de professor (sobreposição parcial, total e cruzada).
  - Testar conflitos de turma.
  - Testar conflitos de sala de aula.
  - Testar intervalos com horários inválidos.
  - Testar permissões de acesso e restrições por perfil.
  - *Meta:* Manter a cobertura geral do projeto acima de 85% (atualmente em 87.47%).

---

### 🟩 Parte 3: Montagem de Grade pela Coordenação (#57)
*Desenvolver a interface administrativa em Bootstrap 5 + HTMX para que a coordenação possa gerenciar a grade semanal de cada turma.*

- [ ] **3.1. Criar Formulários de Cadastro/Edição (`forms.py`):**
  - `HorarioTurmaForm` com validações limpas disparando os erros amigáveis de conflito da Parte 2.
- [ ] **3.2. Implementar Views e Rotas no App Acadêmico:**
  - CRUD completo para `HorarioTurma` protegido por controle de acesso por papel (**RBAC** - restrito à Coordenação).
  - Filtros interativos por Curso, Turma e Período Letivo para facilitar a manutenção.
- [ ] **3.3. Construir Templates Responsivos:**
  - Usar HTMX para adicionar/remover horários de forma parcial e dinâmica (sem recarregar a página inteira).
  - Feedback visual claro de sucesso e mensagens de erro específicas em caso de conflitos de horário.

---

### 🟦 Parte 4: Exibição da Grade / Calendário por Perfil (#45)
*Criar visualizações customizadas e seguras para cada tipo de usuário no sistema.*

- [ ] **4.1. Visualização do Aluno:**
  - Grid semanal apresentando apenas as disciplinas e horários das turmas em que o aluno logado possui matrícula ativa.
- [ ] **4.2. Visualização do Professor:**
  - Agenda individual com horários e salas das turmas sob sua responsabilidade.
- [ ] **4.3. Visualização de Secretaria e Coordenação:**
  - Grade horária completa da instituição, com filtros avançados.
- [ ] **4.4. Integração na Interface Lateral:**
  - Adicionar link de navegação responsivo no componente `sidebar.html`.

---

## 📈 Acompanhamento do Progresso

| Parte | Tópico | Status | Descrição |
| :---: | :--- | :---: | :--- |
| 🟥 | **Parte 1: Modelos e Migrações** | ✅ **Concluído** | Criação de `HorarioTurma`, `EventoCalendario` e migração reversível. |
| 🟨 | **Parte 2: Regras e Testes** | ⚙️ **Em Andamento** | Criação de services de validação e testes automatizados. |
| 🟩 | **Parte 3: Montagem Coordenação** | ⏳ **A Fazer** | CRUD e interface com HTMX sob regras de RBAC. |
| 🟦 | **Parte 4: Exibições por Perfil** | ⏳ **A Fazer** | Grades customizadas de Aluno, Professor e Administrativo. |

---

## 🛡️ Regras de Ouro
1. **Estilo de Commits:** Commits incrementais usando `feat(academics):`, `fix(academics):`, `test(academics):` em português.
2. **Não Quebrar builds:** Testes devem rodar e passar antes de cada commit.
3. **Pristine working tree:** Sempre solicitar confirmação antes de qualquer commit ou alteração no GitHub.
