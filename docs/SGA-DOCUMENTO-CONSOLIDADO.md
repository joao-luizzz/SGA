SGA — Sistema de Gestão Acadêmica
Documento Consolidado para Validação do Grupo
Disciplina: Laboratório de Engenharia de Software Professor Responsável: Rodrigo Salgado Integrantes: Andrey Kerges Nascimento, Alexandre Hesse, Max Iago Villafan, João Luiz, Vitor Augusto Versão: 0.4 — Decisões consolidadas após revisão do grupo Data: Agosto/2026


________________


📋 Como usar este documento
Este arquivo reúne tudo que já foi definido sobre o projeto: escopo, regras de negócio, requisitos funcionais/não funcionais, modelagem de dados e rastreabilidade. O objetivo é o grupo revisar em conjunto e confirmar se todos concordam.


* Se você concorda com um ponto, não precisa fazer nada.
* Se você discorda de algo, escreva sua contraproposta na seção "📝 Registro de Discussão do Grupo", no final deste documento, indicando o item pelo código (ex.: RN10, RF05, seção 3).
* Itens marcados como "pendente" ao longo do texto ainda não têm decisão — são justamente os pontos que mais precisam da opinião de todo mundo.


________________


✅ Resumo Executivo — Decisões Já Tomadas
#
	Decisão
	Onde está detalhado
	1
	Nome do projeto: SGA — Sistema de Gestão Acadêmica
	—
	2
	Domínio: ensino superior (não escola particular K-12)
	Escopo, seção "Decisão de Domínio"
	3
	Quatro perfis de usuário: Aluno, Professor, Secretaria, Coordenação de Curso — sem perfil de Responsável
	Escopo §1, Regras de Negócio §1
	4
	Secretaria (administrativo) e Coordenação de Curso (pedagógico) são perfis distintos, com responsabilidades separadas
	Regras de Negócio RN04a/RN04b
	5
	Aluno se matricula por disciplina/turma a cada período — não existe turma fixa
	Escopo, Regras de Negócio §2-3
	6
	Calendário acadêmico fica no roadmap opcional
	Escopo §3, RF24
	7
	Controle de vagas por turma entra no MVP
	RN10, RN11, RF29
	8
	Transferência de aluno fica no roadmap opcional
	RN16, RF18
	9
	Situação de matrícula do aluno (ativo/trancado/transferido/formado/cancelado) entra no MVP
	RN14, RF17
	10
	Upload de documentos cadastrais fica no roadmap opcional
	RN29, RF19
	11
	Horário consolidado do aluno fica no roadmap opcional
	RF08a
	12
	Recuperação de senha fica no roadmap opcional
	RF03a
	13
	Matrícula só é permitida dentro do período aberto no calendário
	RN10a
	14
	Emissão de documentos oficiais (histórico, declaração, atestado) fica fora do MVP — complexidade grande demais para a Fase 1
	RN28
	15
	Cancelamento de matrícula por autoatendimento do aluno fica fora do MVP — só a Secretaria cancela na Fase 1
	RN13a
	⏳ Pontos Ainda Pendentes de Decisão (o grupo precisa se posicionar)
#
	Pendência
	Impacto
	P1
	Fórmula definida: média = (P1 + P2 + Trabalho) / 3; média mínima para aprovação = 6,0.
	RN17
	P2
	Média mínima: 6,0; aluno com média entre 4,0 e 5,9 realiza exame final como recuperação.
	RN19
	P3
	Frequência mínima exigida: 75%.
	RN23
	P4
	Pré-requisitos entre disciplinas não serão implementados no MVP; ficam reservados para a Fase 3.
	RN13
	P5
	Transferência simplificada: entrada exige instituição de origem e data; saída exige instituição de destino e data. Documentos comprobatórios ficam para fase posterior.
	RN16
	P6
	Comunicados podem ser institucionais, direcionados a um perfil (alunos ou professores) ou direcionados a um curso específico.
	RN26
	

________________


1. Escopo do Projeto
Disciplina: Laboratório de Engenharia de Software Professor Responsável: Rodrigo Salgado Integrantes: Andrey Kerges Nascimento, Alexandre Hesse, Max Iago Villafan, João Luiz, Vitor Augusto Versão: 0.3 — Domínio confirmado: Ensino Superior Data: Agosto/2026


________________


Decisão de Domínio (confirmada)
O grupo definiu que o sistema atenderá uma instituição de ensino superior, inspirado no SIGA utilizado pelas Fatecs — não mais uma escola particular de Ensino Fundamental/Médio, como no rascunho inicial. Essa decisão muda a estrutura central do sistema:


* O aluno se matricula em um Curso (ex.: "Análise e Desenvolvimento de Sistemas") e cursa disciplinas específicas por semestre, em vez de pertencer a uma turma fixa com grade curricular idêntica para todos.
* Turma, neste domínio, passa a significar a oferta de uma disciplina em um período letivo (ex.: "Programação Orientada a Objetos — 2026/1 — Turma A"), com professor, horário e sala próprios — e não mais um grupo fixo de alunos que cursa tudo junto.
* Não há perfil de Responsável/Pais, já que o público é adulto.


________________


1. Escopo (versão enxuta — formato solicitado pelo professor)
O projeto consiste no desenvolvimento de uma Secretária Inteligente para Instituições de Ensino Superior, um sistema web que centraliza a gestão administrativa e acadêmica da instituição, inspirado no SIGA utilizado pelas Fatecs. O sistema atende quatro perfis de usuário — Aluno, Professor, Secretaria e Coordenação de Curso — cada um com acesso restrito às funcionalidades correspondentes ao seu papel.


O Aluno se matricula em disciplinas (turmas) oferecidas em cada período letivo, consulta notas, faltas, frequência, materiais de aula, comunicados e o calendário acadêmico. O Professor lança notas e faltas das turmas em que leciona, e disponibiliza materiais didáticos. A Secretaria cuida da parte administrativa: cadastro de alunos e professores, matrícula em disciplinas, transferências de entrada/saída, upload de documentos cadastrais e controle da situação de matrícula de cada aluno. A Coordenação de Curso cuida da parte pedagógica: grade curricular do curso, abertura de turmas (com vagas e horário), alocação de professores e publicação de comunicados e eventos no calendário acadêmico. O sistema garante que cada usuário acesse apenas os dados pertinentes ao seu perfil (RBAC), assegurando organização, segurança e praticidade no dia a dia da instituição.


