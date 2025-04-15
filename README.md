# Terre Haute

A lightweight web tool for reverse engineering and rebuilding Android APKs locally.

Terre Haute empowers developers, security researchers, and Android enthusiasts to decompile, modify, rebuild, and sign APKs offline, ensuring privacy and control. Built with a cyberpunk-inspired interface, it’s perfect for penetration testers, reverse engineers, and privacy-conscious users.

## Features
- Decompile APKs into Smali and XML using Apktool
- Rebuild modified APKs with error logging
- Sign APKs with debug or custom keystores using jarsigner
- Local processing—no data leaves your machine
- Cyberpunk UI with drag-and-drop and progress tracking
- Secure uploads with rate limiting and Basic Auth
- Asynchronous tasks via Celery and Redis

## Requirements
To run Terre Haute on Ubuntu (20.04 LTS or later):

### System Packages
```bash
sudo apt update && sudo apt install -y \
    python3.12 \
    python3.12-venv \
    openjdk-11-jdk \
    redis-server \
    unzip \
    wget \
    git
```

### Python Dependencies
Listed in `requirements.txt`:
```
amqp==5.3.1
billiard==4.2.1
celery==5.5.1
click==8.1.8
Flask==2.1.2
Flask-Limiter==3.12
itsdangerous==2.2.0
Jinja2==3.1.6
kombu==5.5.2
limits==4.7.3
MarkupSafe==3.0.2
ordered-set==4.1.0
packaging==24.2
python-dateutil==2.9.0.post0
redis==5.2.1
sentry-sdk==2.26.0
typing_extensions==4.13.2
tzdata==2025.2
vine==5.1.0
Werkzeug==2.1.2
```

### Tools
- **Apktool** (v2.9.3): For APK decompilation/rebuilding
- **jarsigner** and **keytool**: Included with `openjdk-11-jdk`
- **debug.keystore**: Generated during setup (optional)

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/TerreHaute.git
   cd TerreHaute
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Apktool**:
   ```bash
   wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar
   wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool
   chmod +x /usr/local/bin/apktool
   ```

5. **Generate Debug Keystore** (optional):
   ```bash
   keytool -genkey -v -keystore debug.keystore -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=Android Debug,O=Android,C=US"
   ```

6. **Start Redis**:
   ```bash
   redis-server --daemonize yes
   ```

## Usage
1. **Start Celery**:
   ```bash
   source venv/bin/activate
   celery -A app.celery worker --loglevel=info
   ```

2. **Start Flask**:
   ```bash
   source venv/bin/activate
   export FLASK_ENV=development
   python app.py
   ```

3. **Access the Tool**:
   - Open `http://localhost:5000`
   - **Unbundle**: Upload an APK to decompile
   - **Rebuild & Sign**: Upload a modified ZIP and sign
   - **About**: Learn more
   - Credentials: `admin`/`password123`

## Project Structure
```
TerreHaute/
├── app.py
├── requirements.txt
├── templates/
│   ├── unbundler.html
│   ├── builder.html
│   ├── about.html
├── README.md
├── LICENSE
├── .gitignore
```

## Why Terre Haute?
Unlike online APK tools, Terre Haute runs locally, ensuring privacy. It’s for:
- Penetration testers
- Android developers
- Reverse engineers
- Malware analysts
- Privacy-conscious users

## Credits
- Built with [Apktool](https://ibotpeaches.github.io/Apktool/) and [jarsigner](https://docs.oracle.com/en/java/javase/11/tools/jarsigner.html)
- Powered by [Flask](https://flask.palletsprojects.com/) and [Celery](https://docs.celeryproject.org/)
- Created by Cocofelon

## Disclaimer
⚠️ For legal and ethical use only. Do not modify or redistribute apps without authorization.

## License
[MIT License](LICENSE)
