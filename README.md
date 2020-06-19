# alerta-web-addon
Web service with UI for control new alerta zulip plugin, based on Flask and Flask-Bootstrap

#### RUN
`python server.py --dbstring ... --port ...`

or by playbook: 
 
`ansible-playbook -i inventory/prod prepare_host.yml`
  
 next variable should be set:
- worker_address
- worker_key
- export DATABASE_URL
##### server args:
- `--port` by default = 23456
- `--dbstring` postgresql://...
- `--debug` by default=False