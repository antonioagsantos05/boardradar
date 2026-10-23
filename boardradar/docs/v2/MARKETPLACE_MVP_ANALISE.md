# Documentação recebida: marketplace no MVP

Os dois DOCX do ZIP `BoardRadar_2_0_Documentacao_Marketplace_MVP.zip` foram preservados em `fontes/marketplace-mvp/`, com hashes em `manifest.json`. São especificações fornecidas, não funcionalidades comprovadas nem autorização para publicação externa.

## Mudança central de escopo

A decisão final dos documentos passa a exigir marketplace no lançamento comercial: anúncios com usuário autenticado, jogo/edição, preço, condição, idioma, região, componentes e fotos; envio para revisão; publicação após aprovação; busca e página do jogo; contato mediado; denúncias e gestão de disponibilidade.

Há trechos antigos ainda conflitantes: o funil mantém “fase posterior”, a tabela comercial ainda cita evolução 2.2 e a técnica mantém R4. A seção final expressamente define marketplace como obrigatório do MVP e deve orientar a revisão do planejamento, sem alegar implementação pronta.

## Diferença para o código atual

- Existente: contas locais, sessão, senhas com hash, SQLite persistente e registros pessoais com autorização por proprietário.
- Ausente: entidades e migrações de anúncios/edições vinculadas, fotos, estados de publicação, permissões de moderador, auditoria, denúncias, solicitações de contato e consultas de anúncios ativos.
- Ausente: separação visual das ofertas de lojas e anúncios na ficha; consulta pelo Radar a anúncios elegíveis; alertas de wishlist por edição.
- Os registros de “Meus jogos” não são anúncios e não devem ser publicados automaticamente.

## Sequência de implementação proposta

1. Modelo de anúncios referenciado em jogo/edição, migrações que preservem contas e jogos existentes, estados e autorização por papel.
2. Cadastro de anúncio e fotos locais com validação, armazenamento privado, envio à moderação e ferramentas locais para atribuir moderador explicitamente.
3. Revisão, auditoria, descoberta de ativos e seção própria na ficha; pausa, reserva, venda e remoção controladas.
4. Contato mediado, denúncias e proteção contra spam.
5. Consulta estruturada pelo Radar e wishlist por edição com alertas internos consentidos.
6. Testes de autorização, arquivos, transições e fluxo completo com duas contas e moderador.

Tudo permanece local conforme orientação vigente. Não ativar pagamento, envio externo de mensagens, parceiros, LLM ou publicação na internet apenas por constarem nos documentos. O pacote recebido nesta mensagem não veio acompanhado de uma instrução textual de implementação; esta entrega registra a análise, sem apresentar o marketplace como concluído.
