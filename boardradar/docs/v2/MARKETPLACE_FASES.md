# Marketplace local: plano e fase 1

## Fases

1. **Fundação e rascunhos — implementada:** modelo relacional, jogo/edição, preço em centavos, condição, idioma, região, componentes, rascunhos privados, edição, remoção lógica, auditoria e autorização.
2. **Fotos e publicação — implementada:** validação de arquivos, armazenamento privado, envio para revisão, fila de moderação, aprovação/rejeição e revalidação após edição. Veja [instruções e validação da fase 2](MARKETPLACE_FASE_2.md).
3. **Descoberta e disponibilidade — implementada:** busca de anúncios ativos, seção separada na ficha da edição e estados reservado, pausado e vendido. Veja [entrega e aderência ao PDF de fluxos](MARKETPLACE_FASE_3.md).
4. **Contato e denúncias — implementada localmente:** mensagens mediadas, denúncias, limites persistidos de uso, revisão final com aceite versionado, entrega/retirada, lacrado, defeitos e negociação.
5. **Radar e wishlist — implementada localmente:** consulta de anúncios ativos por edição, wishlist com preço-alvo, opt-in e alertas internos deduplicados, perfil opcional e solicitação privada de inclusão de jogo/edição.
6. **Aceite integrado — verificação local:** roteiro `scripts/check-user-flows-browser.mjs` com comprador, vendedor e moderador e testes Python de autorização, precedência e consentimento. Consulte o [estado consolidado e os limites](FLUXOS_USUARIO_LOCAL.md).

## Como usar a fase 1

Reinicie `npm start`, entre em `/conta` e abra **Meus anúncios** (`/anuncios`). Selecione uma edição cadastrada, preencha os dados e salve o rascunho. A edição e a remoção só são permitidas ao vendedor. Os registros pessoais de “Meus jogos” não viram anúncios automaticamente.

A cobertura continua nas edições preliminares dos 68 jogos editoriais. A biblioteca importada sem identidade de edição não ganha edições comerciais inventadas. As fases 2 e 3 permitem fotos, envio, aprovação e descoberta pública na instalação local. Não há pagamento nem envio externo de mensagens.

## Persistência e migrações

O banco é o mesmo `.local/accounts.sqlite3`. Tabelas novas são criadas de forma aditiva e idempotente, sem apagar usuários, sessões ou jogos pessoais. Há chaves estrangeiras, índices por edição/estado/preço e trilha de ações. Atualizações exigem a revisão atual para impedir sobrescrita de edição antiga. Preços aceitam apenas inteiros positivos em centavos.

Estados reservados no modelo: draft, pending_review, active, reserved, paused, sold, rejected, removed e expired. A fase 2 acrescenta envio, aprovação e rejeição com controle de revisão; cliente não escolhe arbitrariamente estado, vendedor ou papel privilegiado.

Nenhuma conta recebe moderação automaticamente. O operador local pode atribuir explicitamente com `python scripts/set-moderator.py EMAIL`, ou revogar com `--revoke`. A fila e as decisões com fotos já estão disponíveis na fase 2, sem autoaprovação. O papel não permite editar o texto de outro vendedor.

## Contratos locais da fase 1

- `GET /api/listings`: anúncios do usuário autenticado, inclusive removidos para consulta.
- `GET /api/listings?view=queue`: reservado à moderação.
- `POST /api/listings`: ações create, update e remove; validação, sessão e origem iguais à aplicação.
- Na fase 2, submit exige foto e revisão atual; approve/reject exigem moderador, justificativa, estado pendente e revisão atual. Fotos são enviadas e lidas por `/api/listing-images`, com sessão e validação.

Esta é a primeira entrega incremental, não o aceite completo do marketplace descrito nos DOCX.
