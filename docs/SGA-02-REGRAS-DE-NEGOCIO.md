# SGA — Sistema de Gestão Acadêmica

## 📜 Regras de Negócio (RN)

| Metadado | Detalhe |
| :--- | :--- |
| **Versão** | `0.3` |
| **Domínio** | Ensino Superior |
| **Escopo Referência** | `SGA-01-ESCOPO.md` |

---

## 1. Perfis e Hierarquia de Acesso

| Perfil | Criação no Sistema | Escopo de Acesso & Atribuições |
| :--- | :--- | :--- |
| **Secretaria** | Seed inicial do sistema ou cadastro por outro usuário da Secretaria | **Administrativo:** Cadastro de Alunos e Professores; Matrícula/Cancelamento em turmas; Controle da situação cadastral; Registro de transferências; Upload de documentos. |
| **Coordenação** | Seed inicial do sistema ou cadastro por usuário de Coordenação | **Pedagógico:** Gestão de Cursos, Disciplinas e Grade Curricular; Abertura de Turmas (vagas, horário, sala); Alocação de Professores; Calendário e Comunicados. |
| **Professor** | Cadastrado pela Secretaria | **Docente:** Acesso exclusivo às turmas em que está alocado; Lançamento de notas e presenças/faltas; Postagem de materiais. |
| **Aluno** | Cadastrado pela Secretaria | **Discente:** Acesso exclusivo aos próprios dados (boletim de notas, faltas, frequência, materiais, comunicados). |

---

## 2. Regras Detalhadas por Módulo

### 🔐 Perfis e Permissões (RBAC)
* **RN01 `[MVP]`**: Um usuário possui exatamente um perfil entre: `SECRETARIA`, `COORDENACAO`, `PROFESSOR` ou `ALUNO`.
* **RN02 `[MVP]`**: Um Professor só pode lançar ou editar notas e faltas nas turmas às quais está formalmente alocado pela Coordenação.
* **RN03 `[MVP]`**: Um Aluno só pode visualizar notas, faltas e materiais das turmas nas quais está efetivamente matriculado.
* **RN04a `[MVP]`**: A Secretaria não realiza abertura de turmas, alocação de professores, definição de grade curricular ou publicação de comunicados — ações exclusivas da Coordenação.
* **RN04b `[MVP]`**: A Coordenação não realiza cadastro de novos usuários (alunos/professores), matrículas de alunos, transferências ou upload de documentos — ações exclusivas da Secretaria.
* **RN04c `[ROADMAP - FASE 2]`**: Todo usuário poderá solicitar recuperação de senha ("esqueci minha senha") via link enviado por e-mail com expiração temporária (ex.: 30 minutos).

---

### 🏛️ Estrutura Acadêmica
* **RN05 `[MVP]`**: Todo Curso possui nome, descrição e uma grade curricular própria (conjunto de disciplinas).
* **RN06 `[MVP]`**: Todo Aluno é vinculado a um Curso no momento do cadastro inicial, mas se matricula individualmente em Turmas (disciplinas) a cada período letivo — não existe turma fixa compartilhada.
* **RN07 `[MVP]`**: Uma Turma é a oferta de uma Disciplina em um período letivo específico, com limite máximo de vagas, horário e sala definidos pela Coordenação.
* **RN08 `[MVP]`**: Cada Turma é ministrada por um Professor responsável alocado pela Coordenação.
* **RN09 `[MVP]`**: O horário de uma turma define dia da semana e horário de início/fim. Não pode haver conflito de horário para o mesmo Professor no mesmo dia e horário.
* **RN40 `[MVP]`**: A turma pode ser criada pela Coordenação sem professor alocado inicialmente, mas só fica disponível para matrícula após possuir professor alocado, horário, sala e limite de vagas configurados.

---

### 📝 Matrícula em Disciplinas
* **RN10 `[MVP]`**: Um Aluno só pode ser matriculado em uma Turma se houver vagas disponíveis (`COUNT(matrículas ativas) < vagas_máximas`). Ao atingir o limite, a matrícula deve ser bloqueada.
* **RN10a `[ROADMAP - FASE 2]`**: A matrícula do aluno por autoatendimento só é permitida durante a janela de matrícula aberta no calendário acadêmico.
* **RN11 `[MVP]`**: A quantidade de vagas disponíveis deve ser calculada dinamicamente com base nas matrículas ativas.
* **RN12 `[MVP]`**: A matrícula em uma Turma possui status próprio: `Ativa`, `Trancada`, `Concluída` ou `Cancelada`.
* **RN13 `[ROADMAP - FASE 3]`**: Não há validação de pré-requisitos entre disciplinas no MVP. Essa regra é reservada para a Fase 3.
* **RN13a `[MVP]`**: No MVP, o cancelamento de matrícula em turma é realizado exclusivamente pela Secretaria (sem autoatendimento do aluno).
* **RN42 `[MVP]`**: A matrícula do aluno em turma é realizada pela Secretaria. A matrícula por autoatendimento do aluno fica no roadmap da Fase 2.

---

