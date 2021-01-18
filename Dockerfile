FROM clearlinux:latest  AS builder

ARG dumb_init_version=1.2.4
ARG swupd_args
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
 && swupd os-install -V ${VERSION_ID} \
    --path /install_root --statedir /swupd-state \
    --bundles=haproxy,clr-network-troubleshooter,inotify-tools,iproute2  \
    --no-boot-update \
# Install dumb-init
 && mkdir -p /install_root/usr/local/bin/ \
 && curl -s -o /install_root/usr/local/bin/dumb-init -L https://github.com/Yelp/dumb-init/releases/download/v${dumb_init_version}/dumb-init_${dumb_init_version}_amd64 \
 && chmod +x /install_root/usr/local/bin/dumb-init

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

RUN mkdir -p /usr/local/etc/haproxy

COPY docker-entrypoint.sh hitless_reload.sh /
COPY haproxy.cfg /usr/local/etc/haproxy

ENV HAPROXY_CONFIG_FILE="/usr/local/etc/haproxy/haproxy.cfg"
ENV HAPROXY_PID_FILE="/var/run/haproxy.pid"
ENV HAPROXY_HITLESS_RELOAD=""

VOLUME /usr/local/etc/haproxy

ENTRYPOINT ["/usr/local/bin/dumb-init", "--", "/docker-entrypoint.sh"]
CMD ["haproxy"]
