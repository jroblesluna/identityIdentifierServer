FROM python:3.10-slim

# Instalar dependencias de sistema necesarias para compilar dlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libjpeg-dev \
    libpng-dev \
    python3-dev \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app

COPY . /app

# Instalar CMake vía pip y dlib antes que el resto
RUN pip install --upgrade pip setuptools wheel \
 && pip install cmake==3.27.0 \
 && pip install dlib==19.22.0 \
 && pip install --no-cache-dir -r requirements.txt

# Descargar modelo si lo necesitas
# RUN wget https://.../shape_predictor_68_face_landmarks.dat -O /app/...

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]