### 🎓 Situação de Matrícula do Aluno
* **RN14 `[MVP]`**: Cada Aluno possui uma situação institucional: `Ativo`, `Trancado`, `Transferido`, `Formado` ou `Cancelado`. As alterações são efetuadas pela Secretaria.
* **RN15 `[MVP]`**: Alunos com situação `Trancado` ou `Cancelado` não podem ser matriculados em novas turmas.
* **RN16 `[ROADMAP - FASE 2]`**: Registro de transferências de entrada (exigindo instituição de origem e data) e de saída (exigindo instituição de destino e data).
* **RN39 `[ROADMAP - FASE 2]`**: Caso a transferência seja implementada, será simplificada, registrando apenas dados de instituição e data.
* **RN47 `[MVP]`**: O aluno reprovado poderá cursar novamente a disciplina em outro período letivo. A tentativa anterior permanece registrada com o resultado de reprovação.

---

### 📊 Avaliação e Cálculo de Médias
* **RN17 `[MVP]`**: O cálculo da média parcial do aluno na disciplina é realizado pela fórmula:
  $$\text{Média Parcial} = \frac{P1 + P2 + \text{Trabalho}}{3}$$
* **RN18 `[MVP]`**: A média da disciplina deve ser recalculada automaticamente sempre que uma nota for lançada, editada ou removida.
* **RN19 `[MVP]`**: Critérios de aprovação e situação por disciplina:
  * **Média Parcial $\ge 6,0$**: `Aprovado Direto`.
  * **$4,0 \le \text{Média Parcial} < 6,0$**: Elegível para `Exame Final` de recuperação.
  * **Média Parcial $< 4,0$**: `Reprovado por Nota`.
* **RN20 `[MVP]`**: Apenas o Professor responsável pela turma pode lançar ou editar notas.
* **RN32 `[MVP]`**: A média parcial utiliza notas na escala de $0,0$ a $10,0$.
* **RN33 `[MVP]`**: A média mínima para aprovação direta é $6,0$.
* **RN34 `[MVP]`**: Alunos com média parcial entre $4,0$ e $5,9$ e frequência $\ge 75\%$ realizam o Exame Final.
* **RN35 `[MVP]`**: A média final pós-exame é calculada por:
  $$\text{Média Final} = \frac{\text{Média Parcial} + \text{Nota do Exame}}{2}$$
  Aprovação exige Média Final $\ge 6,0$.

---

### ⏱️ Frequência e Presença
* **RN21 `[MVP]`**: A frequência é registrada por aula/data para cada aluno matriculado (presente/ausente).
* **RN22 `[MVP]`**: O percentual de frequência do aluno é recalculado automaticamente a cada falta registrada ou alterada.
* **RN23 `[MVP]`**: A frequência mínima obrigatória para aprovação é de **75%**.
* **RN36 `[MVP]`**: Aluno com frequência abaixo de **75%** é reprovado por falta.
* **RN48 `[MVP]`**: Frequência inferior a **75%** resulta em `Reprovado por Falta` e **impede** a realização do Exame Final de recuperação.

---

### 📢 Materiais, Comunicados e Calendário
* **RN24 `[ROADMAP - FASE 2]`**: Somente o Professor responsável pode publicar materiais de aula na sua turma.
* **RN25 `[ROADMAP - FASE 2]`**: Materiais podem ser arquivos (PDF, DOCX, PPTX) ou links externos (máx. 20MB).
* **RN26 `[ROADMAP - FASE 2]`**: Comunicados cadastrados pela Coordenação podem ser institucionais, por perfil ou por curso.
* **RN27 `[ROADMAP - FASE 2]`**: Eventos do calendário acadêmico são cadastrados pela Coordenação e visíveis aos alunos e professores.
* **RN38 `[ROADMAP - FASE 2]`**: Comunicados aceitam públicos institucional, por perfil ou por curso.

---

### 📂 Documentação Cadastral e Oficial
* **RN28 `[ROADMAP - FASE 3]`**: A emissão de documentos oficiais (histórico escolar, declaração de matrícula, atestados) fica fora da Fase 1.
* **RN29 `[ROADMAP - FASE 2]`**: Upload e armazenamento de documentos cadastrais do aluno (RG, CPF, comprovante de residência) pela Secretaria.

---

### 🔍 Auditoria e Segurança
* **RN30 `[MVP]`**: Toda alteração de nota ou falta gera registro de auditoria com: usuário responsável, ação realizada, valor anterior, novo valor e data/hora.
* **RN31 `[MVP]`**: Registros de auditoria são imutáveis (não podem ser editados ou excluídos).

---

## 3. Matriz de Classificação das Regras

> [!IMPORTANT]
> **MVP Compromissado (Fase 1):** RN01, RN02, RN03, RN04a, RN04b, RN05, RN06, RN07, RN08, RN09, RN10, RN11, RN12, RN13a, RN14, RN15, RN17, RN18, RN19, RN20, RN21, RN22, RN23, RN30, RN31, RN32, RN33, RN34, RN35, RN36, RN40, RN41, RN42, RN43, RN47, RN48.

> [!NOTE]
> **Roadmap Opcional (Fase 2):** RN04c, RN10a, RN16, RN24, RN25, RN26, RN27, RN29, RN38, RN39, RN44.

> [!WARNING]
> **Roadmap Futuro (Fase 3):** RN13, RN28, RN45.
