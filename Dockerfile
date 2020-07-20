FROM python:3.8

LABEL maintainer="Anton Sidelnikov <a.sidelnikov@t-systems.com>"
ENV web_server_port=23456

# Update aptitude with new repo
RUN apt-get update
# Install software
RUN apt-get install -y git
# Clone the conf files into the docker container
RUN git clone https://github.com/opentelekomcloud-infra/alerta-web-addon.git
# Install requirements
RUN pip3 install -r alerta-web-addon/playbooks/files/requirements.txt
# Run app
CMD cd /alerta-web-addon && python -m alertawebaddon --port ${web_server_port}