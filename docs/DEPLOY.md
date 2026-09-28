# Deploy no seu ambiente (WSL2 + Apache + Cloudflare Tunnel)

Assumindo o mesmo padrão dos outros subdomínios (`evolution`, `home`,
`terminal`).

## 1. Subir o container

```bash
cd /caminho/do/projeto/Tik
cp .env.example .env
# preencher .env com as chaves reais
docker compose up -d --build
```

Isso sobe o `tik-api` escutando em `127.0.0.1:8090`, na rede `rede-vps`.

## 2. Vhost Apache

Criar `/etc/apache2/sites-available/tik.topachadinhos.com.br.conf`:

```apache
<VirtualHost *:80>
    ServerName tik.topachadinhos.com.br

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8090/
    ProxyPassReverse / http://127.0.0.1:8090/

    ErrorLog ${APACHE_LOG_DIR}/tik_error.log
    CustomLog ${APACHE_LOG_DIR}/tik_access.log combined
</VirtualHost>
```

Importante: o TikTok vai chamar `GET /oauth/callback` como redirect do
navegador do usuário (você) e não precisa de webhook externo sem auth,
mas **não** coloque esse subdomínio atrás do Basic Auth do site
principal, senão o redirect do OAuth quebra (o TikTok não sabe preencher
usuário/senha do `.htpasswd`).

```bash
sudo a2ensite tik.topachadinhos.com.br.conf
sudo systemctl reload apache2
```

## 3. Cloudflare Tunnel

Em `/etc/cloudflared/config.yml`, adicionar uma entrada de `ingress`
antes do catch-all final:

```yaml
  - hostname: tik.topachadinhos.com.br
    service: http://localhost:80
```

E criar o registro DNS (CNAME apontando pro túnel), como fez para os
outros subdomínios:

```bash
cloudflared tunnel route dns <nome-do-tunnel> tik.topachadinhos.com.br
sudo systemctl restart cloudflared
```

## 4. TikTok for Developers

1. Criar app em https://developers.tiktok.com/apps
2. Adicionar produto "Login Kit" e "Content Posting API"
3. Redirect URI: `https://tik.topachadinhos.com.br/oauth/callback`
4. Copiar `client_key` e `client_secret` pro `.env`
5. Enquanto o app não for auditado, os vídeos publicados via API caem
   como rascunho no inbox do TikTok do usuário — normal nessa fase.

## 5. Deploy automático (GitHub Actions self-hosted runner)

Seguir o mesmo padrão dos outros projetos: workflow que faz rsync dos
arquivos pra pasta do projeto na VPS e roda `docker compose up -d --build`
depois do push na branch principal.
