FROM python:3.10-slim

WORKDIR /app

# Install ffmpeg for PyDub
RUN apt-get update && apt-get install -y ffmpeg

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

# Expose the port Render expects
EXPOSE 10000

# Start the Flask app with gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
