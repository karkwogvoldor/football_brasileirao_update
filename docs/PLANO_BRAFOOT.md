# BRAFOOT — visão de produto e plano de migração

> Documento de intenção e roteiro técnico. Estado de referência: branch `BRAFOOT`, 10/11/2026. As fases abaixo são propostas; nenhuma funcionalidade do jogo está implementada por este documento.

## 1. Visão

Evoluir o campinho virtual do Brasileirão 2026 para um microjogo de gestão de futebol, inspirado na simplicidade de Brasfoot e em atributos de jogadores de jogos como PES e Football Manager, mas com identidade, interface, regras e fórmulas próprias. O usuário escolhe um clube, monta o time, define uma estratégia, simula partidas e acompanha uma temporada persistente. O jogo deve funcionar mesmo quando a fonte externa de dados estiver indisponível.

O Brasileirão será a primeira competição jogável. A estrutura já deve permitir acrescentar outras temporadas, campeonatos e ligas sem duplicar a engine nem atrelar IDs internos a um fornecedor.

### Princípios

- Jogabilidade acessível: uma partida deve ser compreensível em poucos minutos, com decisões táticas que tenham efeitos visíveis.
- Simulação explicável: eventos e resultado vêm de regras versionadas, probabilidades calibráveis e uma semente reproduzível; não de números arbitrários escondidos na interface.
- Dados reais e dados de jogo são coisas diferentes. Elenco, posição e calendário podem vir de fonte autorizada; atributos, potencial, condição e desempenho simulado são cálculos ou escolhas editoriais do BRAFOOT.
- Mudanças no futebol real não reescrevem partidas, saves ou temporadas em andamento. Cada save usa uma versão congelada dos elencos e parâmetros.
- O projeto cresce por fatias funcionais, preservando a aplicação atual até a nova experiência atingir critérios de substituição.

## 2. Ponto de partida constatado no repositório

- FastAPI, SQLAlchemy/PostgreSQL, Pydantic, HTML/CSS/JavaScript; imagens em Cloudinary e deploy descrito no Railway.
- `Team` guarda nome, formação, escudo e foto do destaque; `Jogador` guarda nome, número, posição e vínculo opcional ao time. Não há atributos de jogo, temporada, partida ou save.
- `static/clube.js` guarda no cliente os IDs dos titulares, as formações e as descrições dos destaques. As substituições por arrastar e soltar alteram apenas o estado da página.
- Os seeds por clube fazem POST para uma URL de produção fixa. A API atual expõe POST/PATCH/DELETE sem autenticação. A operação de importação precisará de um caminho administrativo separado e seguro antes de automatizar atualizações.
- Não foi encontrada suíte de testes automatizados nem sistema de migrações de banco. `create_all` na inicialização cria tabelas ausentes, mas não migra tabelas existentes.

## 3. Produto-alvo

### Primeira versão jogável (MVP)

1. Escolher um clube e iniciar um save de uma temporada do Brasileirão.
2. Ver elenco, onze inicial, reservas, condição física e atributos de jogo; trocar jogadores e escolher formação, estilo e intensidade.
3. Simular uma rodada com narração textual curta, placar, eventos principais, estatísticas simples e influência observável das escolhas.
4. Registrar resultados, tabela, calendário e evolução da temporada. Salvar e retomar o progresso.
5. Importar ou atualizar elencos por uma fonte aprovada, com revisão das mudanças antes da publicação. A versão inicial deve aceitar também importação manual/CSV para não bloquear o jogo por dependência externa.

Ficam fora do MVP: mercado de transferências completo, contratos/finanças, base de jovens, múltiplas divisões simultâneas, partidas ao vivo e multiplayer. Esses recursos entram após o ciclo completo de uma temporada funcionar bem.

### Jornada posterior

Adicionar lesões e suspensões com regras transparentes, treino e evolução, transferências, gestão financeira simplificada, copas, acesso/rebaixamento e competições adicionais. Cada incremento depende de regras próprias, testes e dados adequados; não é pressuposto do primeiro lançamento.

## 4. Modelo de dados proposto