Ficam fora do escopo inicial (Fase 1) funcionalidades como módulo financeiro, emissão de documentos oficiais (histórico escolar, declaração de matrícula, atestados) — decisão tomada pelo grupo por ser uma frente grande e complexa demais para essa fase —, aplicativo mobile nativo e comunicação em tempo real entre usuários. Esses itens compõem o roadmap de Fase 2.


________________


2. Objetivos
2.1 Objetivo Geral
Desenvolver uma aplicação web responsiva que permita a gestão integrada de cursos, disciplinas, turmas, professores e alunos, com controle de notas, frequência, matrícula por disciplina e comunicação institucional, respeitando o perfil de acesso de cada usuário.
2.2 Objetivos Específicos
* Permitir que o aluno se matricule em disciplinas/turmas ofertadas e acompanhe seu desempenho acadêmico (notas, faltas, situação por disciplina).
* Permitir que o professor registre faltas e notas das turmas em que leciona, e compartilhe materiais didáticos.
* Permitir que a Secretaria administre o cadastro de alunos e professores, matrículas, transferências e documentação cadastral.
* Permitir que a Coordenação de Curso administre a grade curricular, abra turmas com controle de vagas, aloque professores e monte o calendário acadêmico.
* Centralizar comunicados institucionais (mural/avisos) visíveis conforme o perfil do usuário.
* Garantir segurança e isolamento de dados por perfil (RBAC), com atenção à LGPD no tratamento de dados de alunos e professores.


________________


3. Dentro do Escopo (Fase 1 / MVP)
Módulo Aluno


* Login e autenticação
* Matrícula em disciplinas/turmas ofertadas no período letivo (respeitando vagas disponíveis e o período de matrícula aberto no calendário)
* Visualização de notas e situação por disciplina
* Visualização de faltas e percentual de frequência por disciplina
* Visualização/download de materiais postados nas disciplinas em que está matriculado
* Visualização de comunicados e do calendário acadêmico
* Visualização do horário de aulas consolidado (grade semanal com todas as turmas em que está matriculado)


Módulo Professor


* Login e autenticação
* Visualização das turmas em que leciona
* Lançamento de faltas por aula/data
* Lançamento e edição de notas por avaliação/período
* Upload de materiais de aula (PDF, DOCX, PPTX, links)
* Visualização da lista de alunos matriculados na turma


Módulo Secretaria


* Login e autenticação
* CRUD de Alunos (cadastro, dados cadastrais)
* CRUD de Professores (cadastro)
* Matrícula e cancelamento de matrícula de alunos em turmas
* Controle da situação de matrícula do aluno (ativo, trancado, transferido, cancelado, formado)
* Transferência de aluno — registro de entrada (vindo de outra instituição) e saída (para outra instituição)
* Upload de documentos cadastrais do aluno (RG, CPF, histórico do ensino médio, comprovante de residência)


Módulo Coordenação de Curso


* Login e autenticação
* CRUD de Cursos
* CRUD de Disciplinas e grade curricular do curso
* Abertura de Turmas (oferta de disciplina por período, com professor, horário, sala e número de vagas)
* Alocação de professores às turmas
* Calendário acadêmico — cadastro de eventos institucionais (datas de prova, feriados, período de matrícula, reuniões)
* Publicação de comunicados/mural
* Relatórios básicos de desempenho e frequência por turma


Transversal


* Autenticação e autorização por papel (RBAC)
* Auditoria básica de alterações em notas e faltas (quem alterou e quando)
* Controle automático de vagas (a matrícula em uma turma não pode exceder o limite definido)
* Recuperação de senha ("esqueci minha senha", via e-mail)
* Matrícula restrita ao período aberto — RF05 só é permitido dentro da janela de matrícula cadastrada no calendário acadêmico (RF24)


________________


4. Fora do Escopo (Fase 1)
* Módulo financeiro (mensalidades, boletos, inadimplência)
* Emissão de documentos oficiais (histórico escolar, declaração de matrícula, atestados) — decisão confirmada do grupo: complexidade grande demais para a Fase 1. Fica fora do MVP e poderá integrar o roadmap opcional.
* Cancelamento de matrícula em disciplina pelo próprio aluno (autoatendimento) — no MVP, apenas a Secretaria cancela matrículas (ver 03-REQUISITOS.md, RF16). Autoatendimento traz regras extras (prazo limite, devolução de vaga) que poderão integrar o roadmap opcional.
* Matrícula 100% automática sem qualquer intervenção da secretaria (ex.: pré-requisitos complexos, dependência entre disciplinas)
* Aplicativo mobile nativo (o sistema será web responsivo)
* Comunicação em tempo real (chat) entre usuários
* Integração com sistemas externos (Receita Federal, MEC/e-MEC, etc.)


Itens podem compor um roadmap de Fase 2, a ser detalhado após a validação do MVP.


________________


5. Pontos em Aberto para Validação com o Grupo/Professor
1. Definir periodicidade de avaliação (por etapas configuráveis dentro do semestre) e a fórmula exata de cálculo de média.
2. Definir frequência mínima exigida (ex.: 75%) e regra de reprovação por falta.
3. Definir se existem pré-requisitos entre disciplinas (ex.: aluno só pode se matricular em "Estrutura de Dados II" se já cursou "Estrutura de Dados I") — impacta a regra de matrícula.
4. Definir o que caracteriza uma transferência válida (documentação mínima exigida).


Já decidido:


