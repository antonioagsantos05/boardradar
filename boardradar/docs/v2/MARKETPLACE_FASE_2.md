# Marketplace — fase 2 entregue

## Uso

1. Reinicie `npm start`, entre em sua conta e acesse **Meus anúncios**.
2. Salve o anúncio, adicione pelo menos uma foto e clique em **Enviar para revisão**.
3. Uma conta diferente, com permissão de moderador, abre `/moderacao`, confere os dados e as fotos, informa justificativa e aprova ou rejeita.
4. O vendedor consulta o resultado e a justificativa em “Meus anúncios”. Editar texto, preço, edição ou fotos devolve o anúncio a rascunho; é necessário reenviar e revisar novamente.

O anúncio aprovado recebe estado `active`. A descoberta pública, a seção na ficha do jogo e os estados reservado/vendido pertencem à fase 3. Nenhum jogo pessoal vira anúncio automaticamente.

## Moderador local

Crie uma segunda conta pela interface e use o terminal na pasta do projeto:

```powershell
..\.tools\python-3.13.7\python.exe scripts/set-moderator.py moderador@exemplo.com
```

Ou use `python` caso esteja no PATH. Para revogar, acrescente `--revoke`. A atribuição é explícita e local, sem promoção automática pelo cadastro e sem escolha de papel pela API. O vendedor não pode revisar o próprio anúncio, mesmo que tenha permissão de moderador. A tela “Meus anúncios” apresenta o link da moderação quando a conta possui esse papel.

## Fotos e persistência

- Até seis fotos por anúncio; JPEG, PNG e WebP estáticos, até 5 MB e 16 megapixels de entrada.
- O servidor decodifica, limita a dimensão a 1600 × 1600, orienta a foto e gera novo JPEG sem copiar metadados, com saída limitada a 2 MB. Formato declarado não basta: o conteúdo deve ser decodificável e permitido. SVG e animações não são aceitos.
- As fotos ficam como BLOBs no banco local de contas, fora de `public/`. Nome de arquivo e caminhos enviados pelo cliente não são utilizados.
- Leitura exige sessão de proprietário ou moderador, mesmo quando aprovado nesta fase. Respostas de imagem são privadas, sem cache e com Content-Type fixo e nosniff.
- A migração 2 é aditiva. Fazer backup de `.local/accounts.sqlite3` com a aplicação parada também preserva as fotos. O banco de índice de busca continua separado.
- Há limite de três processamentos simultâneos de imagem e um por sessão. Não foi integrado antivírus nesta versão local; decodificação e nova codificação não são apresentadas como certificação de segurança.

O processamento usa [Sharp](https://sharp.pixelplumbing.com/api-constructor/), registrado como dependência direta e com versão fixa no lockfile.

## Revisão e consistência

O envio exige foto e estado elegível. A decisão exige permissão de moderação, outro vendedor, estado pendente e revisão atual. A aprovação exige conferência explícita da identidade da edição nas fotos; a justificativa é obrigatória para aprovação e rejeição e fica na auditoria. A aprovação do anúncio não transforma uma edição preliminar do catálogo em fonte oficialmente verificada.

Mudanças de fotos ou conteúdo incrementam a revisão e retiram o anúncio da fila/estado ativo. Uma decisão com revisão antiga é recusada. Rejeitados podem ser corrigidos e reenviados. Contas comuns não leem a fila e não aprovam ou rejeitam.

## Verificação

Testes Python cobrem estados, autorização, foto obrigatória, limite de fotos, revisão antiga, autoaprovação, justificativa, rejeição e reenvio. Execute `node scripts/test-python.mjs`.

O fluxo real de navegador está em `node scripts/check-marketplace-phase2-browser.mjs`, com banco isolado em `.qa/`: cobre conta e rascunho, upload, leitura privada, arquivo falso, remoção de EXIF/ICC, moderação com duas contas, aprovação/rejeição, invalidação por edição e layout móvel. O script atribui o papel somente à conta de teste no banco isolado.
