# Freeze the scryme backend into a standalone binary inside a container — no host Python needed.
#
# Build context is the repo root so both backend/ and desktop/ are available:
#   docker build -f desktop/backend.Dockerfile --target export \
#     --output type=local,dest=desktop/dist .
# That writes desktop/dist/scryme-backend/ (the exe + its _internal libs), which electron-builder
# bundles into the app under resources/backend/.
#
# Built on Debian bookworm (glibc 2.36) so the binary runs on any Linux with glibc >= 2.36.
FROM python:3.12-slim-bookworm AS build

# binutils gives PyInstaller objdump/strip for dependency analysis.
RUN apt-get update && apt-get install -y --no-install-recommends binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY backend /work/backend
COPY desktop/backend.spec /work/desktop/backend.spec

RUN pip install --no-cache-dir -r backend/requirements.txt pyinstaller==6.11.1

WORKDIR /work/desktop
RUN pyinstaller --noconfirm --clean backend.spec

# Export stage: a scratch image whose entire filesystem is just the frozen bundle, so
# `--output type=local` drops desktop/dist/scryme-backend/ onto the host with nothing else.
FROM scratch AS export
COPY --from=build /work/desktop/dist/scryme-backend /scryme-backend
