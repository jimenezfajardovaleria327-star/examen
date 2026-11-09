# Examen Segundo Parcial: Pipeline de datos contenerizado

**Matrícula:** 125055397  
**Pregunta asignada:** Top 10 productos por ingreso total en 2025 (`cantidad * precio_unitario`).  
**Procesamiento:** Hadoop Streaming en modo standalone, comparado con lectura secuencial en Python.  
**API:** Flask + PostgreSQL.

## Requisitos

- Docker Engine y el complemento Docker Compose.
- El CSV generado con `ecamenval.py` debe estar en `../../practica1.py/ventas_125055397.csv` respecto a esta carpeta. No se copia a la imagen ni se agrega al repositorio.
- El archivo actual, generado con la matrícula indicada, ocupa aproximadamente 352 MB.

Si el CSV está en otra ubicación, edita `DATASET_PATH` en `.env`. Ajusta también `DB_PASSWORD` antes de compartir el repositorio. Los valores predeterminados son solo para desarrollo local.

## Ejecución

Desde esta carpeta:

```bash
cp .env.example .env
docker compose up --build
```

El servicio `hadoop` imprime la versión de Hadoop, prueba `ssh localhost`, mide primero el script secuencial y después ejecuta Hadoop Streaming. Antes de cargar datos, compara byte por byte los resultados; si difieren, el servicio falla. Al coincidir, `scripts/cargar_resultados.py` guarda los 10 productos en PostgreSQL. La API espera a que el pipeline termine y queda disponible en `http://localhost:5001`.

La primera ejecución descarga las imágenes y Hadoop, por lo que tarda más. En ejecuciones posteriores el proceso de análisis se repite al iniciar el stack. El CSV está montado de solo lectura y PostgreSQL usa el volumen nombrado `db_data`.

## Verificación y API

En otra terminal, desde esta carpeta:

```bash
docker compose exec hadoop hadoop version
docker compose exec hadoop ssh localhost
docker compose exec api ssh pipeline@hadoop 'printf "SSH API a Hadoop OK\\n"'
curl http://localhost:5001/ssh-check
curl http://localhost:5001/resultados
curl http://localhost:5001/resultados/ELE-0001
```

La última clave es un ejemplo; usa un producto que aparezca en la lista real. Los endpoints responden JSON. El CRUD incluye `GET /resultados`, `GET /resultados/<producto>`, `POST`, `PUT` y `DELETE` sobre `/resultados`. Para probar una escritura sin agregar una fila fuera del top 10:

```bash
curl -X PUT http://localhost:5001/resultados/ELE-0001 \
  -H 'Content-Type: application/json' \
  -d '{"total_revenue": 123456.78}'
```

Usa una clave existente. El valor de ejemplo modifica el resultado almacenado; el job lo restaura al volver a ejecutarse.

## Comparativa de rendimiento

El contenedor registra `Tiempo secuencial: ...s` y `Tiempo Hadoop Streaming: ...s` al iniciar. También guarda los resultados de ambos métodos en `/data/output/secuencial.tsv` y `/data/output/resultado/part-00000`; el script comprueba que coincidan exactamente antes de cargar la base de datos. Para conservar una evidencia de la sesión:

```bash
docker compose logs --no-color hadoop | tee evidencias/pipeline.log
```

Registra aquí los tiempos de la ejecución final:

| Método | Tiempo (s) | Resultado |
| --- | ---: | --- |
| Secuencial Python | Pendiente de ejecutar | Top 10 |
| Hadoop Streaming standalone | Pendiente de ejecutar | Idéntico al secuencial |

Para un archivo de este tamaño y una sola máquina, el script secuencial suele ganar porque evita iniciar tareas, serializar y ordenar pares clave-valor, incluso cuando Hadoop usa su ejecutor local. MapReduce se vuelve conveniente cuando los datos superan la capacidad de una sola máquina o se distribuyen en varios nodos; el paralelismo compensa esos costos de coordinación.

## Persistencia y limpieza

```bash
docker compose down
docker compose up --build
```

`docker compose down` conserva el volumen `db_data`; la carga del pipeline es idempotente y vuelve a poblar los mismos resultados. Para borrar deliberadamente la base y volver a procesar:

```bash
docker compose down -v
docker compose up --build
```

El segundo comando elimina todos los volúmenes del proyecto, incluidos los datos de PostgreSQL, las salidas y las llaves SSH; al iniciar se generan llaves nuevas y se repite el procesamiento.

## Evidencias

Guarda en `evidencias/` capturas o logs que muestren `hadoop version`, `ssh localhost`, la conexión `api` a `hadoop`, las salidas equivalentes de ambos métodos y la respuesta JSON de la API. El log de Hadoop contiene la salida del job y los tiempos.

## Teoría

1. **Explica la diferencia entre los modos standalone, pseudo-distribuido y totalmente distribuido de Hadoop. ¿En cuál de ellos se usa HDFS?**  
  En standalone, Hadoop ejecuta los trabajos localmente, sin servicios distribuidos ni HDFS. En pseudo-distribuido, los servicios corren como procesos separados en una sola máquina y se puede usar HDFS local. En totalmente distribuido, almacenamiento y cómputo se reparten entre varias máquinas; también se usa HDFS. Por tanto, HDFS se usa en los modos pseudo-distribuido y totalmente distribuido.

2. **¿Por qué el dataset se monta como volumen y no se copia dentro de la imagen con `COPY`? Menciona al menos dos razones.**  
  El volumen mantiene el CSV fuera de la imagen, evitando que esta y el repositorio crezcan cientos de megabytes. También permite reemplazar o regenerar el dataset sin reconstruir la imagen. Al montarlo como solo lectura (`:ro`), el contenedor no puede modificar el archivo original.

3. **¿Qué ocurre con los datos de la base de datos al ejecutar `docker compose down`? ¿Y con `docker compose down -v`?**  
  `docker compose down` elimina los contenedores y la red, pero conserva los volúmenes nombrados, por lo que los datos persisten. `docker compose down -v` elimina también esos volúmenes y sus datos; es una operación destructiva.

4. **¿Por qué MapReduce no siempre es más rápido que un script secuencial con un archivo de 400 MB? ¿A partir de qué condiciones conviene?**  
  MapReduce añade costos de planificación, serialización, ordenamiento y coordinación; para 400 MB en una sola máquina, una lectura secuencial puede terminar antes. Conviene cuando el volumen excede la capacidad de un nodo o se distribuye entre varios nodos y el paralelismo compensa esos costos.

5. **¿Cuál es la diferencia entre `CMD` y `ENTRYPOINT`, y entre `COPY` y `ADD`?**  
  `ENTRYPOINT` define el ejecutable principal del contenedor; `CMD` proporciona valores o argumentos predeterminados que pueden reemplazarse al ejecutar el contenedor. `COPY` copia archivos del contexto de construcción a la imagen. `ADD` también puede extraer archivos tar locales y manejar URLs; para una copia normal se prefiere `COPY` por ser más explícito.