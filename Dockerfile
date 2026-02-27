FROM python:3.11-slim

# Cria usuário
RUN useradd -m -u 1000 user

WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Instala dependências como root (mais seguro para PATH)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia projeto
COPY . .

# Cria pastas com root
RUN mkdir -p /app/uploads /app/db \
    && chown -R user:user /app

# Troca para user só no final
USER user

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--workers", "3", "--threads", "2", "--bind", "0.0.0.0:7860",  "--timeout", "120",  "main:app"]