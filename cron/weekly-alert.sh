#!/bin/bash

/usr/bin/docker run --rm --name link-watcher -v /link-watcher/volumes/watcher:/tmp/watcher --env-file /link-watcher/.env --entrypoint "python3" link-watcher alert.py -d /tmp/watcher/ -f /tmp/watcher/hosts.json