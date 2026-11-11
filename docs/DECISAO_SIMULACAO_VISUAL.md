# Decisão técnica — simulação segmentada e visualização 2D híbrida

Status: aceita em 11/11/2026.

## Objetivo

O BRAFOOT apresentará as partidas no navegador por meio de um campinho 2D visto de cima, com movimentação simplificada durante a circulação da bola e cenas mais detalhadas nos acontecimentos relevantes. A referência é a legibilidade dos gerenciadores clássicos, mas interface, recursos visuais, regras e fórmulas serão próprios.

A visualização aumenta a imersão, mas não decide resultados. A engine Python continua sendo a única autoridade sobre posse, confrontos, faltas, cartões, chances, finalizações, defesas, gols, desgaste e alterações do estado da partida. O navegador apenas reproduz eventos que a engine já resolveu.

## Avanço segmentado da partida

A partida não será calculada integralmente antes da exibição porque substituições e mudanças táticas precisam alterar o restante do jogo. A engine avançará por segmentos determinísticos:

- duração padrão inicial: 180 segundos simulados, configurável no `SimulationRuleset`;
- um segmento termina antes do limite quando alcança intervalo, fim de jogo ou uma interrupção relevante que permita decisão do usuário;
- nenhum segmento futuro é calculado enquanto o segmento atual ainda está sendo apresentado;
- comandos solicitados durante a reprodução ficam pendentes e são aplicados na próxima interrupção válida, antes do segmento seguinte;
- substituições, formação, posições atribuídas, postura e intensidade afetam somente eventos posteriores à aceitação do comando;
- eventos e placar de segmentos concluídos são imutáveis.

A quantidade de substituições, as janelas permitidas e quais interrupções aceitam comandos pertencem ao conjunto de regras versionado, não ao front-end.

A primeira fatia de `SimulationRuleset` registra uma versão canônica e a duração positiva do segmento, com padrão de 180 segundos. Os demais limites serão incorporados quando suas regras de domínio forem implementadas, sem usar valores implícitos no front-end.

## Estado e determinismo

Cada segmento recebe um estado completo e devolve um novo estado, eventos semânticos ordenados e um checkpoint persistível. O estado mínimo inclui:

- segundo atual da partida e período;
- placar, posse e zona da bola;
- jogadores em campo, banco e posições atribuídas;
- energia, disponibilidade, cartões e lesões;
- substituições e janelas ainda disponíveis conforme o ruleset;
- formação, postura, intensidade e instruções táticas;
- versão das regras, semente e posição do gerador pseudoaleatório;
- histórico de comandos aceitos.

Mesma entrada inicial, mesma versão de regras, mesma semente e mesmo histórico de comandos devem produzir os mesmos segmentos e eventos. Recarregar a página restaura o último checkpoint confirmado; não recalcula silenciosamente o passado.

Na primeira versão, o relógio regulamentar é contínuo de `00:00` a `90:00`. O primeiro tempo para exatamente em `45:00`, permanece no estado de intervalo até uma transição explícita e o segundo tempo para exatamente em `90:00`. Um avanço nunca consome segundos do período seguinte. Acréscimos e prorrogação ficam fora desta primeira fatia e exigirão regras versionadas próprias.

A zona semântica da bola usa inicialmente uma grade relativa de três terços (`defensivo`, `médio` e `ofensivo`) por três corredores (`esquerdo`, `central` e `direito`). Trocar a perspectiva entre as equipes gira a zona em 180 graus. Coordenadas normalizadas e posições exatas continuam sendo responsabilidade da apresentação e não integram o estado esportivo da engine.

## Eventos da engine e cenas visuais

Existem duas representações distintas:

1. `MatchEvent`: fato semântico e persistente produzido pela engine, como passe, condução, duelo, cruzamento, finalização, defesa, gol, falta, cartão ou substituição.
2. `PresentationScene`: coreografia derivada para o navegador, com posições normalizadas, trajetórias e keyframes de jogadores e bola.

O evento semântico registra minuto, participantes, equipe, zona de origem, zona de destino, contexto, resultado e explicação do cálculo. A cena visual pode ser reconstruída a partir do evento e de uma versão de apresentação, sem alterar o resultado esportivo.

