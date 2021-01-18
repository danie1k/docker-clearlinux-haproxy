#!/bin/bash
set -eu

# first arg is `-f` or `--some-option`
if [ "${1#-}" != "$1" ]
then
  set -- haproxy "$@"
fi

if [ "$1" = 'haproxy' ]
then
  shift # "haproxy"
  # if the user wants "haproxy", let's add a couple useful flags
  #   -W  -- "master-worker mode" (similar to the old "haproxy-systemd-wrapper"; allows for reload via "SIGUSR2")
  #   -p  -- writes pids of all children to this file
  #   -db -- disables background mode
  if [ "$HAPROXY_HITLESS_RELOAD" = '' ]
  then
    set -- haproxy -db -p "$HAPROXY_PID_FILE" -f "$HAPROXY_CONFIG_FILE" "$@"
  else
    set -- haproxy -W -db -p "$HAPROXY_PID_FILE" -f "$HAPROXY_CONFIG_FILE" "$@"

    /hitless_reload.sh &
  fi
fi

if [ "$HAPROXY_HITLESS_RELOAD" = '' ]
then
  exec "@"
else
  "$@" &
  wait -n
fi
