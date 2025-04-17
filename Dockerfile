FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar && \
    wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool
RUN keytool -genkey -v -keystore /app/debug.keystore -alias androiddebugkey \
    -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android \
    -dname "CN=Android Debug,O=Android,C=US"
COPY app.py .
COPY templates/ templates/
EXPOSE 5000
CMD ["python", "app.py"]
