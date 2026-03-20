#!/bin/sh
set -eu

if [ -z "${NGINX_LOCAL_RESOLVERS:-}" ]; then
  NGINX_LOCAL_RESOLVERS="$(awk '/^nameserver / {print $2}' /etc/resolv.conf | paste -sd' ' -)"
  export NGINX_LOCAL_RESOLVERS
fi
