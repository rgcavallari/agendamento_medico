FROM python:3.12-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia o requirements primeiro (melhora cache)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Expõe a porta em que o Flask roda
EXPOSE 5000

# Variáveis de ambiente (opcional, mas ajuda)
ENV FLASK_APP=app.py

# Comando para rodar a aplicação
CMD ["python", "app.py"]
