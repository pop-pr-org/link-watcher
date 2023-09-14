#!/bin/bash

/usr/bin/docker run --rm --name link-watcher -v /docker/link-watcher/volumes/watcher:/tmp/watcher --env-file /docker/link-watcher/.env registry.pop-pr.rnp.br/library/link-watcher:$(grep -oP '^VERSION=\K.*' /docker/link-watcher/.env)