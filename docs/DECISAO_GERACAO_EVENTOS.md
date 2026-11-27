# Geração determinística de eventos (Fase 3, primeira fatia)

Implementada em `brafoot/engine/simulation.py`, com sorteios em `randomness.py` e calibração em
`SimulationTuning` (`rulesets.py`). A engine continua independente de FastAPI, banco e interface.

## Entradas e saídas

- Entrada: `MatchState`, `SimulationRuleset`, duas `SimulatedTeam` (11 jogadores atribuídos com
  perfil; `build_simulated_team` valida 11 jogadores e um goleiro e deriva as forças setoriais) e a
  próxima sequência de eventos.
- Saída: `SegmentSimulation` com os eventos confirmados, o novo estado e o motivo da parada. O mesmo
  estado, ruleset e equipes produzem exatamente os mesmos eventos. `simulate_match` encadeia os 30
  segmentos de uma partida regulamentar.

## Aleatoriedade

`DeterministicStream` é baseado em contador: o sorteio *n* depende só de `(semente, n)` (BLAKE2b),
independente de plataforma. O estado guarda `random_seed` e `random_step`, então retomar de um
snapshot continua a mesma partida (coberto por teste).

## Modelo de ação

A cada passo, o time com a bola escolhe passe, condução, cruzamento ou finalização conforme a zona
(grade 3×3 do ponto de vista de quem tem a posse). O portador é rastreado: `MatchState.ball_holder_id`
é persistido (snapshots antigos sem o campo ainda são lidos). Probabilidades combinam as forças
setoriais dos dois times, atributos individuais do portador e um pequeno mando de campo:

| Ação | Resultado | Eventos |
| --- | --- | --- |
| Passe | completo ou interceptado | `PASS`, `POSSESSION_CHANGE` |
| Condução | progride ou perde para um desarme | `CARRY`, ou `DUEL` + `POSSESSION_CHANGE` |
| Cruzamento | completo (pode virar cabeçada) ou afastado | `CROSS`, `SHOT`, `POSSESSION_CHANGE` |
| Finalização | fora, bloqueada ou no alvo; no alvo vira gol ou defesa | `SHOT`, `GOAL`, `SAVE`, `POSSESSION_CHANGE` |

Convenções: zonas e `team_side` são da equipe que age; os participantes pertencem a ela (exceto o
segundo jogador de um `DUEL`). Um gol entrega o início de jogo ao time que sofreu; uma defesa deixa a
bola com o goleiro; tiro de meta e bloqueio geram `POSSESSION_CHANGE`.

## Calibração (ruleset `2026.1`)

Bateria de 300 partidas por cenário, equipes com todos os atributos iguais:

| Cenário | Gols/jogo | V/E/D (mandante) | Chutes/time | Acerto de passe |
| --- | --- | --- | --- | --- |
| 10 × 10 | 2,63 | 44 / 23 / 33 % | 12,7 | 82 % |
| 11 × 10 | 2,50 | 50 / 30 / 21 % | – | – |
| 12 × 9 (casa mais forte) | 3,03 | 70 / 17 / 12 % | 17,8 / 9,5 | 80–85 % |

A sensibilidade à força foi reduzida após uma primeira calibração em que 12 × 9 dava 88% de vitória
da equipe mais forte. Os valores finais estão nas faixas dos testes (`slow`) de equilíbrio e de força.

## Limites conhecidos desta fatia

- Sem assistências, faltas, cartões, impedimentos, pênaltis, escanteios, lesões, fadiga e
  substituições durante o segmento (os comandos existem; a integração com o segmento é futura).
- Substituições exigirão reconstruir `SimulatedTeam` a partir da `MatchTeamSelection` atual.
- A bola é modelada só por zona 3×3; posições exatas continuam na camada de apresentação.
- Tipos de evento ainda sem cena: `DUEL`, `SAVE`, `GOAL`, `POSSESSION_CHANGE` (passo 3 do plano).
