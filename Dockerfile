FROM python:3.12-slim
WORKDIR /app
COPY server/ /app/server/
COPY db/ /app/db/
COPY scripts/ /app/scripts/
ENV APP_ENV=staging
ENV SOUKLY_PORT=8787
ENV PYTHONUNBUFFERED=1
EXPOSE 8787
CMD ["sh", "-c", "python3 server/migrate.py && python3 server/app.py"]
