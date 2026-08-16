# SGA — Sistema de Gestão Acadêmica

## 🗄️ Modelagem de Dados e Modelo Relacional

| Metadado | Detalhe |
| :--- | :--- |
| **Versão** | `0.3` |
| **Domínio** | Ensino Superior |
| **SGBD Referência** | PostgreSQL 16 (Django ORM) |

---

## 1. Dicionário de Entidades

### 1.1 `Usuario` (Model Base de Autenticação)
Representa as contas de acesso ao sistema (`CustomUser`).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `full_name` | `VARCHAR(255)` | Sim | Nome completo do usuário |
| `email` | `VARCHAR(255)` (Unique) | Sim | Identificador de login (normalizado em minúsculas) |
| `password` | `VARCHAR(255)` | Sim | Hash de senha nativo do Django (PBKDF2/Argon2) |
| `role` | `VARCHAR(20)` (Enum) | Sim | `ALUNO`, `PROFESSOR`, `SECRETARIA`, `COORDENACAO` |
| `is_active` | `BOOLEAN` | Sim | Padrão: `True` |
| `must_change_password` | `BOOLEAN` | Sim | Padrão: `False` (força troca no 1º acesso) |
| `created_at` | `TIMESTAMPTZ` | Sim | Data e hora de criação |

---

### 1.1a `TokenRecuperacaoSenha` `[ROADMAP - FASE 2]`
Armazena tokens temporários para redefinição de senha via e-mail (RF03a).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `usuario_id` | `BIGINT` (FK → `Usuario.id`) | Sim | Usuário solicitante |
| `token` | `VARCHAR(255)` (Unique) | Sim | Token único enviado no link |
| `expira_em` | `TIMESTAMPTZ` | Sim | Validade temporária (ex.: 30 min) |
| `usado` | `BOOLEAN` | Sim | Padrão: `False` |
| `criado_em` | `TIMESTAMPTZ` | Sim | Registro automático |

---

### 1.2 `Aluno` (Perfil Discente)
Informações acadêmicas do discente vinculadas ao usuário.

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `usuario_id` | `BIGINT` (FK → `Usuario.id`, 1:1) | Sim | Conta de usuário associada |
| `matricula` | `VARCHAR(20)` (Unique) | Sim | Registro Acadêmico (RA) |
| `curso_id` | `BIGINT` (FK → `Curso.id`) | Sim | Curso vinculado |
| `situacao` | `VARCHAR(20)` (Enum) | Sim | `ATIVO`, `TRANCADO`, `TRANSFERIDO`, `FORMADO`, `CANCELADO` |
| `data_ingresso` | `DATE` | Sim | Data de início do curso |

---

### 1.3 `Professor` (Perfil Docente)
Informações acadêmicas do docente vinculadas ao usuário.

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `usuario_id` | `BIGINT` (FK → `Usuario.id`, 1:1) | Sim | Conta de usuário associada |
| `registro_funcional` | `VARCHAR(30)` (Unique) | Sim | Código de registro funcional |
| `titulacao` | `VARCHAR(100)` | Não | Ex.: *Especialista*, *Mestre*, *Doutor* |

---

### 1.4 `DocumentoAluno` `[ROADMAP - FASE 2]`
Documentação cadastral arquivada pela Secretaria (RN29).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `aluno_id` | `BIGINT` (FK → `Aluno.id`) | Sim | Aluno proprietário |
| `tipo` | `VARCHAR(30)` (Enum) | Sim | `RG`, `CPF`, `HISTORICO_EM`, `COMPROVANTE_RESIDENCIA` |
| `arquivo_path` | `VARCHAR(300)` | Sim | Caminho do arquivo armazenado |
| `enviado_em` | `TIMESTAMPTZ` | Sim | Registro automático |

---

### 1.5 `TransferenciaAluno` `[ROADMAP - FASE 2]`
Histórico de transferências registrado pela Secretaria (RN16).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `aluno_id` | `BIGINT` (FK → `Aluno.id`) | Sim | Aluno transferido |
| `tipo` | `VARCHAR(10)` (Enum) | Sim | `ENTRADA` ou `SAIDA` |
| `instituicao` | `VARCHAR(150)` | Sim | Instituição de origem ou destino |
| `data` | `DATE` | Sim | Data da transferência |
| `observacao` | `TEXT` | Não | Detalhes adicionais |

---

### 1.6 `Curso`
Cursos de graduação mantidos pela Coordenação (RN05).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `nome` | `VARCHAR(150)` | Sim | Ex.: *Análise e Desenvolvimento de Sistemas* |
| `descricao` | `TEXT` | Não | Detalhamento do curso |
| `ativo` | `BOOLEAN` | Sim | Padrão: `True` |

---

### 1.7 `Disciplina`
Disciplinas pertencentes aos cursos (RN05).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `nome` | `VARCHAR(100)` | Sim | Ex.: *Programação Orientada a Objetos* |
| `carga_horaria` | `INTEGER` | Sim | Carga horária total (ex.: 80h) |
| `ativa` | `BOOLEAN` | Sim | Padrão: `True` |

---

### 1.8 `GradeCurricular` (Tabela Associativa Curso × Disciplina)
Composição da matriz curricular de cada curso.

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `curso_id` | `BIGINT` (FK → `Curso.id`) | Sim | Curso relacionado |
| `disciplina_id` | `BIGINT` (FK → `Disciplina.id`) | Sim | Disciplina associada |
| `semestre_sugerido` | `INTEGER` | Não | Semestre recomendado (ex.: 1º a 6º) |
| `pre_requisito_id` | `BIGINT` (FK → `Disciplina.id`) | Não | `[ROADMAP - FASE 3]` Disciplina pré-requisito |

