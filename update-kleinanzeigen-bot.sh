#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON="$SCRIPT_DIR/.venv/bin/python"
REPOSITORY="https://github.com/Second-Hand-Friends/kleinanzeigen-bot.git"
REVISION="e57f8f67af6114fb147ff04fb1eaa6a7a502bf4b"

if [ ! -x "$PYTHON" ]; then
  echo "Error: .venv/bin/python not found. Create the virtual environment first." >&2
  exit 1
fi

"$PYTHON" -m pip install --upgrade -r "$SCRIPT_DIR/requirements-kleinanzeigen.txt"

# Plain pip installs skip the project's PDM post-install hook. Apply the
# matching upstream nodriver compatibility patch from the pinned revision.
PATCH_DIR=$(mktemp -d "${TMPDIR:-/tmp}/kleinanzeigen-bot-patch.XXXXXX")
trap 'rm -rf "$PATCH_DIR"' EXIT HUP INT TERM
git clone --quiet --filter=blob:none --no-checkout "$REPOSITORY" "$PATCH_DIR/repository"
git -C "$PATCH_DIR/repository" show \
  "$REVISION:scripts/fix_nodriver.py" > "$PATCH_DIR/fix_nodriver.py"
"$PYTHON" "$PATCH_DIR/fix_nodriver.py"

"$PYTHON" -m kleinanzeigen_bot version
