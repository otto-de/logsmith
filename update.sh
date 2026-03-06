#!/usr/bin/env bash

uv sync
uv export --format requirements-txt > requirements.txt
