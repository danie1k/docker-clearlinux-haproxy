FROM clearlinux:latest AS builder

ARG swupd_args
ARG multirun_version=1.0.0

# Move to latest Clear Linux irelease to ensure
# that the swupd command line arguments are
# correct
RUN swupd update --no-boot-update $swupd_args \
 && swupd bundle-add curl

# Grab os-release info from the minimal base image so
# that the new content matches the exact OS version
COPY --from=clearlinux/os-core:latest /usr/lib/os-release /

# Install additional content in a target directory
# using the os version from the minimal base
RUN source /os-release \
 && mkdir /install_root \
 && swupd os-install -V $(cat /usr/lib/os-release | grep VERSION_ID | awk -F= '{print $2}') \
    --path /install_root --statedir /swupd-state \
    --bundles=haproxy,clr-network-troubleshooter,inotify-tools,iproute2,python3-basic \
    --no-boot-update \
# Download & install multirun
 && curl -s -o /tmp/multirun.tar.gz \
    -L https://github.com/nicolas-van/multirun/releases/download/${multirun_version}/multirun-glibc-${multirun_version}.tar.gz \
 && mkdir -p /install_root/usr/local/bin/ \
 && tar -zxvf /tmp/multirun.tar.gz -C /install_root/usr/local/bin/ \
 && chmod +x /install_root/usr/local/bin/multirun

# For some Host OS configuration with redirect_dir on,
# extra data are saved on the upper layer when the same
# file exists on different layers. To minimize docker
# image size, remove the overlapped files before copy.
RUN mkdir /os_core_install
COPY --from=clearlinux/os-core:latest / /os_core_install/
RUN cd / \
 && find os_core_install | sed -e 's/os_core_install/install_root/' | xargs rm -d &> /dev/null || true

FROM clearlinux/os-core:latest

COPY --from=builder /install_root /

COPY requirements.txt /

RUN mkdir -p $HAPROXY_CONFIG_VOLUME /docker_network_monitor \
# Install Python requirements
 && pip install -r /requirements.txt

COPY python/docker_network_monitor/ /docker_network_monitor/
COPY haproxy.cfg /usr/local/etc/haproxy/

ENV DOCKER_API_BASE_URL="unix:///var/run/docker.sock"
ENV DOMAIN_NAME="local"
ENV HAPROXY_CONFIG_VOLUME="/usr/local/etc/haproxy"
ENV HAPROXY_PID_FILE="/var/run/haproxy.pid"
ENV NETWORK_MONITOR_DEBOUNCE="10"
ENV NETWORK_NAME="bridge"

VOLUME $HAPROXY_CONFIG_VOLUME
VOLUME /var/run/docker.sock

ENTRYPOINT ["/usr/local/bin/multirun"]
CMD ["echo 'You need to manually specify command for this Docker Container!'", "false"]
