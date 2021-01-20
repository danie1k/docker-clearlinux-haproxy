#!/bin/env python
import collections
import os
import re
import signal
import subprocess
import sys
import textwrap
from threading import Timer
from types import FunctionType
from typing import Iterator

import docker

BLOCK_MARKER_BEGIN = "# docker-backend-begin"
BLOCK_MARKER_END = "# docker-backend-end"
HAPROXY_CONFIG_REGEX = fr"(?:{BLOCK_MARKER_BEGIN}((?:.*?\r?\n?)*){BLOCK_MARKER_END})+"


# Source: https://gist.github.com/walkermatt/2871026
def debounce(wait):  # noqa
    """Decorator that will postpone a functions
    execution until after wait seconds
    have elapsed since the last time it was invoked."""

    def decorator(func):
        def debounced(*_args, **_kwargs):
            def call_it():
                func(*_args, **_kwargs)

            try:
                debounced.t.cancel()
            except AttributeError:
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()

        return debounced

    return decorator


class Docker:
    docker_api: docker.APIClient
    network_name: str

    Container = collections.namedtuple("Container", "ip hostname")

    def __init__(self, network_name: str) -> None:
        self.docker_api = docker.APIClient(base_url=os.environ["DOCKER_API_BASE_URL"])
        self.network_name = network_name

    def get_containers(self) -> Iterator[Container]:
        for container in self.docker_api.inspect_network(net_id=self.network_name)["Containers"].values():
            yield Docker.Container(container["IPv4Address"].split("/", 1)[0], container["Name"])

    def listen_network_changes(self, callback: FunctionType) -> None:
        filters = {
            "type": "network",
            "network": self.network_name,
            "event": ["connect", "disconnect"],
        }

        for event in self.docker_api.events(filters=filters, decode=True):
            callback(event)


class HaProxy:
    config_path: str
    domain_name: str

    def __init__(self, config_path: str, domain_name: str) -> None:
        self.config_path = config_path
        self.domain_name = domain_name

    def docker_to_backend(self, container: Docker.Container, indent: int = 2) -> str:
        return textwrap.indent(
            textwrap.dedent(
                """
                server      {hostname}  {ip}:80  weight 0
                use-server  {hostname}  if {{ req.hdr(host) -i "{hostname}.{domain_name}" }}
                """
            ).format(domain_name=self.domain_name, **container._asdict()),
            (" " * indent),
        )

    def generate_new_config(self, *containers: Docker.Container) -> str:
        with open(self.config_path, "r") as fobj:
            haproxy_config = fobj.read()

        backend_servers = "\n".join(self.docker_to_backend(container) for container in containers)
        new_backend_block = f"{BLOCK_MARKER_BEGIN}\n" f"{backend_servers}\n" f"{BLOCK_MARKER_END}"

        return re.sub(HAPROXY_CONFIG_REGEX, new_backend_block, haproxy_config, 1)

    def gracefuly_reload_haproxy(self) -> None:
        print("HA-Proxy configuration changed, reloading", flush=True)

        haproxy_pid_file = os.environ["HAPROXY_PID_FILE"]
        assert os.path.exists(
            haproxy_pid_file
        ), "Cannot find PID FILE {haproxy_pid_file}! Did you forget to add -W flag to haproxy command?"

        # Verify configuration
        result = subprocess.run(["haproxy", "-c", "-f", os.environ["HAPROXY_CONFIG_FILE"]], check=False)
        assert result.returncode == 0, "Unable to reload HA-Proxy due to configuration file errors!"

        # Reload HA-Proxy
        with open(haproxy_pid_file, "r") as fobj:
            pid = int(fobj.read().strip())
        os.kill(pid, signal.SIGUSR2)

    def write_haproxy_config(self, config: str) -> None:
        with open(self.config_path, "w") as fobj:
            fobj.truncate(0)
            fobj.write(config)


if __name__ == "__main__":
    d = Docker(network_name=os.environ["NETWORK_NAME"])
    h = HaProxy(
        config_path=os.environ["HAPROXY_CONFIG_FILE"],
        domain_name=os.environ["DOMAIN_NAME"],
    )

    @debounce(10)
    def tick(_unused) -> None:
        containers = d.get_containers()
        config = h.generate_new_config(*containers)
        h.write_haproxy_config(config)
        h.gracefuly_reload_haproxy()

    try:
        print("Docker networks monitor started!", flush=True)
        d.listen_network_changes(tick)
    finally:
        print("Docker networks monitor exited unexpectedly!", flush=True)
        sys.exit(1)
