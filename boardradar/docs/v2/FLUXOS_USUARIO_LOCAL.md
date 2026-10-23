# Fluxos do PDF — implementação local sem login Google

Diretriz: implementar os fluxos de `BoardRadar_Fluxos_Cadastro_e_Anuncios.pdf`, exceto autenticação Google, expressamente dispensada pelo usuário. Toda execução permanece local, com SQLite e sem serviços de inferência, pagamento ou envio externo de mensagens.

## Conta e personalização

Após cadastrar ou entrar por e-mail/senha, “Minha conta” apresenta **Comprar / explorar**, **Vender um jogo** e **Minhas conversas**. A coleção pessoal é uma seção secundária, recolhida. A mesma conta participa como compradora e vendedora; vender não depende de preencher perfil.

Personalização é opcional e retomável: experiência, estilos, filmes/séries/videogames/franquias e orçamento habitual. O usuário autoriza expressamente salvar e usar essas preferências, pode editá-las, excluí-las ou pular diretamente para vender. Não se infere habilidade permanente.

O perfil ordena sugestões no portal, na vitrine sem filtros atuais e no Radar. Restrições explícitas atuais são aplicadas antes da ordenação; histórico nunca exclui um jogo por si só. Referências são cruzadas com relações editoriais locais conhecidas, sem prometer reconhecer qualquer obra. Orçamento habitual é preferência flexível; limites atuais no chat são mandatórios. O perfil chega ao Python pela sessão validada no servidor, não por um perfil arbitrário enviado pelo navegador. O contexto por requisição é limpo ao terminar.

## Cadastro de anúncio e revisão

Além de jogo/edição, fotos, preço, idioma, componentes e região, há campos explícitos de **lacrado**, **defeitos**, **preço negociável** e **envio, retirada ou ambos**. Lacrado só é permitido para produto novo. Rascunho pode deixar entrega pendente, mas não pode ser enviado assim.

Antes de enviar, o vendedor revisa dados e fotos e aceita as regras locais exibidas. O aceite é vinculado a usuário, anúncio, versão das regras, revisão e horário. Aprovação exige esse aceite atual. Editar conteúdo ou fotos retorna a rascunho, incrementa a revisão e exige novo envio/aceite; não basta uma aprovação antiga.

As regras exibidas exigem dados verdadeiros, fotos reais do item e ausência de fraude e contatos pessoais no texto público. Anúncios com telefone/e-mail no conteúdo são recusados. Textos são renderizados como texto, sem HTML executável. A plataforma não processa pagamentos nem garante vendedores.

Anúncios antigos sem entrega/aceite atual não são expostos na vitrine; o vendedor precisa editar, completar e reenviar. A migração é aditiva, preservando contas e registros.

## Jogo ou edição ausente

Em “Meus anúncios”, o vendedor solicita inclusão informando jogo/edição/idioma. A solicitação é privada e persistente, com estado e parecer consultáveis pelo solicitante. A moderação recebe a fila e pode registrar análise ou rejeição com justificativa.

Registrar análise não inventa um BGG ID nem cria automaticamente edição comercial. A inclusão efetiva continua editorial: revisar fontes, identidade, direitos de uso e dados do catálogo, atualizar os arquivos de origem e reconstruir a aplicação. Enquanto isso, a solicitação permanece registrada; não se publica anúncio sem identidade de edição cadastrada.

## Contato mediado e denúncias

Anúncios ativos têm formulário “Falar com o vendedor”. Somente uma conta autenticada pode iniciar contato; o vendedor não inicia conversa consigo mesmo. A conversa fica ligada ao anúncio e às contas reais derivadas da sessão. Apenas seus dois participantes consultam e respondem em `/mensagens`; nem uma conta alheia com papel de moderador recebe acesso automático às conversas.

Não se publica telefone/e-mail da conta. Mensagens são internas e atualizadas ao abrir/atualizar a tela, sem envio externo ou pagamento. O histórico mantém as mensagens no banco; a tela apresenta as últimas cem por conversa.

Denúncias de anúncios ficam na fila de moderação, deduplicadas por usuário/anúncio. O moderador registra justificativa e pode encerrar sem remoção ou remover o anúncio, retirando-o da busca e bloqueando fotos públicas. Solicitações e mensagens têm limites persistidos de uso por hora, não apenas um botão desabilitado no navegador.

## Wishlist e alertas

O visitante autenticado salva a edição na wishlist sem ativar notificações automaticamente. Em “Minha conta”, pode definir preço-alvo em centavos e optar separadamente por avisos internos de novos anúncios aprovados daquela edição. Salvar novamente pela vitrine não cancela um consentimento existente.

A aprovação gera evento apenas quando edição e preço-alvo correspondem, com opt-in ativo e vendedor diferente do destinatário. Há deduplicação por anúncio/usuário; reativar um anúncio não gera uma sequência de avisos repetidos. É possível marcar como lido, editar a inscrição ou remover/cancelar; cancelar retira avisos ainda não lidos dessa edição.

O aviso registra que houve uma oportunidade, não garante disponibilidade atual. O usuário deve conferir a vitrine novamente. Não há e-mail, push, alertas de preço/estoque de lojas fictícias nem compra confirmada.

## Radar e anúncios

Consultas de ofertas e recomendações podem incluir cartões separados de anúncios ativos da comunidade, obtidos por edição em ferramenta estruturada, com preço lido do banco e orçamento atual respeitado. Ofertas de lojas continuam DEMO e não são misturadas à comunidade. Não se afirma que o anúncio é produto novo de varejista, nem se garante segurança do vendedor ou fechamento de negócio.

## Verificação

- `node scripts/test-python.mjs`: regressões e testes de consentimento, precedência, propriedade, moderação, contato privado, denúncias, solicitações, aceites, antispam e alertas por edição/preço.
- `node scripts/check-user-flows-browser.mjs`: fluxo em Chrome com comprador, vendedor e moderador, em banco isolado `.qa/user-flows-*.sqlite3`; cobre personalização, wishlist, contato, privacidade, solicitações e denúncias, além das fases anteriores.
- `npm run build`: compilação e verificação TypeScript.

A implementação cobre o fluxo funcional local. Não equivale a validação comercial de todas as edições, implantação pública, recuperação de senha por e-mail ou processamento de pagamentos. Login Google permanece excluído por decisão do usuário.