| Domínio | Entidades e responsabilidade |
| --- | --- |
| Catálogo | `Competition`, `Season`, `Club`, `Player`, `ClubMembership` (vínculo com início/fim), `Fixture` e `RealDataSnapshot`. IDs internos imutáveis; IDs externos ficam numa tabela de mapeamento por fornecedor. |
| Jogo | `PlayerAttributes` (versão, origem e confiança), `PlayerCondition` (energia, forma, disponibilidade), `Tactic`, `Lineup` e `LineupSlot`. Atributos base são distintos da condição transitória. |
| Simulação | `SimulationRuleset`, `GameSave`, `GameSeason`, `GameMatch`, `MatchEvent` e `Standing`. Cada partida registra versão das regras, semente, entradas e resultado. |
| Ingestão | `DataSource`, `ImportRun`, `SourceRecord`, `ImportDiff` e `ImportApproval`, com datas, proveniência, erros e possibilidade de rejeitar um lote. |

`Player` representa a pessoa; `ClubMembership` representa sua passagem pelo clube, sem sobrescrever história após transferência. `RealDataSnapshot` preserva a fotografia publicada. Um `GameSave` referencia um snapshot e uma versão de regras; novas importações criam novas versões e só entram em saves novos ou mediante ação explícita, com regras de compatibilidade documentadas.

Na migração, criar mapeamentos dos atuais IDs de `times` e `jogadores` para as novas chaves. Não presumir que os números gerados pelos seeds sejam estáveis: hoje o front-end depende deles. Exigir conferência de duplicatas, nomes, posições e vínculos antes de trocar as leituras.

## 5. Atributos e condição dos jogadores

Propor uma escala interna de 1 a 20 para atributos como velocidade, aceleração, resistência, força, passe, controle, finalização, desarme, posicionamento, tomada de decisão e habilidades específicas de goleiro. A posição define pesos para uma avaliação derivada, mas a avaliação geral não deve apagar o perfil: um atacante rápido e um centroavante forte podem ter o mesmo geral e jogar de forma diferente.

Separar explicitamente:

- **Atributo base**: capacidade estimada para o jogo, versionada e com origem (`editorial`, `modelo`, `fonte licenciada`).
- **Condição atual**: energia, forma recente, moral e disponibilidade dentro do save; varia após partidas e decisões.
- **Efetividade na partida**: resultado temporário de atributo base, condição, adequação à posição, tática, adversário e aleatoriedade controlada.

Dados públicos de elenco não medem de modo confiável força, resistência ou potencial individual. Não transformar altura, idade, nota de partida ou ausência de estatística em diagnóstico físico. Para o MVP, usar perfis iniciais editoriais ou regras conservadoras por posição, indicar valores estimados na interface e permitir correção manual. Só derivar atributos de métricas externas quando houver direito de uso, cobertura suficiente, método documentado e avaliação de viés/erro. Testar limites e calibrar distribuições para evitar que um único atributo domine a simulação.

## 6. Engine própria de partida

Criar um pacote Python independente de FastAPI, banco, scraper e interface. Entrada: dois elencos válidos, táticas, condição, contexto da partida, versão das regras e semente. Saída: placar, eventos ordenados, estatísticas, desgaste e alterações de estado. O mesmo input com a mesma semente deve produzir a mesma saída.

Fluxo inicial proposto: validar escalações → calcular forças por setor e encaixe tático → gerar posses/oportunidades em períodos discretos → resolver criação, defesa e finalização → registrar gols e eventos → aplicar fadiga/substituições → consolidar estatísticas. Usar probabilidades limitadas e calibradas, com mandante e aleatoriedade moderados; registrar por que uma chance ocorreu. A experiência pode ser textual e em tempo acelerado, sem exigir animação complexa.

Invariantes: onze titulares distintos por equipe, goleiro presente, jogador elegível e pertencente ao elenco do save, eventos em ordem, placar igual à soma dos gols e tabela consistente com os resultados. Executar baterias de simulações para inspecionar distribuição de gols, empates, efeito do mando, equilíbrio entre clubes e impacto real das táticas. Ajustar parâmetros com dados e testes de regressão antes de ampliar a complexidade.

