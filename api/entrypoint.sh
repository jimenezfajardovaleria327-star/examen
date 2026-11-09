#!/bin/sh
set -eu
mkdir -p /root/.ssh
chmod 700 /root/.ssh
cp /run/ssh-shared/id_ed25519 /root/.ssh/id_ed25519
chmod 600 /root/.ssh/id_ed25519
cat > /root/.ssh/config <<'EOF'
Host hadoop
  User pipeline
  IdentityFile /root/.ssh/id_ed25519
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  BatchMode yes
EOF
chmod 600 /root/.ssh/config
attempt=0
until ssh pipeline@hadoop 'test -f /data/output/pipeline.done'; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 1800 ]; then
    echo "El pipeline Hadoop no termino dentro del limite de espera" >&2
    exit 1
  fi
  sleep 2
done
exec python /app/app.py