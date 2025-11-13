#!/bin/bash
# YouTube transcript extractor wrapper
# Allows usage: /youtube <url> or youtube <url>

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exec python3 "$SCRIPT_DIR/droid_slash_cli.py" /youtube "$@"
