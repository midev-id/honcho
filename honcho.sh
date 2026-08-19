#!/usr/bin/env bash
# ============================================================
#  honcho.sh — control self-hosted Honcho server (Docker)
#  Usage:
#    ./honcho.sh start    # build + start semua container
#    ./honcho.sh stop     # stop container (data TETAP aman)
#    ./honcho.sh restart  # stop lalu start
#    ./honcho.sh status   # cek status container + health API
#    ./honcho.sh logs     # lihat log (api + deriver)
# ============================================================
set -euo pipefail

cd "$(dirname "$0")"

ACT="${1:-status}"
COMPOSE="docker compose"

# Poll /health sampai siap (maks ~30s) — beri pesan jelas kalau gagal.
wait_ready() {
  for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
      echo "✅ Honcho API ready: http://localhost:8000 (health ok)"
      return 0
    fi
    sleep 1
  done
  echo "⚠️  Container up tapi /health belum merespon dalam 30s — cek 'logs'."
  return 1
}

case "$ACT" in
  start)
    echo "▶️  Starting Honcho (build jika perlu)..."
    docker info >/dev/null 2>&1 || { echo "❌ Docker belum jalan. Buka Docker Desktop dulu."; exit 1; }
    $COMPOSE up -d --build
    wait_ready
    ;;
  stop)
    echo "⏹️  Stopping Honcho (data di volume Docker, tetap aman)..."
    $COMPOSE stop
    echo "✅ Stopped."
    ;;
  restart)
    echo "🔄 Restarting Honcho..."
    $COMPOSE restart
    wait_ready
    ;;
  status)
    echo "=== docker compose ps ==="
    $COMPOSE ps
    echo
    echo "=== API health ==="
    curl -s http://localhost:8000/health 2>&1 || echo "(API tidak merespon — mungkin belum start)"
    echo
    ;;
  logs)
    echo "=== API logs (tail) ==="
    $COMPOSE logs api --tail 30 2>&1 | grep -vE "^\s*$" | tail -30
    echo
    echo "=== Deriver logs (tail) ==="
    $COMPOSE logs deriver --tail 20 2>&1 | grep -vE "^\s*$" | tail -20
    ;;
  *)
    echo "Pakai: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac