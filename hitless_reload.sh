#!/bin/bash
set -eu

echo "[HITLESS-RELOAD] Hitless reload enabled."

_reload() {
  while read _unused; do
    if [[ $(haproxy -c -f "$HAPROXY_CONFIG_FILE") ]]
    then
      echo "[HITLESS-RELOAD] HA-Proxy configuration changed, reloading."
      kill -SIGUSR2 $(cat "$HAPROXY_PID_FILE") >/dev/null 2>&1 || true
    else
      echo "[HITLESS-RELOAD] Unable to reload HA-Proxy due to configuration file errors!"
    fi
  done
}

inotifywait -e close_write --format %f -m -q "$HAPROXY_CONFIG_FILE" | _reload

echo "[HITLESS-RELOAD] inotifywait exited unexpectedly!" >&2
