[![QA Build Status](https://travis-ci.com/danie1k/homelab-haproxy.svg?branch=master)](https://travis-ci.com/danie1k/homelab-haproxy)
[![Docker Hub Build Status](https://img.shields.io/docker/cloud/build/danie1k/homelab-haproxy)](https://hub.docker.com/repository/docker/danie1k/homelab-haproxy)
[![Docker Image Version](https://img.shields.io/docker/v/danie1k/homelab-haproxy)](https://hub.docker.com/repository/docker/danie1k/homelab-haproxy)
[![MIT License](https://img.shields.io/github/license/danie1k/homelab-haproxy)](https://github.com/danie1k/homelab-haproxy/blob/master/LICENSE)

# Automated HA-Proxy for Docker containers

Based on https://github.com/clearlinux/dockerfiles/tree/master/haproxy

**The idea behind this container is to**

- Monitor changes in certain given Docker Network
- React when containers connect/disconnect to this network
- Automatically map names of these containers in HA-Proxy to FQDNs


## Usage

- Run this container at least in two Docker Networks.
- By default, it will listen for requests on `eth0`, so make your end-user-facing network to be first on a list.
- Monitoring tool will automatically modify HA-Proxy settings
- If any new container will show up, it will be added to configuration **if it has the following labels set**:
    - `haproxy.source_port`
    - `haproxy.target_port`


## Environment variables

- `DOCKER_API_BASE_URL="unix:///var/run/docker.sock"`
- `HAPROXY_CONFIG_FILE="/usr/local/etc/haproxy/haproxy.cfg"`
- `HAPROXY_PID_FILE="/var/run/haproxy.pid"`
- `DOMAIN_NAME="local"`
- `NETWORK_NAME="bridge"`


## Volumes

- `/usr/local/etc/haproxy`
- `/var/run/docker.sock`
