FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY backend ./backend

# Hugging Face Spaces uses port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Command to run the application
CMD ["python", "backend/main.py"]
