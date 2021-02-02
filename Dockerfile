FROM python:3.8

LABEL maintainer="Anton Sidelnikov <a.sidelnikov@t-systems.com>"
ENV web_server_port=23456

EXPOSE ${web_server_port}

# Update aptitude with new repo
RUN apt-get update
# Copy the conf files into the docker container
COPY . /alerta-web-addon
# Install requirements
RUN pip3 install -r alerta-web-addon/playbooks/files/requirements.txt
# Run app
CMD cd /alerta-web-addon && python -m alertawebaddon --port ${web_server_port}
