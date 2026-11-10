# Decisão: fontes de dados gratuitas no início do BRAFOOT

- **Status:** aceita
- **Data:** 10/11/2026
- **Escopo:** desenvolvimento inicial, protótipo e MVP
- **Relacionada a:** [PLANO_BRAFOOT.md](PLANO_BRAFOOT.md)

## Contexto

O BRAFOOT precisa de clubes, jogadores, elencos, calendário, resultados e metadados para desenvolver sua engine. APIs esportivas completas cobram assinaturas e ainda podem exigir licenças adicionais para publicar dados, fotos e escudos. O projeto não assumirá esse custo antes de validar a jogabilidade, a simulação e o fluxo de uma temporada.

Também não construiremos a base do projeto sobre scraping de sites que proíbem coleta automatizada ou não concedem direito de reutilização. Esse tipo de dependência pode ser bloqueado, mudar sem aviso e impedir a publicação do jogo.

## Decisão

Durante o desenvolvimento inicial, o BRAFOOT adotará uma estratégia composta e sem assinatura paga:

1. Os seeds e dados já existentes no projeto formarão o primeiro snapshot local do Brasileirão 2026.
2. Um importador CSV será o caminho oficial para corrigir e atualizar clubes, jogadores e vínculos durante o protótipo.
3. A API-Football gratuita poderá gerar snapshots ocasionais, respeitando o limite de 100 requisições por dia e as temporadas disponíveis no plano gratuito.
4. O football-data.org gratuito poderá complementar calendário, resultados e classificação do Brasileirão.
5. A Wikidata será usada para metadados estruturados disponibilizados em CC0, como identidade, nacionalidade, nascimento e altura, quando presentes.
6. O OpenFootball poderá fornecer resultados e calendários históricos em domínio público para testes e calibração.
7. TheSportsDB poderá ser consultada apenas como fonte complementar, pois seu conteúdo comunitário não garante cobertura uniforme de elencos.
8. Todo dado importado passará por normalização, comparação e aprovação antes de virar um snapshot publicável.
9. Saves e temporadas iniciadas sempre apontarão para um snapshot congelado. Atualizações posteriores não modificarão partidas ou elencos de um save em andamento.

Nenhuma dessas fontes será tratada como dona dos atributos do jogo. Atributos BRAFOOT serão calculados ou revisados dentro do projeto e manterão sua própria versão e procedência.

## Papel de cada fonte

| Fonte | Uso previsto | Limitação principal |
| --- | --- | --- |
| Seeds atuais | Snapshot inicial de clubes e jogadores | Exigem revisão e atualização manual |
| CSV manual | Correções e atualização controlada | Depende de curadoria |
| API-Football Free | Consulta ocasional de clubes, elencos, jogadores e partidas | 100 requisições/dia; temporadas gratuitas limitadas; direitos de publicação não incluídos automaticamente |
| football-data.org Free | Calendário, resultados e classificação | Sem dados profundos de jogadores no plano gratuito |
| Wikidata | IDs, nomes, nascimento, nacionalidade, altura e outros metadados CC0 | Dados de clube e elenco podem estar incompletos ou desatualizados |
| OpenFootball | Calendários e resultados históricos CC0 | Não oferece elencos completos |
| TheSportsDB Free | Consulta complementar e protótipos | Cobertura comunitária e irregular |

## Política para scrapers

Um scraper só poderá ser incorporado quando a fonte:

- permitir acesso automatizado e reutilização nos termos aplicáveis;
- não exigir contorno de login, proteção, bloqueio ou endpoint privado;
- possuir limites de coleta que possamos respeitar;
- aceitar cache ou armazenamento compatível com nossos snapshots;
- tiver um adaptador isolado que possa ser desligado sem afetar a engine;
- registrar URL, horário da coleta, versão do parser e procedência de cada lote;
- preservar o último snapshot válido quando a coleta falhar.

Sofascore e outras fontes que proíbem scraping sem consentimento não serão usadas por scraper. Quando existir API oficial ou autorização escrita compatível com o jogo, ela poderá ser avaliada como novo adaptador.

## Arquitetura resultante

Todas as fontes deverão implementar a mesma fronteira conceitual:

```text
coletar -> normalizar -> validar -> comparar -> aprovar -> publicar snapshot
```

A engine e os saves não acessarão APIs ou páginas externas diretamente. Eles lerão somente o catálogo interno e snapshots publicados. IDs internos serão permanentes; IDs de cada fornecedor ficarão em mapeamentos separados.

Cada lote deverá registrar, no mínimo:

- fonte e identificador externo;
- instante da coleta;
- competição e temporada;
- versão do importador;
- campos recebidos e campos ausentes;
- confiança e estado de revisão;
- diferenças em relação ao snapshot anterior.

## Atributos no período sem API paga

Os atributos iniciais serão gerados por perfis de posição e ajustados por curadoria. Dados como idade, altura, minutos e estatísticas disponíveis poderão influenciar a estimativa, mas não serão convertidos automaticamente em diagnóstico físico.

Serão separados:

- atributo base do jogador;
- condição, forma e fadiga dentro do save;
- efetividade calculada em cada partida;
- avaliação geral derivada para apresentação.

Cada atributo guardará versão, método e nível de confiança. Não serão copiadas avaliações proprietárias de PES, Football Manager ou outro jogo.

## Consequências

### Benefícios

- desenvolvimento sem mensalidade de dados;
- engine executável offline e testes reproduzíveis;
- independência de um único fornecedor;
- atualização revisável e reversível;
- caminho simples para conectar uma API licenciada no futuro.

### Custos aceitos

- alguma curadoria manual no início;
- dados menos atualizados durante o protótipo;
- cobertura desigual entre fontes gratuitas;
- necessidade de detectar duplicatas, transferências e conflitos;
- fotos e escudos continuam sujeitos a direitos próprios e não são liberados apenas porque uma API fornece a URL.

## Critério para reavaliar

A contratação de uma fonte paga só será considerada quando o projeto tiver uma vertical jogável validada e pelo menos uma destas necessidades for concreta:

- atualização automática frequente em produção;
- cobertura de várias ligas com qualidade uniforme;
- estatísticas que reduzam significativamente a curadoria;
- licença comercial clara para o uso pretendido;
- volume que ultrapasse os limites gratuitos;
- receita ou orçamento que justifique o custo recorrente.

Antes de contratar, será feita uma prova de conceito comparando cobertura, campos ausentes, estabilidade de IDs, termos de armazenamento, direito de produzir atributos derivados e custo total.

