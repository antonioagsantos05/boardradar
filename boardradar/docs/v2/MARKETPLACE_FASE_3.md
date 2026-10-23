# Marketplace — fase 3

Esta página registra a entrega da fase 3. As pendências do PDF listadas aqui foram tratadas no incremento seguinte, exceto login Google dispensado pelo usuário; veja o [estado consolidado dos fluxos](FLUXOS_USUARIO_LOCAL.md).

## Entrega

A vitrine `/marketplace` apresenta somente anúncios aprovados e ativos. A busca aceita jogo, título e região, com paginação de 24 registros e ordenação por preço. Rascunhos, pendentes, rejeitados, reservados, pausados, vendidos e removidos não aparecem como disponíveis.

A página de cada jogo mantém ofertas fictícias de lojas e anúncios da comunidade em seções separadas. A seção da comunidade usa a edição selecionada; o link da vitrine abre a ficha com essa edição na URL. Preço, conservação, componentes, idioma, região e atualização são identificados como informações do vendedor. Não existe checkout ou CTA de contato que aparente uma função ainda indisponível.

Em **Meus anúncios**, o vendedor pode reservar, pausar, reativar ou marcar vendido. Somente o dono pode alterar disponibilidade, com revisão atual. Reativação só é permitida quando há aprovação anterior que não foi invalidada por alterações. Vendido é terminal nesta entrega. Alteração de conteúdo ou fotos volta a rascunho e exige moderação, inclusive ao editar um anúncio reservado.

## Privacidade e fotos

A projeção pública contém apenas os campos da oferta, sem e-mail, ID do vendedor, justificativas privadas ou dados da conta. Fotos só têm leitura pública enquanto o anúncio está ativo. Fora desse estado, permanecem restritas ao dono e à moderação. URLs antigas não continuam oferecendo fotos a visitantes; as respostas não são armazenadas em cache.

“Público” significa visível a qualquer visitante desta instalação em loopback; nenhum deploy externo ou anúncio fora da máquina foi realizado. Contato mediado e denúncias ficam na fase 4; ferramentas do Radar e alertas de wishlist na fase 5.

## Uso e verificação

Reinicie `npm start`, crie e aprove um anúncio com duas contas conforme o guia da fase 2 e abra `/marketplace`. Acesse a ficha do jogo para comparar os dados das fontes separadamente.

Testes Python: `node scripts/test-python.mjs`. Verificação em navegador: `node scripts/check-marketplace-phase3-browser.mjs`, com banco isolado em `.qa/`. O fluxo cobre também as regressões de conta, fotos e moderação.

## PDF de fluxos recebido durante a implementação

O arquivo original está em `fontes/BoardRadar_Fluxos_Cadastro_e_Anuncios.pdf`. Foram lidos o texto das cinco páginas e os diagramas incorporados nas páginas 2 e 3. Ele complementa o planejamento, sem acionar integrações externas por si só.

Já atendidos: conta por e-mail/senha, login, mesma conta compradora/vendedora, acesso direto aos anúncios, seleção de jogo/edição/idioma, descrição de componentes, preço, fotos reais fornecidas pelo vendedor, região, rascunho, revisão com justificativa, publicação após moderação, busca, ficha do jogo e controles de disponibilidade.

Pendências incorporadas ao plano: personalização opcional e retomável (experiência, estilos, entretenimento e orçamento), autenticação Google opcional, solicitação de inclusão de jogos ausentes, condição lacrado explícita, negociação e modalidade de entrega/retirada, revisão final com aceite versionado das regras, contato mediado, denúncias e alertas consentidos por edição. O estado atual não deve ser apresentado como atendimento integral desse PDF.

O vendedor pode acessar o fluxo de anúncios sem preencher preferências. Não foi implantada autenticação Google nem perfil persistente neste incremento local. Solicitações para jogos ausentes não devem criar automaticamente uma edição comercial não validada.
