# Plano — Tik (postagem automática TikTok + IA)

## Objetivo de negócio
Faturar com TikTok publicando conteúdo em volume, com qualidade suficiente
pra reter audiência, usando geração de conteúdo por IA + automação de
publicação — sem violar os Termos de Uso (o que levaria a shadowban/ban).

## Arquitetura (na sua VPS/WSL2)

```
Internet ──Cloudflare Tunnel──> Apache (WSL2) ──ProxyPass──> container "tik-api" (porta local, ex 8090)
                                                                    │
                                                            rede-vps (docker network)
                                                                    │
                                              outros containers (ex: banco, redis, evolution)
```

- Subdomínio sugerido: `tik.topachadinhos.com.br` (fora do Basic Auth do
  site principal, porque o TikTok vai chamar callbacks/webhooks nesse
  domínio para o OAuth redirect).
- Container Docker próprio (`tik-api`), na rede `rede-vps` externa.
- Persistência: SQLite/Postgres simples pra guardar contas, tokens OAuth,
  fila de posts, histórico. Comece com SQLite (arquivo em volume), migra
  pra Postgres se precisar escalar.

## Módulos do app (`app/`)

- `api/` — FastAPI: endpoints de OAuth callback do TikTok, endpoints
  internos pra disparar geração/publicação, healthcheck.
- `tiktok/` — cliente da Content Posting API (auth, refresh token, upload
  de vídeo, criação de post/rascunho, consulta de status).
- `content/` — pipeline de geração de conteúdo:
  - roteiro/legenda via LLM (Claude API)
  - texto-pra-voz (TTS) se for vídeo narrado
  - montagem de vídeo (ex: ffmpeg + templates, ou remix de clipes)
  - hashtags/SEO de legenda
- `scheduler/` — fila de publicação (ex: APScheduler ou Celery+Redis) —
  decide quando cada vídeo vai pro TikTok, evita padrão robótico
  (horários variados, intervalo mínimo entre posts).
- `storage/` — vídeos gerados, thumbnails, assets, cache local (volume
  Docker mapeado, fora do container).
- `core/` — config, logging, segurança (guardar tokens TikTok
  criptografados, não em texto puro).

## Roadmap

1. **Bootstrap (agora)**
   - Scaffold do projeto, Dockerfile, docker-compose no padrão da sua
     infra, healthcheck endpoint.
   - Cadastro do app em https://developers.tiktok.com (Login Kit +
     Content Posting API) — isso você faz manualmente, eu ajudo a
     configurar o redirect URI = `https://tik.topachadinhos.com.br/oauth/callback`.
2. **OAuth + conta conectada**
   - Fluxo de login TikTok, guardar access/refresh token por conta.
   - Endpoint pra listar contas conectadas.
3. **Pipeline de conteúdo (fase que já dá pra rodar sem aprovação do TikTok)**
   - Gerar roteiro/legenda com IA a partir de um "tema"/nicho.
   - Gerar ou montar vídeo.
   - Salvar em fila local pra revisão.
4. **Publicação via API (modo rascunho, enquanto app não auditado)**
   - Upload do vídeo + criação de post como draft.
   - Você abre o TikTok no celular e confirma a publicação (ainda manual
     nessa etapa, mas o trabalho pesado — criar o conteúdo — já é 100%
     automático).
5. **Auditoria do app no TikTok for Developers**
   - Depois que o app for aprovado: mudar o client pra usar publicação
     direta (sem draft), habilitar `scheduler` pra rodar sozinho.
6. **Deploy no seu ambiente**
   - Dockerfile + compose, vhost Apache, entrada no `cloudflared/config.yml`.
   - Deploy automático via GitHub Actions self-hosted runner (mesmo padrão
     dos outros projetos).

## Decisões em aberto (preciso da sua confirmação conforme chegamos lá)
- Quantas contas TikTok você pretende operar? (1 conta bem cuidada é bem
  mais seguro que várias — múltiplas contas do mesmo dono/IP podem ser
  linkadas e banidas em conjunto pelo TikTok)
- Nicho/tema do conteúdo (afeta o pipeline de geração: vídeo falado,
  compilação, texto na tela, etc.)
- Qual LLM/API de geração de vídeo usar (ex: Claude pra roteiro, e pra
  vídeo: algo como um serviço de TTS + assets, ou vídeos com clipes
  próprios/stock)
