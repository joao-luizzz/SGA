# SGA — Roteiro de demonstração e entrega

| Metadado | Valor |
| --- | --- |
| Versão | **1.0 — MVP Fase 1 concluído** |
| Data | **31 de agosto de 2026** |

## Preparação

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo --password 'SgaDemo2026!'
```

`seed_demo` é idempotente e prepara os quatro papéis, uma turma completa e cenários de aprovação direta, exame e reprovação por falta. Todas as contas abaixo usam a senha `SgaDemo2026!`, definida explicitamente no comando. Para usar outra senha, altere o valor de `--password`; não reutilize uma senha real.

| Papel/cenário | E-mail |
| --- | --- |
| Secretaria | `secretaria.demo@sga.edu.br` |
| Coordenação | `coordenacao.demo@sga.edu.br` |
| Professor | `professor.demo@sga.edu.br` |
| Aluno aprovado direto | `aluno.aprovado@sga.edu.br` |
| Aluno elegível ao exame | `aluno.exame@sga.edu.br` |
| Aluno reprovado por falta | `aluno.falta@sga.edu.br` |

## Sequência de demonstração

1. **Coordenação:** entrar com a conta demo de Coordenação, criar/mostrar Curso e Disciplina, abrir ou editar Turma com período, horários textuais validados, sala, vagas e Professor responsável.
2. **Secretaria — usuários:** listar Alunos e Professores, criar ou editar uma conta e mostrar ativação/inativação sem expor credenciais reais.
3. **Secretaria — matrícula:** efetivar matrícula em turma apta e explicar que as vagas são calculadas pelas matrículas ativas.
4. **Secretaria — status e retentativa:** alterar uma matrícula ativa para Trancada, Cancelada ou Concluída; explicar que nova tentativa exige outra Turma/período, preservando o histórico.
5. **Professor — chamada:** abrir somente uma turma própria ativa, registrar uma chamada completa e mostrar o relatório de frequência e a auditoria.
6. **Professor — notas:** lançar P1, P2 e Trabalho para matrículas ativas; mostrar MP e a validação de 0 a 10.
7. **Professor — exame:** no cenário elegível, lançar Exame e mostrar MF; contrastar com o cenário abaixo de 75%, no qual o exame é bloqueado.
8. **Aluno:** entrar com as contas demo e mostrar boletim, situação e frequência sem acesso a registros de outros alunos.
9. **Qualidade:** apresentar a suíte automatizada, a CI nos dois bancos e a separação entre MVP e Roadmap.

## Validação antes da entrega

```bash
docker compose exec web python manage.py check
docker compose exec web pytest
git diff --check
```

Além da execução local em Docker/PostgreSQL, a CI executa, nessa ordem, `python manage.py check`, `python manage.py makemigrations --check --dry-run` e `pytest` nos jobs **SQLite** e **PostgreSQL 16**.

## Checklist da demonstração da Fase 1

- [ ] Containers `web` e `db` ativos; migrations aplicadas.
- [ ] `seed_demo` executado e contas de demonstração acessíveis.
- [ ] Quatro papéis demonstrados: Coordenação, Secretaria, Professor e Aluno.
- [ ] Cadastro/edição de usuários, matrícula e gestão de status demonstrados.
- [ ] Chamada completa, notas, exame, boletim e frequência demonstrados.
- [ ] Retentativa em nova turma/período explicada e histórico anterior preservado.
- [ ] Sem senha real, dado pessoal real ou credencial de produção em tela.
- [ ] Validações locais e CI verdes.

## Estado atual e demonstração da Fase 2 — 08/10/2026

A Fase 1/MVP continua sendo o núcleo documental. Na develop atual também estão integradas as entregas de materiais/comunicados (PR #66), calendário/grade/conflitos (PR #67), relatórios (PR #68), transferências (PR #69) e conclusão dos relatórios com integração da Semana 5 (PR #70).

### Sequência de demonstração

1. Coordenação: curso, disciplina, turma, grade/horários e calendário; mostrar conflitos e filtros por perfil.
2. Secretaria: pessoas, matrícula/status e registro de solicitação de transferência.
3. Professor: materiais nas próprias turmas, chamada e notas; Exame apenas para aluno elegível.
4. Aluno: materiais e comunicados pertinentes, calendário, boletim, situação e frequência próprias.
5. Coordenação: relatórios acadêmicos com filtros combinados; demonstrar motivos de risco, exportação CSV e impressão A4.
6. Secretaria e Coordenação: completar o fluxo de transferência (registro e decisão) e conferir que o histórico acadêmico e os relatórios permanecem preservados.
7. Encerrar com arquitetura, PostgreSQL, testes/CI e estado das fases. Recuperação de senha/notificações estão pendentes; Fase 3 é futura.

Use dados de demonstração e um banco descartável. A validação da PR #70 inclui roteiro de navegador com filtros, CSV, impressão, decisões de transferência e permissões; ela não substitui a preparação específica do ambiente da apresentação.

**Estado:** Fase 1/MVP concluída; Semana 1 concluída; Semana 2 concluída (PR #66); Semana 3 concluída (PR #67); Semana 4 pendente (#35); Semana 5 concluída (#36, #49, #51 e #62; PRs #68–#70); Fase 3 futura (#37).

Não apresentar recuperação de senha ou notificações como implementadas. “Fora do MVP” nos documentos da Fase 1 significa fora do escopo original, não necessariamente ausente do código atual.