* ✅ Nome do projeto: SGA — Sistema de Gestão Acadêmica.
* ✅ Domínio: ensino superior (não escola K-12).
* ✅ Secretaria e Coordenação de Curso são perfis distintos no RBAC.
* ✅ Emissão de documentos oficiais fica fora da Fase 1.
* ✅ Controle de vagas e situação acadêmica permanecem no MVP. Calendário, transferência e documentos cadastrais ficam no roadmap opcional.
* ✅ Horário consolidado, recuperação de senha e matrícula vinculada ao calendário ficam no roadmap opcional.
* ✅ Cancelamento de matrícula por autoatendimento do aluno fica fora do MVP e poderá integrar o roadmap opcional.
* ✅ Não há perfil de Responsável/Pais.


________________


2. Regras de Negócio
Versão: 0.3 — Domínio: Ensino Superior Depende de: decisões pendentes listadas em 01-ESCOPO.md, seção 5


________________


1. Perfis e Hierarquia de Acesso
Perfil
	Como é criado
	Escopo de acesso
	Secretaria
	Cadastrado manualmente no sistema (seed inicial) ou por outro usuário de Secretaria/Coordenação
	Foco administrativo: cadastra alunos e professores; realiza matrícula/cancelamento de matrícula em turmas; controla situação de matrícula; registra transferências; faz upload de documentos cadastrais
	Coordenação de Curso
	Cadastrado manualmente no sistema (seed inicial) ou por outro usuário de Coordenação
	Foco pedagógico: gerencia cursos, disciplinas, grade curricular, abre turmas (com vagas e horário), aloca professores, monta o calendário acadêmico e publica comunicados
	Professor
	Cadastrado pela Secretaria
	Acesso restrito às turmas em que está alocado
	Aluno
	Cadastrado pela Secretaria
	Acesso restrito aos próprios dados (matrícula, notas, faltas, materiais, comunicados, calendário)
	

RN01 — Um usuário possui exatamente um perfil (Secretaria, Coordenação de Curso, Professor ou Aluno). RN02 — Um Professor só pode lançar ou editar notas/faltas em turmas às quais está formalmente alocado pela Coordenação. RN03 — Um Aluno só pode visualizar notas, faltas e materiais das turmas em que está efetivamente matriculado. RN04a — A Secretaria não realiza abertura de turmas, alocação de professores, grade curricular ou publicação de comunicados/calendário — essas ações são exclusivas da Coordenação de Curso. RN04b — A Coordenação de Curso não realiza cadastro de novos usuários (aluno, professor), matrícula/cancelamento de matrícula, transferência ou upload de documentos cadastrais — essas ações são exclusivas da Secretaria. RN04c — Todo usuário pode solicitar recuperação de senha ("esqueci minha senha") por meio de um link enviado ao e-mail cadastrado, com expiração do link em prazo curto (ex.: 30 minutos) — prazo exato a definir.


________________


2. Estrutura Acadêmica
RN05 — Todo Curso possui nome, descrição e uma grade curricular própria (conjunto de Disciplinas). Criação e manutenção de Cursos são responsabilidade da Coordenação de Curso. RN06 — Todo Aluno é vinculado a um Curso no momento da matrícula inicial, mas se matricula individualmente em Turmas (disciplinas) a cada período letivo — não existe turma fixa compartilhada por todos os alunos do curso. RN07 — Uma Turma é a oferta de uma Disciplina em um período letivo específico, com um Professor responsável, horário, sala e número máximo de vagas, definidos pela Coordenação de Curso. RN08 — Cada Turma é ministrada por um Professor responsável, alocado pela Coordenação de Curso. RN09 — O horário de uma Turma define dia da semana e horário de início/fim. Não pode haver dois horários conflitantes para o mesmo Professor no mesmo dia/hora.


________________


3. Matrícula em Disciplinas
RN10 — Um Aluno só pode se matricular em uma Turma se houver vagas disponíveis (COUNT de matrículas ativas < vagas_maximas). Ao atingir o limite, a matrícula deve ser bloqueada. RN10a — [ROADMAP] Quando o calendário for implementado, a matrícula por autoatendimento só será permitida dentro de uma janela ativa, definida por um evento do tipo matricula no calendário acadêmico (CalendarioEvento) vigente para o curso do aluno. Fora dessa janela, o sistema bloqueia novas matrículas. RN11 — Ao confirmar a matrícula de um aluno em uma turma, a quantidade de matrículas ativas deve ser recalculada. RN12 — A matrícula em uma Turma possui status próprio: ativa, trancada, concluída ou cancelada. RN13 — Não há pré-requisitos entre disciplinas no MVP. A regra fica reservada para a Fase 3. RN13a — No MVP, o cancelamento de matrícula em uma turma é realizado exclusivamente pela Secretaria (não há autoatendimento do aluno na Fase 1 — ver 01-ESCOPO.md, seção 4).


________________


4. Situação de Matrícula do Aluno
RN14 — Cada Aluno possui uma situação institucional: ativo, trancado, transferido, formado ou cancelado. Alterações de situação são responsabilidade da Secretaria. RN15 — Um Aluno com situação trancado ou cancelado não pode realizar novas matrículas em turmas até regularização. RN16 — Transferência de entrada (aluno vindo de outra instituição) exige registro pela Secretaria com, no mínimo, instituição de origem e data. Transferência de saída exige instituição de destino e data. Em ambos os casos a situação do Aluno é atualizada de acordo (transferido para saída).


________________


5. Avaliação
RN17 — O cálculo da média/situação do aluno por disciplina segue uma fórmula configurável definida pela Coordenação (ex.: média simples ou ponderada por peso de avaliação) — a fórmula exata precisa ser validada antes do desenvolvimento. RN18 — A média da disciplina deve ser recalculada automaticamente sempre que uma nota é lançada, editada ou removida. RN19 — O sistema deve indicar a situação do aluno por disciplina (ex.: aprovado, em recuperação, reprovado) conforme a média mínima definida — valor mínimo a confirmar. RN20 — Apenas o Professor responsável pela turma pode lançar ou editar notas.


________________


6. Frequência
RN21 — A frequência é registrada por aula/data e por aluno matriculado na turma (presente/ausente), lançada pelo Professor responsável. RN22 — O percentual de frequência do aluno por disciplina deve ser recalculado automaticamente a cada falta lançada, editada ou removida. RN23 — O sistema deve sinalizar risco de reprovação por falta quando a frequência do aluno cair abaixo do percentual mínimo exigido — percentual mínimo a confirmar (referência comum: 75%).


