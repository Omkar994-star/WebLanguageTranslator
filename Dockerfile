FROM python:3.10-slim

WORKDIR /app

# Install ffmpeg and dependencies for PyDub
RUN apt-get update && apt-get install -y ffmpeg libavcodec-extra && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy the entire app code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port Render expects
EXPOSE 10000

# Start the Flask app with gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
