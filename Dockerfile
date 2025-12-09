FROM python:3.13-alpine AS builder

RUN apk add --no-cache gcc musl-dev linux-headers postgresql-dev

WORKDIR /app

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.13-alpine

RUN apk add --no-cache \
    tzdata \
    postgresql-libs \
    dcron \
    busybox-suid \
    su-exec \
    musl-locales \
    icu-data-full

ENV TZ=Europe/Rome \
    LANG=it_IT.UTF-8 \
    LANGUAGE=it_IT:it \
    LC_ALL=it_IT.UTF-8

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN addgroup -S appgroup -g 1001 && \
    adduser -S appuser -u 1001 -G appgroup

WORKDIR /app

RUN mkdir -p /var/spool/cron/crontabs && \
    chown -R root:appgroup /var/spool/cron/crontabs && \
    chmod 1775 /var/spool/cron/crontabs && \
    chmod u+s /usr/sbin/crond && \
    chmod 4755 /usr/bin/crontab
    
RUN mkdir -p /app/staticfiles /app/media /var/log && \
    chown -R appuser:appgroup /app /var/log

COPY --from=builder --chown=appuser:appgroup /app/venv /app/venv

COPY --chown=appuser:appgroup . .

RUN chmod +x /app/entrypoint.sh

ENV PATH="/app/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "registro.asgi:application", \
     "--workers", "3", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]