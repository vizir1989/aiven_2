#!/bin/sh

set -e
set -x

isort --diff .
flake8 .
