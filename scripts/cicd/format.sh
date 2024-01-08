#!/bin/sh

set -x

# Sort imports one per line, so autoflake can remove unused imports
isort --force-single-line-imports .
autoflake .
# Sort imports back
isort .
black .