________________


7. Materiais Didáticos, Comunicados e Calendário
RN24 — Somente o Professor responsável pela turma pode publicar materiais de aula para aquela turma. RN25 — Materiais podem ser arquivos (PDF, DOCX, PPTX) ou links externos, com limite de tamanho por arquivo — limite a definir (referência: 20MB). RN26 — Comunicados/mural publicados pela Coordenação de Curso podem ser direcionados a todos os usuários, a um perfil específico ou a um Curso específico — regra definida: institucional, por perfil ou por curso. RN27 — Eventos do calendário acadêmico (datas de prova, feriados, período de matrícula, reuniões) são cadastrados pela Coordenação de Curso e visíveis a todos os usuários vinculados ao curso correspondente.


________________


8. Documentação (fora da Fase 1, com exceção do upload cadastral)
RN28 — A emissão de documentos oficiais (histórico escolar, declaração de matrícula, atestados) fica fora do MVP por decisão do grupo — a complexidade de gerar documentos formatados corretamente é grande demais para a Fase 1. Fica reservada para o roadmap de Fase 3. RN29 — [ROADMAP] O upload/armazenamento de documentos cadastrais do aluno poderá integrar a Fase 2 e será responsabilidade da Secretaria — é uma funcionalidade distinta e mais simples do que a emissão de documentos (RN28): aqui o sistema apenas recebe e guarda arquivos enviados, sem gerar nenhum documento novo.


________________


9. Auditoria
RN30 — Toda alteração em nota ou falta deve gerar um registro de auditoria contendo: usuário responsável, ação realizada, dado anterior, dado novo e data/hora. RN31 — Registros de auditoria não podem ser editados ou excluídos por nenhum perfil, incluindo Secretaria e Coordenação.


________________


10. Regras Pendentes de Validação
Estas regras não podem ser implementadas com segurança sem confirmação — ficam como bloqueio de desenvolvimento até resposta:


1. Fórmula exata de cálculo de média (RN17).
2. Média mínima para aprovação e existência (ou não) de recuperação (RN19).
3. Percentual mínimo de frequência (RN23).
4. Se há exigência de pré-requisitos entre disciplinas (RN13).
5. Documentação mínima exigida para transferência (RN16).
6. Regras de segmentação de comunicados (RN26).


Já decidido (não pendente):


* ✅ Nome do projeto: SGA — Sistema de Gestão Acadêmica.
* ✅ Domínio confirmado: ensino superior.
* ✅ Secretaria e Coordenação de Curso são perfis distintos, com responsabilidades separadas (RN04a, RN04b).
* ✅ Emissão e upload de documentos cadastrais ficam fora do MVP e integram apenas o roadmap opcional.
* ✅ Controle de vagas e situação acadêmica permanecem no MVP; transferência e calendário ficam no roadmap opcional.
* ✅ Janela de matrícula por calendário e recuperação de senha ficam no roadmap opcional.
* ✅ Cancelamento de matrícula por autoatendimento fica fora do MVP e poderá integrar o roadmap opcional.
* ✅ Não há perfil de Responsável/Pais.


________________


3. Matriz de Requisitos
Versão: 0.3 — Domínio: Ensino Superior


________________


