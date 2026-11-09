#!/bin/bash
set -euo pipefail

mkdir -p /run/ssh-shared /home/pipeline/.ssh /root/.ssh
chmod 700 /home/pipeline/.ssh /root/.ssh
if [[ ! -s /run/ssh-shared/id_ed25519 ]]; then
  ssh-keygen -q -t ed25519 -N "" -f /run/ssh-shared/id_ed25519
fi
cp /run/ssh-shared/id_ed25519.pub /run/ssh-shared/authorized_keys
chmod 600 /run/ssh-shared/id_ed25519
chmod 644 /run/ssh-shared/id_ed25519.pub /run/ssh-shared/authorized_keys
ln -sf /run/ssh-shared/authorized_keys /home/pipeline/.ssh/authorized_keys
if [[ ! -s /etc/ssh/ssh_host_ed25519_key ]]; then
  ssh-keygen -q -t ed25519 -N "" -f /etc/ssh/ssh_host_ed25519_key
fi
cat > /root/.ssh/config <<'EOF'
Host localhost
  User pipeline
  IdentityFile /run/ssh-shared/id_ed25519
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
EOF
chmod 600 /root/.ssh/config
sshd

dataset_file="${DATASET_FILE:?DATASET_FILE is required}"
output_dir="${OUTPUT_DIR:-/data/output}"
mkdir -p "$output_dir"
rm -rf "$output_dir/resultado"
rm -f "$output_dir/pipeline.done"

echo "=== Hadoop standalone ==="
hadoop version
echo "=== SSH localhost (llave sin contraseña) ==="
ssh -o BatchMode=yes localhost 'printf "SSH localhost OK\\n"'

echo "=== Comparativa secuencial ==="
start=$SECONDS
python3 /app/mapreduce/secuencial.py "$dataset_file" "$output_dir/secuencial.tsv"
sequential_seconds=$((SECONDS - start))
echo "Tiempo secuencial: ${sequential_seconds}s"

echo "=== Hadoop Streaming ==="
streaming_jar="$(find "$HADOOP_HOME/share/hadoop/tools/lib" -maxdepth 1 -name 'hadoop-streaming-*.jar' -print -quit)"
if [[ -z "$streaming_jar" ]]; then
  echo "No se encontro el jar de Hadoop Streaming" >&2
  exit 1
fi
start=$SECONDS
hadoop jar "$streaming_jar" \
  -D mapreduce.framework.name=local \
  -D fs.defaultFS=file:/// \
  -D mapreduce.job.reduces=1 \
  -input "$dataset_file" \
  -output "$output_dir/resultado" \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -files /app/mapreduce/mapper.py,/app/mapreduce/reducer.py
hadoop_seconds=$((SECONDS - start))
echo "Tiempo Hadoop Streaming: ${hadoop_seconds}s"

part_file="$output_dir/resultado/part-00000"
if ! cmp -s "$output_dir/secuencial.tsv" "$part_file"; then
  echo "ERROR: La salida de Hadoop no coincide con la secuencial" >&2
  diff -u "$output_dir/secuencial.tsv" "$part_file" || true
  exit 1
fi
echo "Verificacion: ambas salidas coinciden"

echo "=== Carga a PostgreSQL ==="
python3 /app/scripts/cargar_resultados.py "$part_file"
touch "$output_dir/pipeline.done"
echo "Pipeline listo; SSH disponible en hadoop:22"
exec tail -f /dev/null