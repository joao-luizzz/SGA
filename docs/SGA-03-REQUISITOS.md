# SGA — Sistema de Gestão Acadêmica

## 📊 Matriz de Requisitos do Sistema

| Metadado | Detalhe |
| :--- | :--- |
| **Versão** | `0.3` |
| **Domínio** | Ensino Superior |
| **Escopo Referência** | `SGA-01-ESCOPO.md` / `SGA-02-REGRAS-DE-NEGOCIO.md` |

---

## 1. Requisitos Funcionais (RF)

| ID | Funcionalidade | Descrição | Ator | Prioridade | Escopo |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **RF01** | Autenticação por e-mail | Realizar login com e-mail e senha. Redirecionar para o dashboard do perfil correspondente. | Todos | `Alta` | **MVP** |
| **RF02** | Logout | Encerrar a sessão do usuário de forma segura via requisição POST com CSRF. | Todos | `Alta` | **MVP** |
| **RF03** | Troca de senha obrigatória | Exigir troca de senha no primeiro acesso do usuário (`must_change_password=True`). | Todos | `Média` | **MVP** |
| **RF03a** | Recuperação de senha | Permitir que o usuário solicite redefinição de senha via link enviado por e-mail. | Todos | `Alta` | **Roadmap** |
| **RF04** | RBAC (Controle de Acesso) | Restringir o acesso a páginas e ações conforme o perfil (Secretaria, Coordenação, Professor, Aluno). | Sistema | `Alta` | **MVP** |
| **RF05** | Matrícula por autoatendimento | Permitir que o aluno se matricule em turmas abertas durante a janela do calendário. | Aluno | `Alta` | **Roadmap** |
| **RF06** | Visualização de notas | Exibir ao aluno as notas lançadas e a média/situação por disciplina. | Aluno | `Alta` | **MVP** |
| **RF07** | Visualização de faltas | Exibir ao aluno as faltas registradas e o percentual de frequência por disciplina. | Aluno | `Alta` | **MVP** |
| **RF08** | Download de materiais | Permitir que o aluno visualize e baixe materiais postados nas turmas em que está matriculado. | Aluno | `Alta` | **Roadmap** |
| **RF08a** | Horário consolidado | Exibir ao aluno a grade semanal de horários com todas as suas turmas matriculadas. | Aluno | `Alta` | **Roadmap** |
| **RF09** | Mural e Calendário | Exibir ao usuário os comunicados e os eventos do calendário acadêmico. | Todos | `Média` | **Roadmap** |
| **RF10** | Lançamento de faltas | Permitir que o professor registre presença/falta por aula e data para alunos da sua turma. | Professor | `Alta` | **MVP** |
| **RF11** | Lançamento de notas | Permitir que o professor lance e edite notas (P1, P2, Trabalho, Exame Final) para sua turma. | Professor | `Alta` | **MVP** |
| **RF12** | Upload de materiais | Permitir que o professor anexe materiais (arquivo ou link) a uma turma. | Professor | `Alta` | **Roadmap** |
| **RF13** | Listagem da turma | Exibir ao professor a lista de alunos matriculados na turma em que leciona. | Professor | `Média` | **MVP** |
| **RF14** | CRUD de Professores | Cadastrar, editar e inativar usuários com perfil Professor. | Secretaria | `Alta` | **MVP** |
| **RF15** | CRUD de Alunos | Cadastrar, editar e inativar usuários com perfil Aluno. | Secretaria | `Alta` | **MVP** |
| **RF16** | Matrícula por Secretaria | Matricular um aluno em uma turma válida em nome da instituição. | Secretaria | `Alta` | **MVP** |
| **RF17** | Preservação de histórico | Inativar a conta sem apagar matrículas, notas e faltas anteriores. | Secretaria | `Alta` | **MVP** |
| **RF18** | Registro de transferência | Registrar transferência de entrada (de outra IES) ou de saída (para outra IES), com data. | Secretaria | `Média` | **Roadmap** |
| **RF19** | Documentos cadastrais | Anexar documentos do aluno (RG, CPF, histórico, comprovante de residência) ao cadastro. | Secretaria | `Média` | **Roadmap** |
| **RF20** | CRUD de Cursos | Criar, editar e inativar cursos da instituição. | Coordenação | `Alta` | **MVP** |
| **RF21** | CRUD de Disciplinas | Criar, editar e inativar disciplinas, cada uma ligada diretamente a um curso. | Coordenação | `Alta` | **MVP** |
| **RF22** | Abertura de turmas | Ofertar disciplina por período letivo, definindo professor, horário, sala e limite de vagas. | Coordenação | `Alta` | **MVP** |
| **RF23** | Alocação docente | Atribuir um professor responsável a uma turma aberta. | Coordenação | `Alta` | **MVP** |
| **RF24** | Calendário acadêmico | Criar e editar eventos do calendário (provas, feriados, período de matrícula). | Coordenação | `Média` | **Roadmap** |
| **RF25** | Publicação de comunicados | Criar e excluir avisos no mural, direcionados a todos, por perfil ou por curso. | Coordenação | `Média` | **Roadmap** |
| **RF26** | Relatórios acadêmicos | Gerar relatórios de desempenho e frequência por turma. | Coordenação | `Média` | **Roadmap** |
| **RF27** | Cálculo de média | Calcular automaticamente a média do aluno por disciplina conforme a fórmula oficial. | Sistema | `Alta` | **MVP** |
| **RF28** | Cálculo de frequência | Calcular o percentual de frequência do aluno por disciplina e sinalizar reprovação por falta. | Sistema | `Alta` | **MVP** |
| **RF29** | Controle de vagas | Bloquear automaticamente matrículas quando o limite máximo de vagas da turma for atingido. | Sistema | `Alta` | **MVP** |
| **RF30** | Auditoria de alterações | Registrar log imutável de alterações em notas e faltas (quem alterou, valor antigo, novo e data). | Sistema | `Média` | **MVP** |
| **RF31** | Validação de formulários | Bloquear submissão de dados inválidos ou campos obrigatórios ausentes. | Sistema | `Média` | **MVP** |
| **RF32** | Lançamento de Exame | Permitir exame apenas com $4,00 \le \text{MP} < 6,00$ e frequência $\ge 75\%$. | Professor | `Alta` | **MVP** |
| **RF33** | Resultado acadêmico | Apresentar `Em andamento`, `Aprovado Direto`, `Elegível para Exame Final`, `Aprovado após Exame`, `Reprovado por Nota` ou `Reprovado por Falta`. | Sistema | `Alta` | **MVP** |
| **RF34** | Retentativa de disciplina | Permitir que o aluno reprovado curse a disciplina em outro período, preservando a tentativa anterior. | Sistema | `Média` | **MVP** |
| **RF35** | Matrícula Administrativa | Matrícula efetuada exclusivamente pela Secretaria no MVP. | Secretaria | `Alta` | **MVP** |

