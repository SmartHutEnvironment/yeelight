#!/bin/sh

TARGET_DIR="/data";

if [ -z "$(ls -A ${TARGET_DIR})" ]; then
   cp -r /data-template/* /data/
fi