1. Requisitos Funcionais (RF)
ID
	Funcionalidade
	Descrição
	Ator
	Prioridade
	RF01
	Autenticação
	Realizar login com e-mail e senha. Redirecionar para a dashboard do perfil correspondente após sucesso; exibir erro em caso de falha.
	Todos
	Alta
	RF02
	Logout
	Encerrar a sessão do usuário de forma segura.
	Todos
	Alta
	RF03
	Troca de senha obrigatória
	Exigir troca de senha no primeiro acesso do usuário.
	Todos
	Média
	RF03a
	Recuperação de senha
	Permitir que o usuário solicite redefinição de senha via link enviado por e-mail, com expiração do link.
	Todos
	Alta
	RF04
	RBAC
	Restringir o acesso às funcionalidades e dados conforme o perfil do usuário (Secretaria, Coordenação de Curso, Professor, Aluno).
	Sistema
	Alta
	RF05
	Matrícula em turma
	Permitir que o aluno se matricule em uma turma (disciplina ofertada), respeitando a disponibilidade de vagas e o período de matrícula aberto no calendário (RN10a).
	Aluno
	Alta
	RF06
	Visualização de notas/situação
	Exibir ao aluno as notas lançadas e a média/situação por disciplina em que está matriculado.
	Aluno
	Alta
	RF07
	Visualização de faltas
	Exibir ao aluno as faltas registradas e o percentual de frequência por disciplina.
	Aluno
	Alta
	RF08
	Visualização/download de materiais
	Permitir que o aluno visualize e baixe materiais postados nas turmas em que está matriculado.
	Aluno
	Alta
	RF08a
	Horário consolidado
	Exibir ao aluno a grade semanal de horários com todas as turmas em que está matriculado no período letivo.
	Aluno
	Alta
	RF09
	Visualização de comunicados e calendário
	Exibir ao usuário os comunicados/mural e os eventos do calendário acadêmico relevantes ao seu perfil/curso.
	Todos
	Média
	RF10
	Lançamento de faltas
	Permitir que o professor registre presença/falta por aula e data, para alunos matriculados na turma em que leciona.
	Professor
	Alta
	RF11
	Lançamento de notas
	Permitir que o professor lance e edite notas por avaliação/período, para a turma em que leciona.
	Professor
	Alta
	RF12
	Upload de materiais
	Permitir que o professor anexe materiais (arquivo ou link) a uma turma.
	Professor
	Alta
	RF13
	Listagem de alunos por turma
	Exibir ao professor a lista de alunos matriculados na turma em que leciona.
	Professor
	Média
	RF14
	CRUD de Professores
	Cadastrar, editar e inativar usuários com perfil Professor.
	Secretaria
	Alta
	RF15
	CRUD de Alunos
	Cadastrar, editar e inativar usuários com perfil Aluno, vinculando-os a um Curso.
	Secretaria
	Alta
	RF16
	Matrícula/cancelamento em turma (pela Secretaria)
	Matricular ou cancelar a matrícula de um aluno em uma turma, em nome do aluno quando necessário.
	Secretaria
	Alta
	RF17
	Situação de matrícula
	Alterar a situação institucional do aluno (ativo, trancado, transferido, formado, cancelado).
	Secretaria
	Alta
	RF18
	Transferência de aluno
	Registrar transferência de entrada (de outra instituição) ou de saída (para outra instituição), com dados de origem/destino e data.
	Secretaria
	Média
	RF19
	Upload de documentos cadastrais
	Anexar documentos do aluno (RG, CPF, histórico do ensino médio, comprovante de residência) ao seu cadastro.
	Secretaria
	Média
	RF20
	CRUD de Cursos
	Criar, editar e inativar cursos.
	Coordenação de Curso
	Alta
	RF21
	CRUD de Disciplinas e grade curricular
	Criar, editar e inativar disciplinas, vinculando-as à grade curricular de um curso.
	Coordenação de Curso
	Alta
	RF22
	Abertura de turmas
	Criar uma turma (oferta de disciplina), definindo período letivo, professor, horário, sala e número de vagas.
	Coordenação de Curso
	Alta
	RF23
	Alocação de professor
	Alocar um professor a uma turma.
	Coordenação de Curso
	Alta
	RF24
	Cadastro de calendário acadêmico
	Criar e editar eventos do calendário (provas, feriados, período de matrícula, reuniões), vinculados a um curso ou institucionais.
	Coordenação de Curso
	Média
	RF25
	Publicação de comunicados
	Criar e excluir comunicados no mural, com título, conteúdo e destinatário (todos, perfil ou curso específico).
	Coordenação de Curso
	Média
	RF26
	Relatórios de desempenho e frequência
	Gerar relatório de desempenho e frequência por turma.
	Coordenação de Curso
	Média
	RF27
	Cálculo automático de média
	Calcular automaticamente a média do aluno por disciplina, conforme regra de avaliação definida.
	Sistema
	Alta
	RF28
	Cálculo automático de frequência
	Calcular o percentual de frequência do aluno por disciplina e sinalizar risco de reprovação por falta.
	Sistema
	Alta
	RF29
	Controle automático de vagas
	Impedir matrícula em turma que já atingiu o número máximo de vagas.
	Sistema
	Alta
	RF30
	Auditoria de alterações
	Registrar log de alterações em notas e faltas (quem alterou, o quê e quando).
	Sistema
	Média
	RF31
	Validação de dados
	Bloquear submissão de formulários com campos obrigatórios vazios ou em formato inválido.
	Sistema
	Média
	

Nota: emissão de documentos (histórico, declaração, atestado) permanece fora do escopo da Fase 1 por decisão do grupo — não há RF correspondente nesta versão. Ver 02-REGRAS-DE-NEGOCIO.md, seção 8 (RN28).


Nota: cancelamento de matrícula em disciplina por autoatendimento do aluno também fica fora da Fase 1 (RN13a) — no MVP, apenas RF16 (pela Secretaria) cobre essa ação.


________________


2. Requisitos Não Funcionais (RNF)
ID
	Categoria
	Descrição
	RNF01
	Interface
	Aplicação responsiva, com experiência adequada em desktop, tablet e smartphone, acessada via navegador.
	RNF02
	Segurança de sessão
	Autenticação via JWT com expiração e renovação (refresh token).
	RNF03
	Segurança de senhas
	Senhas armazenadas exclusivamente como hash (bcrypt/argon2 ou equivalente da stack escolhida); nunca em texto puro ou em log.
	RNF04
	Desempenho
	Tempo de resposta das operações comuns da API abaixo de 500ms (p95), em ambiente de desenvolvimento/homologação.
	RNF05
	Auditoria
	Logs de auditoria retidos por, no mínimo, 12 meses.
	RNF06
	Ambientes
	Separação entre ambiente de desenvolvimento, homologação e produção.
	RNF07
	LGPD
	Conformidade com a LGPD no tratamento de dados de alunos e professores, incluindo documentos cadastrais sensíveis (RG, CPF).
	RNF08
	Upload de arquivos
	Upload de materiais e documentos cadastrais limitado por tipo e tamanho de arquivo, com validação real do tipo do arquivo (não apenas pela extensão).
	RNF09
	Compatibilidade
	Funcionamento correto nos navegadores Chrome, Firefox e Edge em suas versões atuais.
	RNF10
	Backup
	Backup periódico automatizado do banco de dados.
	RNF11
	Prevenção de vulnerabilidades comuns
	Proteção contra SQL Injection e XSS, preferencialmente via mecanismos nativos do framework escolhido.
	RNF12
	Credenciais
	Dados sensíveis (strings de conexão, segredos JWT) armazenados em variáveis de ambiente, nunca versionados no repositório.
	

________________


3. Fora de Escopo (reforço — ver 01-ESCOPO.md para lista completa)
* Módulo financeiro
* Emissão de documentos oficiais (histórico escolar, declaração, atestados)
* Aplicativo mobile nativo
* Chat/comunicação em tempo real
* Integrações externas (MEC, Receita Federal, etc.)


________________


4. Modelagem de Dados
Versão: 0.3 — Domínio: Ensino Superior Observação: tipos SQL são ilustrativos; serão ajustados conforme a stack tecnológica escolhida pelo grupo.


________________


1. Entidades
1.1 Usuario
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	Identificador único
	nome
	VARCHAR(150)
	Sim
	Nome completo
	email
	VARCHAR(150) UNIQUE
	Sim
	Login do usuário
	senha_hash
	VARCHAR(255)
	Sim
	Hash da senha, nunca texto puro
	perfil
	ENUM('secretaria','coordenacao','professor','aluno')
	Sim
	Define o RBAC
	ativo
	BOOLEAN
	Sim
	Padrão: true
	criado_em
	DATETIME
	Sim
	Automático
	1.1a TokenRecuperacaoSenha
