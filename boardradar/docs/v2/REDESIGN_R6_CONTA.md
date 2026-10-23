# R6 — Conta, perfil, wishlist e notificações

## Telas e navegação

- `/entrar` e `/cadastro`: formulários separados sobre a autenticação local existente. Cadastro não exige perfil ou consentimento para personalização. Quem escolhe vender segue diretamente para `/vender`; quem explora pode personalizar ou pular.
- `/minha-conta`: resumo dos dados, perfil opcional, avisos e acesso/segurança, com links para wishlist, anúncios, conversas e coleção. A seção fica na URL por `?sec=`.
- `/onboarding`: personalização opcional, com experiência, estilos, videogames, referências e orçamento habitual. Consentimento explícito para salvar; pode ser pulada, retomada, alterada e excluída.
- `/favoritos`: wishlist persistida por edição e apresentação separada dos favoritos deste navegador.

Cabeçalho, navegação mobile e rodapé apontam às novas telas. `/conta` e suas âncoras continuam válidos; a coleção pessoal permanece disponível nela por `#colecao`, sem migrar ou apagar registros.

O retorno após autenticação aceita somente destinos internos limitados, incluindo fichas de jogos com edição. Entrar a partir de uma ficha mantém o jogo/edição como destino; salvar na wishlist continua sendo uma ação explícita após entrar.

## Favoritos e consentimento

Favoritos locais continuam armazenados no navegador. A wishlist da conta permanece por edição no SQLite. A tela permite escolher uma edição cadastrada de um jogo local e adicioná-la à conta, sem remover o favorito local e sem ativar alertas. Não há sincronização automática nem transferência presumida de registros importados sem edição comercial.

O formulário de wishlist carrega o preço-alvo e o consentimento existentes da edição inicial. Selecionar outra edição ou editar um alerta também carrega seus valores. Isso evita sobrescrever um alerta anterior com valores iniciais em branco. O preço-alvo aceita centavos inteiros, com vírgula ou ponto e até duas casas decimais, sem arredondar entradas inválidas.

Alertas são opcionais e somente de novos anúncios internos aprovados da edição, respeitando o preço-alvo do contrato existente. Alertas de lojas DEMO não aparecem como ativos. Remover/cancelar usa a ação real do backend, preservando a retirada de avisos não lidos conforme a regra existente.

## Avisos, sessão e limites

A área de notificações permite atualizar, consultar a página pública do anúncio e marcar avisos como lidos. O anúncio pode ter ficado indisponível; a página pública confere o estado novamente. Não há e-mail ou push externo.

A seção de segurança encerra a sessão real e atualiza a navegação. Favoritos deste navegador são mantidos. Expiração de sessão durante ações do perfil/wishlist atualiza o estado autenticado. Não foram criados botões funcionais de recuperação de senha, edição de dados pessoais ou troca de senha sem contrato. Login Google continua excluído.

## Implementação e validação

Componentes novos: `AccountAccess`, `AccountArea`; modos separados de perfil/wishlist/avisos em `AccountJourney`. Estilos em `account.css` e regras de destino/preço-alvo em `domain/account-ui.ts`. APIs, Python, banco e dados existentes não foram alterados.

Build de produção e TypeScript; 29 testes TypeScript. `scripts/check-redesign-r6.mjs` usa contas/banco isolados, percorre 100 cenários em cinco larguras e valida cadastro, pular perfil, salvar/excluir preferências, transferência explícita, preservação de alertas e preço-alvo, notificação real após aprovação, leitura, cancelamento e logout com favoritos locais preservados. Também mantém regressões da venda, fotos, detalhe público, Radar e navegação. Evidências em `docs/redesign/r6`.

Não há certificação integral de acessibilidade ou medição de desempenho nesta fase. Próxima entrega: R7, página e janela do Radar compartilhando conversa e contratos.
