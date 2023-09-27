#!/bin/bash

/usr/bin/docker run --rm --name link-watcher -v /link-watcher/volumes/watcher:/tmp/watcher --env-file /link-watcher/.env link-watcher