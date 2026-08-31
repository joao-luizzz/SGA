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

## Checklist

- [ ] Containers `web` e `db` ativos; migrations aplicadas.
- [ ] `seed_demo` executado e contas de demonstração acessíveis.
- [ ] Quatro papéis demonstrados: Coordenação, Secretaria, Professor e Aluno.
- [ ] Cadastro/edição de usuários, matrícula e gestão de status demonstrados.
- [ ] Chamada completa, notas, exame, boletim e frequência demonstrados.
- [ ] Retentativa em nova turma/período explicada e histórico anterior preservado.
- [ ] Sem senha real, dado pessoal real ou credencial de produção em tela.
- [ ] Validações locais e CI verdes.

## Limite da apresentação

Não apresentar como pronto: auto-matrícula, recuperação de senha, materiais, calendário, comunicados, documentos, transferências, financeiro, app mobile, integrações ou pré-requisitos. Eles pertencem ao Roadmap, não ao MVP.
