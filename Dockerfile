# Build stage
FROM python:3.9 AS builder

# Install git-lfs in builder stage
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get install git-lfs && \
    git lfs install

# Final stage
FROM python:3.9

# Install only OpenCV dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /usr/bin/git-lfs /usr/bin/git-lfs
COPY --from=builder /usr/local/bin/git-lfs /usr/local/bin/git-lfs

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the application
CMD python manage.py runserver 0.0.0.0:${PORT:-8000}