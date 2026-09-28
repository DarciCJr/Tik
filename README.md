# Tik — Automação de postagem no TikTok com IA

Serviço próprio para gerar e publicar conteúdo no TikTok automaticamente,
rodando na mesma infra dos outros projetos (Docker + `rede-vps` + Apache
reverse proxy + Cloudflare Tunnel).

## Status

Projeto em bootstrap. Ver `PLAN.md` para o roadmap e `docs/DEPLOY.md` para
como plugar no seu ambiente (WSL2 + Apache + cloudflared).

## Por que não é "postar 100% sozinho" desde o dia 1

A API oficial do TikTok (Content Posting API) exige:

1. Cadastro do app no TikTok for Developers + Login Kit.
2. Revisão do app pela TikTok para sair do modo "unaudited".
3. Enquanto não auditado, posts vão como **rascunho privado** no app do
   usuário (ele precisa abrir o TikTok e publicar manualmente) — não é
   possível publicar direto no feed sem essa auditoria.

Então o fluxo real é:

- Fase 1 (agora): pipeline gera o vídeo + legenda + hashtags com IA e
  envia como rascunho via API oficial (ou deixa pronto numa pasta pra
  você revisar/postar). Zero risco de ban de conta.
- Fase 2 (depois de aprovado no TikTok for Developers): publicação direta
  automática.

Não vamos implementar login/automação via navegador (Selenium/Playwright
simulando o app) para *publicar* — isso viola os Termos de Uso do TikTok e
é o tipo de "bot" que gera banimento em massa. Vamos usar a API oficial.