(suporte a RF03a — recuperação de senha) | Atributo | Tipo | Obrigatório | Observação | |---|---|:---:|---| | id | INT (PK, auto) | Sim | — | | usuario_id | INT (FK → usuario.id) | Sim | — | | token | VARCHAR(255) UNIQUE | Sim | Token enviado por e-mail | | expira_em | DATETIME | Sim | Prazo curto de validade (ex.: 30 min) | | usado | BOOLEAN | Sim | Padrão: false | | criado_em | DATETIME | Sim | Automático |
1.2 Aluno (1:1 com Usuario)
(gerido pela Secretaria) | Atributo | Tipo | Obrigatório | Observação | |---|---|:---:|---| | id | INT (PK, auto) | Sim | — | | usuario_id | INT (FK → usuario.id) | Sim | — | | matricula | VARCHAR(20) UNIQUE | Sim | Número de matrícula (RA) | | curso_id | INT (FK → curso.id) | Sim | Curso ao qual o aluno está vinculado | | situacao | ENUM('ativo','trancado','transferido','formado','cancelado') | Sim | RN14 — controlado pela Secretaria | | data_ingresso | DATE | Sim | — |
1.3 Professor (1:1 com Usuario)
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	usuario_id
	INT (FK → usuario.id)
	Sim
	—
	registro_funcional
	VARCHAR(30)
	Sim
	—
	titulacao
	VARCHAR(100)
	Não
	Ex.: Mestre, Doutor
	1.4 DocumentoAluno
(gerido pela Secretaria — RN29) | Atributo | Tipo | Obrigatório | Observação | |---|---|:---:|---| | id | INT (PK, auto) | Sim | — | | aluno_id | INT (FK → aluno.id) | Sim | — | | tipo | ENUM('RG','CPF','historico_ensino_medio','comprovante_residencia','outro') | Sim | — | | arquivo_path | VARCHAR(300) | Sim | Caminho do arquivo armazenado | | enviado_em | DATETIME | Sim | Automático |
1.5 TransferenciaAluno
(gerido pela Secretaria — RN16) | Atributo | Tipo | Obrigatório | Observação | |---|---|:---:|---| | id | INT (PK, auto) | Sim | — | | aluno_id | INT (FK → aluno.id) | Sim | — | | tipo | ENUM('entrada','saida') | Sim | — | | instituicao | VARCHAR(150) | Sim | Instituição de origem (entrada) ou destino (saída) | | data | DATE | Sim | — | | observacao | TEXT | Não | — |


________________




(Curso, Disciplina, GradeCurricular, Turma, Horario, CalendarioEvento e Comunicado são geridos pelo perfil Coordenação de Curso.)
1.6 Curso
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	nome
	VARCHAR(150)
	Sim
	Ex.: "Análise e Desenvolvimento de Sistemas"
	descricao
	TEXT
	Não
	—
	ativo
	BOOLEAN
	Sim
	Padrão: true
	1.7 Disciplina
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	nome
	VARCHAR(100)
	Sim
	Ex.: "Programação Orientada a Objetos"
	carga_horaria
	INT
	Não
	Horas/aula previstas
	ativa
	BOOLEAN
	Sim
	Padrão: true
	1.8 GradeCurricular (tabela associativa Curso × Disciplina)
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	curso_id
	INT (FK → curso.id)
	Sim
	—
	disciplina_id
	INT (FK → disciplina.id)
	Sim
	—
	semestre_sugerido
	INT
	Não
	Semestre recomendado da grade
	pre_requisito_disciplina_id
	INT (FK → disciplina.id)
	Não
	RN13 — pendente de confirmação
	1.9 Turma
(oferta de uma disciplina em um período — RN07) | Atributo | Tipo | Obrigatório | Observação | |---|---|:---:|---| | id | INT (PK, auto) | Sim | — | | disciplina_id | INT (FK → disciplina.id) | Sim | — | | professor_id | INT (FK → professor.id) | Sim | — | | periodo_letivo | VARCHAR(9) | Sim | Ex.: "2026/1" | | sala | VARCHAR(30) | Não | — | | vagas_maximas | INT | Sim | RN10, RN11 | | vagas_ocupadas | INT | Sim | Atualizado automaticamente a cada matrícula/cancelamento |
1.10 Horario
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	turma_id
	INT (FK → turma.id)
	Sim
	—
	dia_semana
	ENUM('SEG','TER','QUA','QUI','SEX','SAB')
	Sim
	—
	hora_inicio
	TIME
	Sim
	—
	hora_fim
	TIME
	Sim
	—
	1.11 Matricula
(vínculo Aluno × Turma — RF05, RF16) | Atributo | Tipo | Obrigatório | Observação | |---|---|:---:|---| | id | INT (PK, auto) | Sim | — | | aluno_id | INT (FK → aluno.id) | Sim | — | | turma_id | INT (FK → turma.id) | Sim | — | | status | ENUM('ativa','trancada','concluida','cancelada') | Sim | RN12 | | matriculado_em | DATETIME | Sim | Automático |
1.12 Avaliacao
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	turma_id
	INT (FK → turma.id)
	Sim
	—
	nome
	VARCHAR(50)
	Sim
	Ex.: "Prova 1"
	peso
	DECIMAL(4,2)
	Não
	Depende da fórmula de média (RN17, pendente)
	periodo
	VARCHAR(20)
	Sim
	Ex.: "Etapa 1"
	data
	DATE
	Não
	—
	1.13 Nota
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	avaliacao_id
	INT (FK → avaliacao.id)
	Sim
	—
	aluno_id
	INT (FK → aluno.id)
	Sim
	—
	valor
	DECIMAL(4,2)
	Sim
	—
	1.14 Falta
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	turma_id
	INT (FK → turma.id)
	Sim
	—
	aluno_id
	INT (FK → aluno.id)
	Sim
	—
	data_aula
	DATE
	Sim
	—
	presente
	BOOLEAN
	Sim
	—
	1.15 Material
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	turma_id
	INT (FK → turma.id)
	Sim
	—
	titulo
	VARCHAR(150)
	Sim
	—
	tipo
	ENUM('arquivo','link')
	Sim
	—
	url_ou_path
	VARCHAR(300)
	Sim
	—
	postado_em
	DATETIME
	Sim
	Automático
	1.16 Comunicado
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	titulo
	VARCHAR(100)
	Sim
	—
	conteudo
	VARCHAR(1000)
	Sim
	—
	destinatario
	ENUM('todos','professores','alunos','curso_especifico')
	Sim
	RN26 — regra a validar
	curso_id
	INT (FK → curso.id)
	Não
	Preenchido se destinatario = 'curso_especifico'
	autor_id
	INT (FK → usuario.id)
	Sim
	Usuário da Coordenação que publicou
	publicado_em
	DATETIME
	Sim
	Automático
	1.17 CalendarioEvento
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	titulo
	VARCHAR(150)
	Sim
	Ex.: "Prova Final — POO"
	tipo
	ENUM('prova','feriado','matricula','reuniao','evento')
	Sim
	—
	data_inicio
	DATE
	Sim
	—
	data_fim
	DATE
	Não
	Para eventos de múltiplos dias
	curso_id
	INT (FK → curso.id)
	Não
	Nulo = evento institucional (todos os cursos)
	descricao
	TEXT
	Não
	—
	1.18 LogAuditoria
