#!/bin/sh

set -e
set -x

pytest \
    --cov . \
    --cov-report xml \
    --no-cov-on-fail \
    tests

coverage report --show-missing