## 7. Atualização de times e escalações

Construir uma interface de **provedor de dados** (`fetch` → `normalize` → `validate` → `diff` → `approve` → `publish`). Ela recebe competição e temporada e entrega clubes, elenco, posições, vínculos, escalações observadas e, se licenciados, partidas. Cada registro mantém fonte, identificador externo, instante de coleta e grau de confiança. Campos ausentes não apagam automaticamente valores conhecidos.

Sofascore é uma referência possível de cobertura, não uma dependência aprovada para scraping. Seus [Termos e Condições](https://www.sofascore.com/de/terms-and-conditions) restringem raspagem e reutilização sem consentimento, ressalvadas permissões legais. A [comunicação oficial sobre a API para parceiros](https://www.sofascore.com/news/sofascore-player-id-explained-every-players-unique-number) menciona acesso programático a IDs e informações básicas de jogadores; isso **não comprova** autorização nem cobertura de elencos, escalações e estatísticas para este projeto. Antes de desenvolver um conector, verificar por escrito licença, escopo, custo, limites, retenção, atribuição, imagens e uso em jogo. Avaliar provedores alternativos sob os mesmos critérios.

Para o protótipo, manter importador manual/CSV com dados próprios ou autorizados. Depois, um adaptador de API/licença aprovada pode rodar em tarefa agendada com limites, retries, cache, alertas e revisão humana de transferências, homônimos e mudanças grandes. Não acessar endpoints não documentados nem contornar bloqueios. Mostrar ao usuário a data da última atualização; em falha, preservar o último snapshot válido.

Elenco atual, escalação provável e onze confirmado são conceitos diferentes. Registrar tipo e data da escalação. Uma escalação confirmada para uma partida real não deve substituir automaticamente a escalação padrão de todos os jogos simulados.

## 8. Arquitetura de evolução

Manter FastAPI e PostgreSQL inicialmente. Separar os módulos `catalog`, `ingestion`, `ratings`, `simulation` e `gameplay`, com fronteiras claras: adaptadores externos escrevem snapshots revisados; a engine recebe objetos de domínio e devolve resultado; serviços de aplicação persistem saves; a API expõe operações; o front-end apresenta estado vindo do servidor. Introduzir migrações versionadas de banco (por exemplo, Alembic), em vez de confiar em `create_all` para alterações estruturais.

Os endpoints antigos podem continuar servindo a galeria durante a transição. Novos endpoints versionados atendem competições, temporadas, clubes, elencos, saves, escalações, partidas e tabela. Restringir escrita administrativa e importações; salvar jogos exige identificação do dono do save ou, num protótipo local, um mecanismo de posse explícito. Definir limites de requisição e validação de dados importados antes de expor essas rotas publicamente.

Ao trocar o front-end, mover titulares, craque e coordenadas persistentes para dados do servidor ou configuração de formação versionada. O campinho existente pode ser reutilizado para montar a equipe. Seleção e substituições passam a salvar uma `Lineup` do save; a página deve diferenciar alterações ainda não confirmadas de uma escalação persistida.

## 9. Fases e critérios de conclusão

| Fase | Entrega | Critério de aceite |
| --- | --- | --- |
| 0. Base segura | Inventário do banco/deploy, backup restaurável, amostra de dados, testes mínimos da galeria/API e escolha de migrações. | Baseline reproduzível; restauração ensaiada em ambiente separado; nenhuma mudança na produção por seeds de teste. |
| 1. Catálogo versionado | Competições/temporadas, clubes, jogadores, vínculos, mapeamento dos IDs atuais; primeira migração de banco. | Os 20 clubes e seus jogadores aparecem na galeria via novo catálogo sem perda de registros; importação antiga preservada para rollback. |
| 2. Dados e atributos | Snapshot inicial, perfis de atributos transparentes e importador manual com validação/diff/revisão. | Origem e data visíveis; duplicatas e alterações inesperadas são sinalizadas; reexecutar importação não duplica entidades. |
| 3. Núcleo da engine | Simulação determinística de uma partida, eventos e desgaste. | Mesma entrada/semente gera mesmo resultado; invariantes e métricas de equilíbrio passam em testes. |
| 4. Vertical jogável | Escolher clube, salvar escalação/tática, jogar uma partida e rever resultado. | Um usuário completa esse fluxo e o retoma após recarregar a página. |
| 5. Temporada MVP | Calendário, rodada, classificação, persistência e encerramento do Brasileirão. | Uma temporada inteira pode ser concluída e retomada; tabela e histórico batem com os resultados. |
| 6. Fonte autorizada | Prova de conceito de um provedor aprovado, agendamento, monitoramento e publicação revisada. | Termos/licença conferidos; falha mantém snapshot anterior; atualização não altera saves em curso. |
| 7. Expansão | Segunda competição/temporada pelo mesmo modelo e regras configuráveis. | Inclusão sem copiar a engine nem depender de IDs ou nomes fixos do Brasileirão. |

As fases 2 a 5 podem usar dados manuais autorizados enquanto a negociação de fonte acontece. A fase 6 só é concluída quando houver fonte e permissão adequadas. Se não houver, o MVP continua operacional com importação manual.

## 10. Validação, lançamento e reversão

- Testes de migração em cópia do banco, com contagens, amostras, chaves e imagens verificadas antes/depois; migrações reversíveis quando viável e backup como via de recuperação.
- Testes de contrato da API e da ingestão com fixtures locais; testes de domínio para invariantes e repetibilidade; simulações estatísticas para detectar regressões de balanceamento. Não depender da disponibilidade de site externo para rodar a suíte.
- Ambiente de homologação com dados separados da produção. Publicar a nova experiência inicialmente por rota/flag; acompanhar erros, importações, saves e latência antes de redirecionar a página principal.
- Plano de reversão: desligar nova rota e jobs, manter o catálogo/snapshot anterior e restaurar backup se uma migração de dados falhar. Nunca rodar os seeds atuais contra produção como ensaio; eles enviam POSTs para a URL publicada.

## 11. Decisões do MVP

Decisões fechadas em 10/11/2026:

1. O jogo roda no navegador e começa sem login obrigatório. Um cookie `HttpOnly` identifica uma sessão anônima, enquanto o conteúdo do save fica no banco. A estrutura permite vincular o save a uma conta futuramente.
2. Cada save controla somente um clube durante a temporada. Um novo save poderá escolher outro clube, mas não haverá troca de clube dentro da temporada do MVP.
3. A temporada usa o calendário real do Brasileirão Série A 2026: 20 clubes, 38 rodadas, datas, confrontos e mandos oficiais. Placares reais não são importados; todos os resultados pertencem à simulação do BRAFOOT.
4. O calendário-base e o snapshot de elenco ficam congelados quando o save começa. Atualizações posteriores não reescrevem a temporada em andamento.
5. A engine começa por um domínio puro, sem dependência de FastAPI ou SQLAlchemy. Uma escalação válida tem exatamente 11 titulares distintos, exatamente um goleiro, todos vinculados ao clube, disponíveis para a partida e uma formação presente no catálogo tático suportado. A disponibilidade distingue jogadores aptos, lesionados e suspensos; os dois últimos não podem ser titulares. O validador retorna todas as infrações com códigos estáveis e os IDs dos jogadores afetados antes de qualquer simulação ou persistência.

Caracterização inicial das escalações existentes: os 20 clubes atendem às regras acima. A referência legada incorreta do Bahia ao jogador `127`, pertencente ao Botafogo no seed reproduzível, foi substituída pelo goleiro João Paulo (`99`) e o goleiro ocupa a primeira posição do desenho tático.

Decisões ainda abertas:

1. Qual grau de realismo e transparência será usado para os atributos iniciais, e quem revisará as estimativas?
2. Qual fornecedor oferece direitos e cobertura suficientes para elenco, escalações e imagens dentro do orçamento quando o protótipo evoluir para produção?

Ordem recomendada: começar pela fase 0 e por uma partida vertical com dados locais; validar diversão e consistência antes de investir em ingestão automática ou recursos de gestão mais amplos.