Atributo
	Tipo
	Obrigatório
	Observação
	id
	INT (PK, auto)
	Sim
	—
	usuario_id
	INT (FK → usuario.id)
	Sim
	Quem realizou a ação
	acao
	VARCHAR(50)
	Sim
	Ex.: "criar", "editar", "excluir"
	entidade
	VARCHAR(50)
	Sim
	Ex.: "Nota", "Falta"
	entidade_id
	INT
	Sim
	—
	dado_anterior
	TEXT
	Não
	—
	dado_novo
	TEXT
	Não
	—
	criado_em
	DATETIME
	Sim
	Automático
	

________________


2. Relacionamentos Principais
* Um Curso possui uma grade curricular de várias Disciplinas (via GradeCurricular).
* Um Aluno está vinculado a um Curso, mas se matricula individualmente em Turmas (via Matricula) — não existe turma fixa compartilhada.
* Uma Turma é a oferta de uma Disciplina em um Período Letivo, com um Professor responsável, Horário(s) e um limite de vagas.
* Cada Turma tem várias Avaliações, e cada avaliação gera Notas por aluno matriculado.
* Cada Turma tem registros de Falta por aluno matriculado e por data de aula.
* Um Aluno pode ter vários DocumentoAluno e, eventualmente, registros de TransferenciaAluno.
* CalendarioEvento e Comunicado podem ser institucionais (sem curso vinculado) ou específicos de um Curso.


________________


3. Pontos em Aberto que Afetam a Modelagem
1. Pré-requisitos entre disciplinas (GradeCurricular.pre_requisito_disciplina_id) — depende de RN13, ainda pendente.
2. O atributo peso em Avaliacao só faz sentido se a fórmula de média for ponderada — depende de RN17 (regra de negócio pendente).
3. Documentação mínima exigida em TransferenciaAluno (quais documentos anexar) — depende de RN16.


________________


5. Rastreabilidade
Versão: 0.3 — Domínio: Ensino Superior Como usar: cada RF deve remeter a um Caso de Uso (CU) documentado futuramente em detalhe (ator, pré-condição, fluxo principal, pós-condição). Esta tabela é o mapa inicial; os CUs completos podem ser desenvolvidos em um documento separado (06-CASOS-DE-USO.md) quando o grupo avançar para essa etapa.


RF
	Funcionalidade
	Caso de Uso Relacionado
	RF01
	Autenticação
	CU — Usuário realiza login
	RF02
	Logout
	CU — Usuário encerra sessão
	RF03
	Troca de senha obrigatória
	CU — Usuário troca senha no primeiro acesso
	RF03a
	Recuperação de senha
	CU — Usuário solicita redefinição de senha
	RF04
	RBAC
	Transversal (protege todos os CUs)
	RF05
	Matrícula em turma
	CU01 — Aluno se matricula em disciplina/turma
	RF06
	Visualização de notas/situação
	CU02 — Aluno consulta notas e situação
	RF07
	Visualização de faltas
	CU03 — Aluno consulta frequência
	RF08
	Visualização/download de materiais
	CU04 — Aluno acessa materiais de aula
	RF08a
	Horário consolidado
	CU04a — Aluno consulta grade de horários
	RF09
	Visualização de comunicados e calendário
	CU05 — Usuário consulta mural e calendário acadêmico
	RF10
	Lançamento de faltas
	CU06 — Professor lança frequência da aula
	RF11
	Lançamento de notas
	CU07 — Professor lança notas de avaliação
	RF12
	Upload de materiais
	CU08 — Professor publica material de aula
	RF13
	Listagem de alunos por turma
	CU09 — Professor consulta alunos da turma
	RF14
	CRUD de Professores
	CU10 — Secretaria cadastra professor
	RF15
	CRUD de Alunos
	CU11 — Secretaria cadastra aluno
	RF16
	Matrícula/cancelamento em turma (pela Secretaria)
	CU12 — Secretaria matricula/cancela matrícula de aluno
	RF17
	Situação de matrícula
	CU13 — Secretaria altera situação do aluno
	RF18
	Transferência de aluno
	CU14 — Secretaria registra transferência de entrada/saída
	RF19
	Upload de documentos cadastrais
	CU15 — Secretaria anexa documento ao cadastro do aluno
	RF20
	CRUD de Cursos
	CU16 — Coordenação gerencia cursos
	RF21
	CRUD de Disciplinas e grade curricular
	CU17 — Coordenação gerencia disciplinas e grade curricular
	RF22
	Abertura de turmas
	CU18 — Coordenação abre turma (oferta de disciplina)
	RF23
	Alocação de professor
	CU19 — Coordenação aloca professor à turma
	RF24
	Cadastro de calendário acadêmico
	CU20 — Coordenação cadastra evento no calendário
	RF25
	Publicação de comunicados
	CU21 — Coordenação publica comunicado
	RF26
	Relatórios de desempenho e frequência
	CU22 — Coordenação gera relatório de turma
	RF27
	Cálculo automático de média
	CU02 (pós-condição)
	RF28
	Cálculo automático de frequência
	CU03 (pós-condição)
	RF29
	Controle automático de vagas
	CU01 (pré-condição)
	RF30
	Auditoria de alterações
	Transversal (RF10, RF11)
	RF31
	Validação de dados
	Transversal (todos os formulários)
	

