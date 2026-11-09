FROM debian:bookworm-slim

ARG HADOOP_VERSION=3.4.1
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    HADOOP_HOME=/opt/hadoop \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:/opt/venv/bin:$PATH \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl openssh-client openssh-server openjdk-17-jre-headless \
      python3 python3-venv && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir psycopg2-binary==2.9.10 && \
    curl -fsSL "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" -o /tmp/hadoop.tar.gz && \
    tar -xzf /tmp/hadoop.tar.gz -C /opt && \
    ln -s "/opt/hadoop-${HADOOP_VERSION}" /opt/hadoop && \
    rm /tmp/hadoop.tar.gz && \
    useradd --create-home --shell /bin/bash pipeline && \
    passwd -l pipeline && \
    mkdir -p /run/sshd /run/ssh-shared /app/mapreduce /app/scripts && \
    rm -rf /var/lib/apt/lists/*

COPY hadoop/sshd_config /etc/ssh/sshd_config
COPY hadoop/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY mapreduce/ /app/mapreduce/
COPY scripts/cargar_resultados.py /app/scripts/cargar_resultados.py

RUN chmod +x /usr/local/bin/entrypoint.sh && \
    printf '\nexport JAVA_HOME=%s\n' "$JAVA_HOME" >> "$HADOOP_HOME/etc/hadoop/hadoop-env.sh" && \
    hadoop version

EXPOSE 22
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]