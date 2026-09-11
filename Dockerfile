# --- Stage 1: build the Vue frontend into static assets ---
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python backend serving the API + built frontend ---
FROM python:3.14-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .
COPY backend/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Drop the built frontend assets into app/static, served by FastAPI.
COPY --from=frontend-build /frontend/dist ./app/static

EXPOSE 8000

CMD ["./entrypoint.sh"]
