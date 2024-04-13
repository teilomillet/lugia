FROM python:3.12

WORKDIR /app

# Copy only the requirements file, to cache the pip install step
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
