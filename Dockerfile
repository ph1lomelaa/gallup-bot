# 1. Используем стабильный Python 3.10
FROM python:3.10-slim

# 2. Устанавливаем зависимости
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Копируем проект
COPY . .

# 4. Указываем команду запуска
CMD ["python", "main.py"]
