FROM python:3.12.1-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache gcc musl-dev libc-dev
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run command
CMD ["python", "src/app.py"]