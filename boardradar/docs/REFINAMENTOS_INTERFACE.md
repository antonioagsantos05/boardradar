# Refinamento de descoberta e área pessoal

Entrega baseada nas telas enviadas após o redesign R8.

## Interface

- Home com título, busca e ações reorganizados. As seções “Qual é o seu estilo de jogo?” e “Do controle à mesa”, incluindo seus links no cabeçalho, foram removidas. As preferências existentes continuam disponíveis no perfil e no motor de recomendações.
- Topo do catálogo reúne apresentação, busca, ordenação e quantidade por página. Os filtros seguem globais, aplicados antes da paginação.
- Radar com janela mais espaçosa, identificação de quem fala, melhor contraste, cards e ações mais legíveis. A página, a janela compacta e a expansão continuam usando a mesma conversa, incluindo cancelamento e preservação do rascunho.
- Favoritos mostram os jogos em cards, incluindo registros importados. Remover um favorito atualiza a tela e o armazenamento local. Wishlist da conta, edição e consentimento para alertas continuam separados, com transferência explícita.
- Minha conta passa a ter navegação lateral, resumo da atividade e acompanhamento dos anúncios. A coleção fica em `/minha-conta?sec=colecao`, com cadastro, edição e remoção, sem depender do painel antigo. A rota `/conta` continua compatível.
- Formulários de perfil, estados vazios e controles da área pessoal receberam ajustes de espaçamento e tamanho.

## Por que o anúncio não aparecia

O banco local continha um anúncio de Dixit em `pending_review`, aguardando moderação. Salvar um jogo pessoal não cria uma oferta; salvar um rascunho também não publica um anúncio. Agora o resumo da conta e Meus anúncios explicam o próximo passo de cada estado.

O anúncio real não foi aprovado automaticamente nem alterado. A revisão continua em `/moderacao`, por outra conta com papel de moderador, conforme o fluxo existente. Para preparar essa conta local, consulte o procedimento de `scripts/set-moderator.py` na documentação de marketplace. O vendedor não revisa o próprio anúncio.

## Exemplos locais

Foram adicionados oito anúncios fictícios: Catan, Azul, Dixit, Wingspan, Carcassonne, Ticket to Ride, Splendor e Pandemic. Todos têm título `[DEMO]`, descrição explícita e imagem ilustrativa marcada como fictícia. São exemplos de interface, sem item real à venda.

Os exemplos pertencem a identidades reservadas de demonstração, separadas do usuário real. O script usa o fluxo de rascunho, imagem, aceite e revisão apenas para essas fixtures. Não publica anúncios de usuários. As sessões temporárias são removidas ao terminar; nenhuma senha fixa de demonstração é exposta.

```text
npm run seed:community-demo
```

A execução é idempotente por identidade/título: repetir não duplica os oito registros nem reativa exemplos encerrados. Antes de escrever em um banco existente, cria um backup SQLite consistente em `.local/backups/`. Se `RADAR_ACCOUNT_DB` estiver definido, o script usa esse banco, assim como a aplicação.

## Verificação

```text
npm run build
npm run check:ui
npm run audit:ui
```

A regressão ampliada cobre 120 cenários responsivos, fluxos anteriores de conta e marketplace, CRUD da coleção com recarga, favoritos importados, remoção de favoritos preservando a wishlist, explicação do estado pendente e criação idempotente dos exemplos. Todos os testes de navegador usam contas e bancos isolados. Evidências em `docs/refinements/flows/browser-baseline.json`.

A auditoria acessível cobre 50 cenários, incluindo perfil, coleção e favoritos preenchidos. As evidências e capturas estão em `docs/refinements/`. A auditoria automática não equivale a certificação WCAG; as verificações humanas continuam necessárias. O build inclui TypeScript, e os 32 testes TypeScript existentes foram aprovados. O motor Python não foi modificado nesta entrega.

O item “remover ft” ainda precisa da identificação da imagem a remover. Não foi presumida a exclusão de fotos de anúncios nem das capas do catálogo.

Para ver o resultado no servidor de produção local, reinicie `npm start` após o build e atualize o navegador com Ctrl+F5.
