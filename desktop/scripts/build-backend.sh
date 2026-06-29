#!/usr/bin/env bash
# Freeze the scryme backend into a self-contained binary with PyInstaller.
#
# Run from desktop/:  npm run build:backend
# Produces desktop/dist/scryme-backend/ (the exe + its _internal libs), which electron-builder
# bundles into the app under resources/backend/.
#
# Two build paths, auto-selected:
#   1. Docker (preferred) — freezes inside a Debian bookworm container. No host Python needed and
#      the binary is portable (glibc >= 2.36). Set SCRYME_BUILD_NO_DOCKER=1 to skip it.
#   2. Local interpreter — when Docker is unavailable. Uses, in order: $SCRYME_BUILD_PYTHON, a
#      throwaway venv at desktop/.build-venv (if `python3 -m venv` works), else $SCRYME_PYTHON /
#      python3 (must already have the backend requirements installed).
#
# PyInstaller output is platform-specific (no cross-compilation) — build on the OS you ship for.
# The Docker path produces a Linux binary; for macOS/Windows installers, run the local path on a
# Mac/Windows host.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
BACKEND="$REPO/backend"
VENV="$HERE/.build-venv"
PYINSTALLER_VERSION="6.11.1"

if [ -z "${SCRYME_BUILD_NO_DOCKER:-}" ] && command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "==> Freezing backend inside a container (no host Python needed)"
  rm -rf "$HERE/dist/scryme-backend"
  docker build -f "$HERE/backend.Dockerfile" --target export \
    --output "type=local,dest=$HERE/dist" "$REPO"
  echo "==> Done: $HERE/dist/scryme-backend/"
  exit 0
fi

echo "==> Docker unavailable; freezing with a local Python interpreter"
if [ -n "${SCRYME_BUILD_PYTHON:-}" ]; then
  PYTHON="$SCRYME_BUILD_PYTHON"
  echo "==> Using SCRYME_BUILD_PYTHON: $PYTHON"
elif python3 -m venv "$VENV" 2>/dev/null; then
  PYTHON="$VENV/bin/python"
  echo "==> Created build venv at $VENV"
else
  PYTHON="${SCRYME_PYTHON:-python3}"
  echo "==> venv unavailable (install python3-venv for an isolated build);"
  echo "    falling back to existing interpreter: $PYTHON"
  echo "    (it must already have the backend requirements installed)"
fi

echo "==> Ensuring backend requirements + PyInstaller in $PYTHON"
"$PYTHON" -m pip install --upgrade pip wheel >/dev/null
"$PYTHON" -m pip install -r "$BACKEND/requirements.txt"
"$PYTHON" -m pip install "pyinstaller==$PYINSTALLER_VERSION"

echo "==> Freezing backend (this can take a minute)"
cd "$HERE"
"$PYTHON" -m PyInstaller --noconfirm --clean backend.spec

echo "==> Done: $HERE/dist/scryme-backend/"