O navegador nunca calcula se um chute foi gol, se um jogador venceu um duelo ou se uma substituição é válida. Queda de FPS, aba em segundo plano, velocidade de reprodução ou tamanho da tela não podem mudar a partida.

## Visualizador 2D híbrido

O visualizador terá uma página própria, separada do editor de escalação, e reutilizará o campo SVG, as coordenadas percentuais e a representação por círculos já existentes. O primeiro formato usa HTML/SVG; Canvas somente será considerado se medições reais mostrarem necessidade.

Decisões de apresentação:

- coordenadas normalizadas de 0 a 100, independentes da resolução;
- 22 jogadores e uma bola, com equipes visualmente distintas;
- posições-base derivadas da formação e espelhadas para o adversário;
- âncoras diferentes para defesa, construção, ataque organizado e transições;
- movimentação simplificada dos jogadores fora do lance;
- coreografia detalhada para passes decisivos, duelos, cruzamentos, chutes, defesas e gols;
- troca visual de lados no segundo tempo;
- relógio, placar, narração, estatísticas, pausa e velocidades de reprodução;
- opção de melhores momentos sem alterar a timeline da engine.

Velocidade de reprodução é uma preferência visual. O relógio oficial, a fadiga e os eventos avançam apenas pelo estado da engine.

## Substituições e decisões durante o jogo

Uma solicitação de substituição contém jogador que sai, jogador que entra e posição atribuída. Antes de aceitá-la, a camada de aplicação consulta as regras da engine e valida elegibilidade, presença no banco, limites, janelas e estado da partida.

Ao aceitar a substituição:

1. encerra-se ou utiliza-se a interrupção válida atual;
2. atualizam-se jogadores em campo, banco e posição atribuída;
3. recalculam-se apenas os perfis setoriais e encaixes afetados;
4. preservam-se placar, eventos e desgaste já ocorridos;
5. grava-se um checkpoint;
6. o segmento seguinte usa a nova composição.

Alterações táticas seguem o mesmo princípio. Um comando não reescreve segmentos já concluídos e não pode ser aplicado retroativamente ao trecho que já está sendo reproduzido.

## Persistência e recuperação

A aplicação deverá persistir, no mínimo, `GameMatch`, `MatchCheckpoint`, `MatchSegment`, `MatchCommand` e `MatchEvent`. Cenas visuais podem ser regeneradas de forma determinística quando a versão de apresentação estiver registrada; se uma cena antiga precisar ser reproduzida exatamente após mudança do coreógrafo, seus keyframes poderão ser armazenados como artefato do segmento.

O checkpoint é salvo após cada segmento confirmado e imediatamente após um comando aceito. Uma falha de rede ou recarga retoma o último checkpoint, sem duplicar eventos nem consumir novamente uma substituição.

## Sequência de entrega

1. Modelar relógio, período, zonas do campo, estado e checkpoint.
2. Implementar avanço puro de um segmento sem eventos complexos.
3. Definir eventos semânticos iniciais e sua ordem determinística.
4. Implementar comandos e substituições nas interrupções válidas.
5. Criar a página separada de partida e renderizar duas formações estáticas.
6. Criar cenas de passe, condução, duelo, cruzamento, finalização, defesa e gol.
7. Reproduzir segmentos e melhores momentos com pausa e velocidades.
8. Persistir checkpoints, comandos e retomada após recarga.
9. Adicionar circulação simplificada entre os destaques.
10. Calibrar duração, frequência dos eventos e clareza visual com partidas completas.

## Critérios de aceite

- mesma entrada, semente, ruleset e comandos geram a mesma timeline;
- uma substituição altera somente os segmentos posteriores à sua aceitação;
- placar é igual aos gols da timeline e não depende da animação;
- recarregar durante uma partida não duplica nem apaga eventos confirmados;
- velocidades de reprodução diferentes produzem o mesmo estado final;
- o visualizador explica os principais acontecimentos sem precisar simular física contínua;
- o modo melhores momentos e a reprodução completa usam os mesmos eventos semânticos.