---

## 2. Requisitos Não Funcionais (RNF)

| ID | Categoria | Descrição Técnica |
| :--- | :--- | :--- |
| **RNF01** | Interface | Aplicação web responsiva (Bootstrap 5 + HTMX), acessível via navegadores em desktop e dispositivos móveis. |
| **RNF02** | Segurança de Sessão | Autenticação baseada em sessão segura com cookies HTTPOnly e CSRF tokens. |
| **RNF03** | Proteção de Senhas | Senhas armazenadas obrigatoriamente utilizando o algoritmo de hash nativo do Django (PBKDF2/Argon2). |
| **RNF04** | Desempenho | Tempo de resposta das requisições abaixo de 500ms (p95) em ambiente de desenvolvimento/produção. |
| **RNF05** | Retenção de Auditoria | Logs de auditoria de notas e faltas mantidos de forma imutável. |
| **RNF06** | Arquitetura | Monólito limpo em Django com separação clara de responsabilidades (`services.py`, `selectors.py`). |
| **RNF07** | LGPD | Conformidade com a Lei Geral de Proteção de Dados no armazenamento de dados pessoais e cadastrais. |
| **RNF08** | Escopo | Recursos de upload permanecem fora da Fase 1. |
| **RNF09** | Compatibilidade | Compatibilidade garantida com os navegadores modernos (Chrome, Firefox, Edge, Safari). |
| **RNF10** | Infraestrutura | Ambiente containerizado via Docker e Docker Compose com banco PostgreSQL 16. |
| **RNF11** | Proteção OWASP | Proteção nativa contra SQL Injection, Cross-Site Scripting (XSS) e Open Redirect. |
| **RNF12** | Variáveis de Ambiente | Configurações sensíveis (chaves secretas, credenciais do banco) mantidas em arquivos `.env` não versionados. |

---

## 3. Resumo de Classificação dos Requisitos

> [!IMPORTANT]
> **Requisitos do MVP Compromissado (Fase 1):**
> RF01, RF02, RF03, RF04, RF06, RF07, RF10, RF11, RF13, RF14, RF15, RF16, RF17, RF20, RF21, RF22, RF23, RF27, RF28, RF29, RF30, RF31, RF32, RF33, RF34, RF35.
> RNF01, RNF02, RNF03, RNF04, RNF05, RNF06, RNF07, RNF08, RNF09, RNF10, RNF11, RNF12.

> [!NOTE]
> **Requisitos do Roadmap Opcional (Fases 2 e 3):**
> RF03a, RF05, RF08, RF08a, RF09, RF12, RF18, RF19, RF24, RF25, RF26.