________________


📝 Registro de Discussão do Grupo
Cada integrante que discordar de algum ponto deve preencher uma linha abaixo, citando o código do item (ex.: RN10, RF05, "Escopo §4") e sua contraproposta. Se todos concordarem com tudo, essa seção fica em branco e o documento é considerado aprovado como está.


Integrante
	Item (código)
	Discordância / Contraproposta
	Decisão final do grupo
	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

________________


Aprovação
* Andrey Kerges Nascimento
* Alexandre Hesse
* Max Iago Villafan
* João Luiz
* Vitor Augusto


(marcar quando concordar com a versão final, após eventuais ajustes desta seção)




━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ATUALIZAÇÃO 0.4 — DECISÕES CONSOLIDADAS APÓS REVISÃO DO GRUPO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


1. Fases do produto


O desenvolvimento será organizado em três fases:


Fase 1 — MVP acadêmico essencial: autenticação, perfis e permissões, cadastro de alunos e professores, cursos, disciplinas, turmas, matrícula, lançamento e consulta de notas, lançamento e consulta de frequência e cálculo do desempenho acadêmico.


Fase 2 — Roadmap opcional de operação acadêmica: comunicados, calendário acadêmico, materiais didáticos, horário consolidado, controle de situação acadêmica, transferência simplificada, upload de documentos cadastrais, relatórios básicos e recuperação de senha, caso seja priorizada pelo grupo.


Fase 3 — Roadmap opcional de evolução do produto: pré-requisitos entre disciplinas, cancelamento de matrícula pelo aluno, emissão de documentos oficiais, notificações, módulo financeiro, aplicativo mobile e integrações externas.


2. Regras acadêmicas definidas


A média parcial será calculada por: (P1 + P2 + Trabalho) / 3. A média mínima para aprovação direta será 6,0. O aluno com média parcial igual ou superior a 4,0 e inferior a 6,0 poderá realizar exame final de recuperação. O aluno com média parcial inferior a 4,0 será reprovado diretamente. Recomenda-se que a média final após o exame seja calculada por (média parcial + nota do exame) / 2, com aprovação quando o resultado for igual ou superior a 6,0. A frequência mínima será de 75%.


3. Decisões de escopo


Pré-requisitos entre disciplinas não serão implementados no MVP. Eles ficam reservados para a Fase 3 porque exigem histórico acadêmico, regras de aprovação e validações adicionais.


Os comunicados terão três possibilidades de público: institucional, para todos; por perfil, destinado a alunos ou professores; ou por curso específico.


Se o grupo optar por desenvolver o roadmap, a transferência poderá ser implementada de forma simplificada: transferência de entrada registra instituição de origem e data; transferência de saída registra instituição de destino e data. A exigência e o armazenamento de documentos comprobatórios ficam para fase posterior.


4. Documentos previstos para o projeto


Documentos essenciais: 00 Documento Consolidado; 01 Escopo; 02 Regras de Negócio; 03 Requisitos Funcionais e Não Funcionais; 04 Modelagem de Dados e Diagrama ER; 05 Matriz de Rastreabilidade; 06 Casos de Uso; 07 Arquitetura do Sistema; 08 Protótipos/Wireframes; 09 Plano e Casos de Teste; 10 Matriz de Permissões/RBAC; 11 Cronograma e Plano de Desenvolvimento.


Documentos recomendados para a entrega final: 12 Manual de Instalação e Configuração; 13 Manual do Usuário; 14 Dicionário de Dados; 15 Plano de Implantação; 16 Registro de Riscos, Premissas e Decisões; 17 Relatório Final de Validação e Evidências de Teste.


A numeração poderá ser ajustada pelo grupo, mas cada documento deve possuir versão, data, responsáveis e relação com os requisitos correspondentes.




DECISÃO FINAL DE ESCOPO — MVP E ROADMAP
Esta decisão substitui qualquer classificação anterior conflitante sobre as Fases 1, 2 e 3.


A Fase 1 é o único escopo comprometido para entrega acadêmica. Ela constitui o MVP do SGA e inclui: autenticação; perfis Aluno, Professor, Secretaria e Coordenação; cadastro e inativação de alunos e professores; cursos e disciplinas; criação de turmas; alocação de professor; matrícula realizada pela Secretaria; controle de vagas; lançamento de P1, P2 e Trabalho; registro de frequência; cálculo de média; exame final; aprovação e reprovação; consulta de notas e frequência pelo aluno; permissões por perfil; e auditoria básica das alterações em notas e frequência.


A Fase 2 é somente um roadmap opcional de expansão acadêmica. Poderá incluir matrícula pelo próprio aluno, conflitos avançados de horário e sala, calendário acadêmico, comunicados, materiais didáticos, recuperação de senha por e-mail, transferência simplificada, documentos cadastrais, relatórios e notificações.


A Fase 3 é somente um roadmap opcional de evolução institucional. Poderá incluir pré-requisitos, equivalência e aproveitamento de disciplinas, emissão de documentos oficiais, módulo financeiro, aplicativo mobile, integrações externas, armazenamento em nuvem, dashboards avançados, API pública e recursos de inteligência artificial.


As Fases 2 e 3 não compõem o compromisso de entrega atual. Sua implementação dependerá exclusivamente do interesse, da disponibilidade e de decisões futuras do grupo. Itens de roadmap podem permanecer documentados para demonstrar visão de evolução, mas não devem ser tratados como requisitos obrigatórios do MVP.
