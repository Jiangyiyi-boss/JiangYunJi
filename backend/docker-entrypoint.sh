#!/bin/bash
set -e

# 等待 MySQL 就绪（最多等 60 秒）
echo "Waiting for MySQL..."
for i in $(seq 1 30); do
  if python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('${DB_HOST:-mysql}', ${DB_PORT:-3306})); s.close()" 2>/dev/null; then
    echo "MySQL is ready"
    break
  fi
  echo "  ...waiting ($i/30)"
  sleep 2
done

# 等待 RabbitMQ 就绪（非关键，快速尝试）
echo "Waiting for RabbitMQ..."
for i in $(seq 1 10); do
  if python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('${RABBITMQ_HOST:-rabbitmq}', ${RABBITMQ_PORT:-5672})); s.close()" 2>/dev/null; then
    echo "RabbitMQ is ready"
    break
  fi
  sleep 2
done

echo "Starting backend..."
exec "$@"
