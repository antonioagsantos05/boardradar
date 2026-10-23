# Publicar no Render: site e Python juntos

1. Envie `Dockerfile`, `.dockerignore`, `scripts/run.mjs`, a rota `src/app/api/health/route.ts` e as demais mudanças do projeto ao GitHub.
2. No Render, crie **Web Service**, conecte o repositório e selecione **Docker** em Language/Runtime.
3. Se o repositório contém a pasta `boardradar`, defina **Root Directory: boardradar**. Se package.json está na raiz do repositório, deixe Root Directory vazio.
4. Com essa raiz selecionada, **Dockerfile Path: ./Dockerfile** e **Docker Build Context: .**. Não sobrescreva Docker Command; o Dockerfile já inicia ambos os serviços.
5. Em Health Check Path, use `/api/health`.
6. Para manter contas, anúncios, mensagens e fotos, adicione um disco persistente montado em **/var/data**. As fotos ficam no próprio SQLite. O Dockerfile já configura `RADAR_ACCOUNT_DB=/var/data/accounts.sqlite3`.
7. Publique. O primeiro acesso terá um banco novo; os dados do seu computador não são enviados automaticamente. As preferências de localStorage também ficam associadas ao domínio acessado.

O Next.js recebe tráfego em `0.0.0.0:$PORT`; o Python permanece privado em loopback com token interno gerado ao iniciar. O serviço falha se o Python não iniciar ou encerrar durante a execução, para permitir a recuperação pela hospedagem. Use apenas uma instância enquanto o banco for SQLite local.

O disco persistente exige serviço pago no Render. Para testar sem disco, o site inicia, mas os dados locais podem ser perdidos em reinícios e novos deploys. Não defina manualmente `RADAR_CHAT_URL` ou `RADAR_CHAT_TOKEN`: o iniciador configura ambos.

## Testar com Docker instalado

```powershell
docker build -t boardradar .
docker run --rm -p 3001:10000 -v boardradar-data:/var/data boardradar
```

Abra http://localhost:3001 e verifique http://localhost:3001/api/health. O volume nomeado preserva o banco entre execuções. O build da imagem requer Docker; não foi possível executá-lo no computador de desenvolvimento sem esse programa instalado.

Referências: https://render.com/docs/docker e https://render.com/docs/disks
