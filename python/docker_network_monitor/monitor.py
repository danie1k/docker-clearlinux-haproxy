#!/bin/env python
import collections
import glob
import os
import pathlib
import signal
import subprocess
import sys
import textwrap
from threading import Timer
from types import FunctionType
from typing import Any, Dict, Iterable, Iterator

import docker
import jinja2

CWD = pathlib.Path(__file__).parent
HAPROCY_CONFIG_ANCHOR = "# DOCKER_NETWORK_MONITOR_ANCHOR"


# Source: https://gist.github.com/walkermatt/2871026
def debounce(wait: int):  # type:ignore # noqa
    """Decorator that will postpone a functions
    execution until after wait seconds
    have elapsed since the last time it was invoked."""

    def decorator(func):  # type:ignore
        def debounced(*_args: Any, **_kwargs: Any) -> None:
            def call_it() -> None:
                func(*_args, **_kwargs)

            try:
                debounced.t.cancel()  # type:ignore
            except AttributeError:
                pass
            debounced.t = Timer(wait, call_it)  # type:ignore
            debounced.t.start()  # type:ignore

        return debounced

    return decorator


class Docker:
    docker_api: docker.APIClient
    network_name: str

    Container = collections.namedtuple("Container", "ip hostname labels")

    def __init__(self, network_name: str) -> None:
        self.docker_api = docker.APIClient(base_url=os.environ["DOCKER_API_BASE_URL"])
        self.network_name = network_name

    def get_containers(self) -> Iterator[Container]:
        for container in self.docker_api.inspect_network(net_id=self.network_name)["Containers"].values():
            detailed_container = self.docker_api.inspect_container(container["Name"])

            labels = detailed_container["Config"]["Labels"]
            if not ("haproxy.source_port" in labels and "haproxy.target_port" in labels):
                print(f"WARNING Skipping container '{container['Name']}' sue to missing labels!", flush=True)
                continue

            yield Docker.Container(
                ip=container["IPv4Address"].split("/", 1)[0],
                hostname=container["Name"],
                labels=detailed_container["Config"]["Labels"],
            )

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

    def generate_new_config(self, containers: Iterable[Docker.Container], template_engine: "TemplateEngine") -> str:
        with open(self.config_path, "r") as fobj:
            lines = map(lambda line: line.strip("\n\r"), fobj.readlines())

        config_string = []
        for item in lines:
            config_string.append(item)
            if item == HAPROCY_CONFIG_ANCHOR:
                config_string.append(os.linesep)
                break
        result = os.linesep.join(config_string)

        for container in containers:
            template = template_engine.get_template(container)
            result += template_engine.render_template(template, container) + os.linesep

        return result

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


class TemplateEngine:
    available_templates: Dict[str, pathlib.Path]

    def __init__(self) -> None:
        self.available_templates = {
            pathlib.Path(item).stem: pathlib.Path(item) for item in glob.glob(str(CWD / "templates" / "*.j2"))
        }

    def get_template(self, container: Docker.Container) -> jinja2.Template:
        template_file: pathlib.Path = self.available_templates.get(
            container.labels.get("haproxy.source_port"), self.available_templates["default"]
        )
        return jinja2.Template(template_file.read_text("utf8"))

    def render_template(self, template: jinja2.Template, container: Docker.Container) -> str:
        template_variables = container._asdict()

        for label_name, value in container.labels.items():
            if label_name.startswith("haproxy."):
                template_variables[label_name.split(".", 1)[1]] = value

        return template.render(**template_variables)


if __name__ == "__main__":
    d = Docker(network_name=os.environ["NETWORK_NAME"])
    h = HaProxy(
        config_path=os.environ["HAPROXY_CONFIG_FILE"],
        domain_name=os.environ["DOMAIN_NAME"],
    )

    def tick() -> None:
        containers = d.get_containers()
        config = h.generate_new_config(containers, TemplateEngine())
        h.write_haproxy_config(config)
        h.gracefuly_reload_haproxy()

    @debounce(10)
    def debounced_tick(_unused: Dict[str, Any]) -> None:
        tick()

    # Build servers list on startup
    tick()

    try:
        print("Docker networks monitor started!", flush=True)
        d.listen_network_changes(debounced_tick)
    finally:
        print("Docker networks monitor exited unexpectedly!", flush=True)
        sys.exit(1)
