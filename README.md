# alerta-web-addon
Web service with UI for control new alerta zulip plugin, based on Flask and Flask-Bootstrap

#### RUN
before run:
- export GITHUB_OAUTH_CLIENT_SECRET=some_secret
- export GITHUB_OAUTH_CLIENT_ID=some_id
- export APP_SECRET_KEY=anyone
- export DATABASE_URL=postgresql://...
- export OAUTHLIB_INSECURE_TRANSPORT=true (if not https)
- export PROXY_PREFIX_PATH=/some_location
- export GF_AUTH_GITHUB_ALLOWED_ORGANIZATIONS=some_org

`python server.py --port ...`

or by playbook: 
 
`ansible-playbook -i inventory/prod playbooks/prepare_host.yml`
  
 next ansible variables should be set:
- worker_address
- worker_key
- skip_nginx (false by default)
- proxy_prefix `if app runs under reverse proxy sub location`
- dns `dns record assigned to ip, for certbot`

##### server args:
- `--port` by default = 23456
- `--debug` by default=False