---

### 1.9 `Turma` (Oferta de Disciplina)
Oferta concreta de uma disciplina em um período letivo (RN07, RN40).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `disciplina_id` | `BIGINT` (FK → `Disciplina.id`) | Sim | Disciplina ofertada |
| `professor_id` | `BIGINT` (FK → `Professor.id`) | Não | Professor alocado (obrigatório para publicação) |
| `periodo_letivo` | `VARCHAR(10)` | Sim | Ex.: *2026/1* |
| `sala` | `VARCHAR(30)` | Não | Local das aulas |
| `vagas_maximas` | `INTEGER` | Sim | Capacidade máxima de vagas (RN10) |
| `vagas_ocupadas` | `INTEGER` (Calculado) | — | Calculado via `COUNT(matrículas ativas)` |

---

### 1.10 `Horario`
Grade de horários das aulas da turma (RN09).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `turma_id` | `BIGINT` (FK → `Turma.id`) | Sim | Turma associada |
| `dia_semana` | `VARCHAR(3)` (Enum) | Sim | `SEG`, `TER`, `QUA`, `QUI`, `SEX`, `SAB` |
| `hora_inicio` | `TIME` | Sim | Horário de início da aula |
| `hora_fim` | `TIME` | Sim | Horário de encerramento da aula |

---

### 1.11 `Matricula`
Vínculo de matrícula do Aluno na Turma (RN10, RN12).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `aluno_id` | `BIGINT` (FK → `Aluno.id`) | Sim | Aluno matriculado |
| `turma_id` | `BIGINT` (FK → `Turma.id`) | Sim | Turma escolhida |
| `status` | `VARCHAR(20)` (Enum) | Sim | `ATIVA`, `TRANCADA`, `CONCLUIDA`, `CANCELADA` |
| `matriculado_em` | `TIMESTAMPTZ` | Sim | Registro automático |

---

### 1.12 `Avaliacao`
Instrumentos de avaliação cadastrados pela turma (RN17).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `turma_id` | `BIGINT` (FK → `Turma.id`) | Sim | Turma correspondente |
| `nome` | `VARCHAR(50)` | Sim | Ex.: *P1*, *P2*, *Trabalho*, *Exame Final* |
| `peso` | `DECIMAL(4,2)` | Não | Peso para cálculo da média |
| `periodo` | `VARCHAR(20)` | Sim | Período ou etapa da avaliação |
| `data` | `DATE` | Não | Data da prova/entrega |

---

### 1.13 `Nota`
Notas lançadas pelo professor para os alunos (RN18, RN20).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `avaliacao_id` | `BIGINT` (FK → `Avaliacao.id`) | Sim | Avaliação vinculada |
| `aluno_id` | `BIGINT` (FK → `Aluno.id`) | Sim | Aluno avaliado |
| `valor` | `DECIMAL(4,2)` | Sim | Nota entre $0,00$ e $10,00$ |

---

### 1.14 `Falta`
Registro diário de presença/ausência (RN21).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `turma_id` | `BIGINT` (FK → `Turma.id`) | Sim | Turma |
| `aluno_id` | `BIGINT` (FK → `Aluno.id`) | Sim | Aluno |
| `data_aula` | `DATE` | Sim | Data da aula realizada |
| `presente` | `BOOLEAN` | Sim | `True` = Presente, `False` = Ausente |

---

### 1.15 `Material` `[ROADMAP - FASE 2]`
Materiais de aula disponibilizados pelo professor (RN24).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `turma_id` | `BIGINT` (FK → `Turma.id`) | Sim | Turma associada |
| `titulo` | `VARCHAR(150)` | Sim | Título descritivo |
| `tipo` | `VARCHAR(10)` (Enum) | Sim | `ARQUIVO` ou `LINK` |
| `url_ou_path` | `VARCHAR(300)` | Sim | URL ou caminho do arquivo |
| `postado_em` | `TIMESTAMPTZ` | Sim | Registro automático |

---

### 1.16 `Comunicado` `[ROADMAP - FASE 2]`
Avisos no mural publicados pela Coordenação (RN26).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `titulo` | `VARCHAR(100)` | Sim | Título do comunicado |
| `conteudo` | `TEXT` | Sim | Mensagem em texto |
| `destinatario` | `VARCHAR(20)` (Enum) | Sim | `TODOS`, `PROFESSORES`, `ALUNOS`, `CURSO_ESPECIFICO` |
| `curso_id` | `BIGINT` (FK → `Curso.id`) | Não | Preenchido se destinatário for por curso |
| `autor_id` | `BIGINT` (FK → `Usuario.id`) | Sim | Usuário da Coordenação autor |
| `publicado_em` | `TIMESTAMPTZ` | Sim | Registro automático |

---

### 1.17 `AuditoriaLog` `[MVP]`
Logs de alteração imutáveis em notas e faltas (RN30, RN31).

| Atributo | Tipo SQL / ORM | Obrigatório | Observação |
| :--- | :--- | :---: | :--- |
| `id` | `BIGINT` (PK, Auto) | Sim | Identificador único |
| `usuario_id` | `BIGINT` (FK → `Usuario.id`) | Sim | Usuário responsável pela alteração |
| `tabela_afetada` | `VARCHAR(50)` | Sim | Ex.: `Nota`, `Falta` |
| `registro_id` | `BIGINT` | Sim | ID do registro alterado |
| `valor_antigo` | `TEXT` | Não | Estado anterior do dado |
| `valor_novo` | `TEXT` | Não | Novo estado do dado |
| `realizado_em` | `TIMESTAMPTZ` | Sim | Data e hora exatas da alteração |
