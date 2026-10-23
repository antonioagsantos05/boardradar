# R4 — Página central do jogo

A ficha editorial destaca o jogo, seus dados, edição selecionada, resumo de preços DEMO elegíveis e wishlist da conta. “Onde comprar” e comunidade aparecem antes da comparação, pesquisa, informações BGG e conteúdo complementar. Os links de comparação e comunidade permanecem no cabeçalho do produto.

## Compra e edição

`OfferCard` substitui a tabela comercial por cards responsivos com loja fictícia, preço do produto, frete não incluído, condição, data simulada e disponibilidade. A mesma política existente de elegibilidade controla o resumo e as ações: edição correta, loja DEMO, moeda, integridade, estoque e validade temporal. Registros indisponíveis/desatualizados continuam identificados e desativados.

“Ver demonstração” apenas explica a simulação; não compra ou redireciona. O bloqueio `/out/*` foi preservado. Anúncios de usuários ficam em uma seção distinta, com as ações de contato e denúncia existentes, filtrados pela edição selecionada. A mudança de edição remonta essa seção para evitar exibir anúncios anteriores enquanto a nova consulta carrega.

O seletor atualiza `?edition=`, preservando outros parâmetros e âncora. Voltar/avançar restaura a seleção. Edição inválida no link recebe aviso explícito e exibe a primeira cadastrada. O catálogo atual tem somente uma edição por jogo; não foram criadas edições artificiais para preencher opções. Testes verificam edição estrangeira, URL e política de bloqueio, sem alegar uma jornada de duas edições reais que os dados ainda não oferecem.

## Wishlist e conteúdo

`EditionWishlist` consulta a sessão real. Visitantes recebem acesso à conta; pessoas autenticadas salvam a edição pelo contrato `save_wishlist`. A ação envia somente `edition_id`, preservando alertas/preço-alvo existentes e sem ativar consentimento. Configuração e remoção continuam na conta. Há estados de consulta, falha, salvamento e confirmação.

“Por que jogar?” usa descrição e categoria editoriais existentes. Pesquisa, fontes, histórico sintético, comparação e relacionados continuam disponíveis. Nenhuma análise por IA, avaliação ou disponibilidade foi inventada.

Registros importados usam o mesmo tratamento visual e capa ilustrativa, com “Onde comprar” mostrando ausência de preço/edição verificados. A wishlist por edição não é oferecida sem identidade comercial. O link ao marketplace é identificado como busca geral, sem vincular ofertas de outro produto.

## Validação

- Build de produção e TypeScript; 26 testes TypeScript, incluindo ação DEMO habilitada/desativada para edição errada, indisponibilidade e datas inelegíveis.
- `scripts/check-redesign-r4.mjs`: banco isolado e 55 cenários em cinco larguras, sem overflow de documento ou exceções JavaScript.
- Verificações de aviso/isolamento da edição, histórico da URL, ação DEMO, saída bloqueada, wishlist autenticada/visitante, preservação de alertas, comparação e ficha importada sem oferta indevida.
- Evidências em `docs/redesign/r4`.

Estilos em `src/styles/product.css`. Nenhuma alteração em contas, Python, APIs ou dados de produção. Sem certificação completa de acessibilidade ou medição de desempenho. Próxima fase: R5, marketplace e fluxo de venda em etapas.
