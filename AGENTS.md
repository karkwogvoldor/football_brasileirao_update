# AGENTS.md

## Escopo

Estas instruções se aplicam a todo o repositório.

## Forma de desenvolvimento

- Desenvolva cada feature junto com testes proporcionais ao risco e ao comportamento alterado.
- Preserve o comportamento existente com testes de caracterização antes de refatorações relevantes.
- Dê preferência a testes de domínio para regras da engine e a testes de integração para API, banco, persistência, importadores e limites entre módulos.
- Toda correção de bug deve incluir um teste que falhe sem a correção e passe com ela, quando o comportamento puder ser reproduzido de forma determinística.
- Mantenha os testes independentes, determinísticos e executáveis sem acesso à produção.

## Integridade dos testes

- Todo teste criado deve ter imediatamente acima da função um breve comentário iniciado por `#`, explicando o comportamento que ele verifica.
- Jamais afrouxe, remova, pule ou reescreva um teste apenas para fazê-lo passar.
- Não diminua a precisão das asserções, não aumente tolerâncias sem evidência e não substitua o objeto testado por mocks que eliminem o comportamento relevante.
- Não use `skip`, `xfail`, filtros, retries ou exclusões para esconder regressões. Uma exceção legítima precisa de motivo técnico documentado e autorização do usuário.
- Quando um teste revelar um defeito, corrija a implementação. Se o requisito mudou, atualize o teste e a documentação de forma explícita, explicando a mudança de comportamento.
- Não altere dados esperados, snapshots, fixtures ou métricas de balanceamento apenas para acomodar uma saída incorreta.
- Não considere a suíte aprovada quando somente um subconjunto conveniente foi executado. Informe exatamente quais grupos foram rodados e quais não puderam ser executados.

## Segurança dos testes

- Testes automatizados nunca podem acessar ou modificar o banco de produção, o Railway, o Cloudinary real ou serviços externos reais por padrão.
- O banco de integração deve ser temporário ou ter nome terminado em `_test`. A suíte deve recusar uma URL igual à `DATABASE_URL` da aplicação.
- Seeds que apontam para a aplicação publicada não podem ser executados durante testes.
- Chamadas externas pertencem ao marcador `external`, são opt-in e não fazem parte da execução padrão.
- Segredos e tokens ficam somente em variáveis de ambiente e nunca entram em fixtures, logs ou arquivos versionados.

## Execução

- Use o Python do projeto no Windows: `venv\Scripts\python.exe`.
- Execução padrão segura: `venv\Scripts\python.exe -m pytest -m "not external"`.
- Use `scripts\test.ps1` para selecionar `fast`, `integration`, `contract`, `all` ou `external`.
- Antes de entregar alterações Python, execute os testes relevantes e, quando viável, a suíte padrão completa.

## Arquitetura de testes

- `tests/unit`: regras puras e determinísticas, especialmente da futura engine.
- `tests/integration`: API, SQLAlchemy, banco, arquivos e integração entre módulos locais.
- `tests/contract`: formato de adaptadores de dados usando respostas locais versionadas.
- `tests/external`: verificações opt-in contra provedores reais, sem mutações.
- Use dados pequenos e explícitos. Evite depender da ordem global de IDs ou do estado deixado por outro teste.

## Controle de mudanças

- Preserve mudanças do usuário e não edite arquivos fora do escopo da tarefa.
- Não faça commit, push, deploy ou alteração em serviços externos sem solicitação explícita.
- Registre decisões arquiteturais relevantes em `docs/`.

