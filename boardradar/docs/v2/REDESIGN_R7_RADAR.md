# R7 — Radar na página e na janela

## Conversa compartilhada

`/radar-ai` apresenta o assistente em uma página própria. A instância de `ChatAssistant` continua no layout global; a página registra um destino de apresentação e recebe o mesmo painel por portal React. Mensagens, contexto, pergunta em edição, sugestões e consulta em andamento continuam no mesmo componente. Não foi criado outro motor ou sessão de chat.

Na janela há acesso à página; nela, “Usar janela compacta” abre o catálogo com a conversa na janela. Links internos para fichas e retorno ao Radar preservam a conversa. O cabeçalho e o rodapé oferecem a página; os atalhos rápidos existentes continuam abrindo a janela. Na página, o atalho rápido foca o campo existente sem criar outro painel.

Conversa e rascunho são temporários nesta aba durante a navegação interna. Recarregar ou recomeçar limpa o histórico. Não representam histórico persistido na conta nem sincronização entre abas.

## Leitura e ações

Respostas e trechos citados aparecem em parágrafos, com fontes expansíveis preservando título, seção, versão, autoridade e dados de origem. Guias editoriais continuam distinguidos de manuais. A comparação mantém tabela rolável com os dados retornados pelo serviço.

Recomendações e grupos de ofertas têm ações para ficha, ofertas DEMO, comparação e wishlist da edição cadastrada. Salvar envia somente `edition_id`, sem alterar preço-alvo ou consentimentos existentes. Visitantes recebem um link para entrar e retornar à ficha da edição. Anúncios da comunidade apontam ao detalhe público, onde disponibilidade e permissão são conferidas novamente.

Capas/avaliações/preços novos não foram inventados. Valores de lojas continuam DEMO, e anúncios de usuários permanecem apresentados separadamente. O conteúdo e as regras do Python não foram alterados.

## Consulta e acessibilidade

O botão “Cancelar consulta” aborta o pedido, restaura a pergunta e impede que uma resposta atrasada altere a conversa. Timeout e recomeço mantêm as proteções por versão da consulta. Alternar entre página e janela não reinicia o pedido. A expansão da janela conserva diálogo, Escape, controle de foco e bloqueio de rolagem; a página usa região normal, com navegação ao redor disponível.

Rolagem automática fica no histórico de mensagens. O foco ao abrir não desloca a página inteira. Sugestões têm rolagem interna horizontal e controles com áreas de toque maiores. Estilos específicos em `src/styles/radar.css`.

## Validação

Build de produção e TypeScript; 29 testes TypeScript. `scripts/check-redesign-r7.mjs` verifica 105 cenários em cinco larguras, mais conversa entre apresentações, preservação do rascunho, fontes em texto corrido, ações de ficha/comparação/ofertas, wishlist sem sobrescrever alertas e link público da comunidade.

O teste pausa uma requisição real pelo navegador, cancela e confere que nenhuma resposta atrasada foi adicionada; também verifica recomeço. Mantém regressões de conta, consentimento, notificações, venda, fotos e navegação. Evidências em `docs/redesign/r7`. Banco e arquivos de teste são isolados; APIs, Python e dados existentes permanecem preservados.

Sem certificação integral de acessibilidade ou medição de desempenho nesta etapa. Próxima fase: R8, revisão final das jornadas, acessibilidade, SEO e desempenho.
