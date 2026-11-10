# Base local, migrações e calendário do BRAFOOT

## Escopo implementado

- Alembic com uma migração de baseline para `times` e `jogadores` e uma migração para catálogo e saves.
- Catálogo versionado com `Competition`, `Season`, `Club` e `Fixture`.
- Calendário oficial do Brasileirão Série A 2026 com 20 clubes, 38 rodadas e 380 partidas.
- Seed local idempotente que reutiliza os dados dos módulos antigos sem fazer requisições HTTP.
- Sessão anônima por cookie e save persistido no banco.

O calendário foi extraído da tabela detalhada publicada pela CBF. O snapshot local guarda apenas referências, datas, horários disponíveis, rodadas e mandos. Placares reais são descartados para que cada save produza resultados próprios.

Fonte: [Tabela oficial do Campeonato Brasileiro Série A 2026](https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a).

## Criar uma base local

No PowerShell:

```powershell
$env:SEED_DATABASE_URL = "sqlite+pysqlite:///./brafoot_dev.db"
venv\Scripts\python.exe seed_all.py
```

O nome do SQLite precisa terminar em `_dev.db` ou `_test.db`. Para PostgreSQL, o host precisa ser local e o nome do banco deve terminar em `_dev` ou `_test`. O comando recusa hosts remotos.

O seed executa as migrações, cria ou atualiza os 20 times e seus jogadores, conecta os registros legados ao catálogo e importa as 380 partidas. Reexecutá-lo não duplica registros.

A aplicação não executa `create_all` por padrão. Em uma compatibilidade local temporária, `AUTO_CREATE_SCHEMA=1` reativa o comportamento antigo, mas o fluxo recomendado é sempre aplicar Alembic antes de iniciar o servidor.

## Executar migrações manualmente

```powershell
$env:MIGRATION_DATABASE_URL = "sqlite+pysqlite:///./brafoot_dev.db"
venv\Scripts\python.exe -m alembic upgrade head
```

Por segurança, a migração recusa uma URL igual à `DATABASE_URL` da aplicação. Uma migração deliberada de produção exige `ALLOW_PRODUCTION_MIGRATIONS=1`, além de backup e autorização explícita.

## Banco legado existente

A revisão `0001_legacy_baseline` representa as tabelas que já existiam antes do Alembic. Em um banco legado, não execute essa criação diretamente. O procedimento futuro será:

1. criar e validar um backup restaurável;
2. conferir manualmente esquema, contagens e amostras;
3. marcar o banco com `alembic stamp 0001_legacy_baseline`;
4. executar apenas as migrações posteriores;
5. comparar os dados antes e depois.

Esse procedimento ainda não foi autorizado nem executado em Railway ou produção.

## API inicial

- `GET /api/v1/seasons/{season_id}/fixtures`: calendário ordenado por rodada.
- `POST /api/v1/saves`: inicia um save controlando um clube.
- `GET /api/v1/saves/current`: recupera o save ativo da sessão anônima.

O cookie `brafoot_session` contém somente um token aleatório. O banco armazena apenas o hash desse token. O cookie usa `HttpOnly` e `SameSite=Lax`; em produção, configure `COOKIE_SECURE=1`.
