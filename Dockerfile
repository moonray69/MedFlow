# Базовий образ Python для Mac M-чіпів
FROM python:3.11-slim

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /code

# Копіюємо список бібліотек
COPY ./requirements.txt /code/requirements.txt

# Оновлюємо pip та встановлюємо залежності
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /code/requirements.txt

# Копіюємо весь код додатку
COPY ./app /code/app

# Команда для запуску сервера всередині контейнера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]