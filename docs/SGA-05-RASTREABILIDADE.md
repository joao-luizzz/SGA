# SGA — Sistema de Gestão Acadêmica

## 🔗 Matriz de Rastreabilidade (Requisito × Caso de Uso × Regra de Negócio)

| Metadado | Detalhe |
| :--- | :--- |
| **Versão** | `0.3` |
| **Domínio** | Ensino Superior |
| **Escopo Referência** | `SGA-01-ESCOPO.md` / `SGA-02-REGRAS-DE-NEGOCIO.md` / `SGA-03-REQUISITOS.md` |

---

## 1. Mapeamento de Rastreabilidade — MVP Compromissado (Fase 1)

| Requisito | Funcionalidade | Caso de Uso (CU) Relacionado | Regras de Negócio (RN) | Entidades Envolvidas |
| :---: | :--- | :--- | :--- | :--- |
| **RF01** | Autenticação por e-mail | `CU01 — Autenticar Usuário` | RN01 | `CustomUser` |
| **RF02** | Logout seguro | `CU02 — Encerrar Sessão` | RN01 | `CustomUser` |
| **RF03** | Troca obrigatória de senha | `CU03 — Alterar Senha no Primeiro Acesso` | RN01 | `CustomUser` |
| **RF04** | RBAC (Controle por Perfil) | `Transversal — Autorização de Acesso` | RN01, RN02, RN03, RN04a, RN04b | `CustomUser` |
| **RF06** | Visualização de notas | `CU04 — Aluno Consulta Boletim` | RN03, RN17, RN18, RN19 | `CustomUser`, `Matricula`, `Nota` |
| **RF07** | Visualização de faltas | `CU05 — Aluno Consulta Frequência` | RN03, RN21, RN22, RN23, RN48 | `CustomUser`, `Turma`, `Falta` |
| **RF10** | Lançamento de faltas | `CU06 — Professor Registra Chamada` | RN02, RN21, RN22 | `Professor`, `Turma`, `Falta` |
| **RF11** | Lançamento de notas | `CU07 — Professor Lança Notas` | RN02, RN17, RN18, RN20, RN32 | `Professor`, `Turma`, `Nota` |
| **RF13** | Listagem da turma | `CU08 — Professor Consulta Alunos da Turma` | RN02 | `Professor`, `Turma`, `Matricula` |
| **RF14** | CRUD de Professores | `CU09 — Secretaria Administra Professores` | RN01, RN04b | `Usuario`, `Professor` |
| **RF15** | CRUD de Alunos | `CU10 — Secretaria Administra Alunos` | RN01, RN04b, RN06 | `Usuario`, `Aluno`, `Curso` |
| **RF16** | Matrícula por Secretaria | `CU11 — Secretaria Matricula Aluno em Turma` | RN04b, RN10, RN11, RN12, RN13a, RN42 | `Aluno`, `Turma`, `Matricula` |
| **RF17** | Situação de matrícula | `CU12 — Secretaria Altera Situação do Aluno` | RN04b, RN14, RN15 | `Aluno` |
| **RF20** | CRUD de Cursos | `CU13 — Coordenação Gerencia Cursos` | RN04a, RN05 | `Curso` |
| **RF21** | CRUD de Disciplinas | `CU14 — Coordenação Gerencia Disciplinas` | RN04a, RN05 | `Curso`, `Disciplina` |
| **RF22** | Abertura de turmas | `CU15 — Coordenação Abre Turma` | RN04a, RN07, RN09, RN40 | `Turma`, `Horario` |
| **RF23** | Alocação docente | `CU16 — Coordenação Aloca Professor` | RN04a, RN08, RN09, RN40 | `Turma`, `Professor` |
| **RF27** | Cálculo automático de média | `Transversal — Regra de Cálculo de Médias` | RN17, RN18, RN19, RN32–RN35 | `Matricula`, `Nota` |
| **RF28** | Cálculo de frequência | `Transversal — Regra de Cálculo de Frequência` | RN21, RN22, RN23, RN36, RN48 | `Falta`, `Matricula` |
| **RF29** | Controle de vagas | `Transversal — Validação de Capacidade` | RN10, RN11 | `Turma`, `Matricula` |
| **RF30** | Auditoria de alterações | `Transversal — Auditoria de Notas e Faltas` | RN30, RN31 | `AuditoriaLog` |
| **RF31** | Validação de dados | `Transversal — Validação de Formulários` | RN01–RN48 | Todas as Entidades |
| **RF32** | Lançamento de Exame | `CU17 — Professor Lança Nota de Exame` | RN34, RN35, RN48 | `Professor`, `Nota` |
| **RF33** | Resultado acadêmico | `Transversal — Apresentação da Situação Final` | RN19, RN33–RN36, RN48 | `Matricula` |
| **RF34** | Retentativa de disciplina | `CU18 — Aluno Cursa Disciplina Novamente` | RN47 | `Matricula` |
| **RF35** | Matrícula Administrativa | `CU19 — Secretaria Executa Matrícula/Cancelamento` | RN13a, RN42 | `Secretaria`, `Matricula` |

---

## 2. Mapeamento de Rastreabilidade — Roadmap Opcional (Fases 2 e 3)

| Requisito | Funcionalidade | Caso de Uso (CU) Relacionado | Regras de Negócio (RN) | Fase |
| :---: | :--- | :--- | :--- | :---: |
| **RF03a** | Recuperação de senha por e-mail | `CU20 — Solicitar Redefinição de Senha` | RN04c | **Fase 2** |
| **RF05** | Matrícula por autoatendimento | `CU21 — Aluno Realiza Auto-Matrícula` | RN10a, RN42 | **Fase 2** |
| **RF08** | Download de materiais | `CU22 — Aluno Acessa Materiais` | RN24, RN25 | **Fase 2** |
| **RF08a** | Horário consolidado | `CU23 — Aluno Consulta Grade de Horários` | RN09 | **Fase 2** |
| **RF09** | Mural e Calendário | `CU24 — Usuário Consulta Avisos e Calendário` | RN26, RN27, RN38 | **Fase 2** |
| **RF12** | Upload de materiais | `CU25 — Professor Publica Material` | RN24, RN25 | **Fase 2** |
| **RF18** | Transferência de aluno | `CU26 — Secretaria Registra Transferência` | RN16, RN39 | **Fase 2** |
| **RF19** | Documentos cadastrais | `CU27 — Secretaria Anexa Documento Cadastral` | RN29 | **Fase 2** |
| **RF24** | Calendário acadêmico | `CU28 — Coordenação Gerencia Calendário` | RN27 | **Fase 2** |
| **RF25** | Publicação de comunicados | `CU29 — Coordenação Publica Comunicado` | RN26, RN38 | **Fase 2** |
| **RF26** | Relatórios acadêmicos | `CU30 — Coordenação Gera Relatórios` | RN05, RN07 | **Fase 2** |
| **—** | Validação de pré-requisitos | `CU31 — Validação Automática de Pré-Requisitos` | RN13 | **Fase 3** |
| **—** | Emissão de documentos oficiais | `CU32 — Emissão de Histórico e Atestados` | RN28 | **Fase 3** |
