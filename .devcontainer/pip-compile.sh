#!/usr/bin/env bash

set -ex

pip install pip-tools

cd requirements
echo ipykernel >> /tmp/requirements.txt
pip-compile --verbose \
   --output-file /tmp/output.txt \
   skinny-requirements.txt \
   core-requirements.txt \
   doc-min-requirements.txt \
   test-requirements.txt \
   lint-requirements.txt \
   /tmp/requirements.txt

# Add a timestamp at the beginning of the file
echo "# Created at: $(date -u +"%F %T %Z")" | cat - /tmp/output.txt > /tmp/requirements.txt
