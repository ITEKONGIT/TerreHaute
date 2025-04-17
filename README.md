Terre Haute

A lightweight web tool for reverse engineering and rebuilding Android APKs locally.

Terre Haute empowers developers, security researchers, and Android enthusiasts to decompile, modify, rebuild, and sign APKs offline, ensuring privacy and control. Built with a cyberpunk-inspired interface, it’s perfect for penetration testers, reverse engineers, and privacy-conscious users.

Features





Decompile APKs into Smali and XML using Apktool



Rebuild modified APKs with error logging



Sign APKs with debug or custom keystores using jarsigner



Local processing—no data leaves your machine



Cyberpunk UI with drag-and-drop and progress tracking



Secure uploads with rate limiting and Basic Auth



Asynchronous tasks via Celery and Redis

Requirements

To run Terre Haute manually on Ubuntu (20.04 LTS or later):

System Packages

sudo apt update && sudo apt install -y \
    python3.12 \
    python3.12-venv \
    openjdk-11-jdk \
    redis-server \
    unzip \
    wget \
    git

Python Dependencies

Listed in requirements.txt:

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

Tools





Apktool (v2.9.3): For APK decompilation/rebuilding



jarsigner and keytool: Included with openjdk-11-jdk



debug.keystore: Generated during setup (optional)

Installation (Manual Setup)

This section is for manual setup without Docker. For Docker setup, see the "Containerized Version" section below.





Clone the Repository:

git clone -b containerized-version https://github.com/ITEKONGIT/TerreHaute.git
cd TerreHaute



Set Up Virtual Environment:

python3.12 -m venv venv
source venv/bin/activate



Install Python Dependencies:

pip install -r requirements.txt



Install Apktool:

wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar
wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool
chmod +x /usr/local/bin/apktool



Generate Debug Keystore (optional):

keytool -genkey -v -keystore debug.keystore -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=Android Debug,O=Android,C=US"



Start Redis:

redis-server --daemonize yes

Containerized Version (Docker Setup)

This branch (containerized-version) includes Docker support for a one-command setup. To use Docker:





Clone this Branch:

git clone -b containerized-version https://github.com/ITEKONGIT/TerreHaute.git
cd TerreHaute



Install Docker:





Download Docker Desktop for Windows or install docker and docker-compose on Ubuntu:

sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker



Build and Run:

docker-compose up --build





Access at http://localhost:5000.



Log in with admin/password123.



Stop with Ctrl+C and docker-compose down.

Usage





Start Celery (if not using Docker):

source venv/bin/activate
celery -A app.celery worker --loglevel=info



Start Flask (if not using Docker):

source venv/bin/activate
export FLASK_ENV=development
python app.py



Access the Tool:





Open http://localhost:5000



Unbundle: Upload an APK to decompile



Rebuild & Sign: Upload a modified ZIP and sign



About: Learn more



Credentials: admin/password123

Project Structure

TerreHaute/
├── app.py
├── requirements.txt
├── templates/
│   ├── unbundler.html
│   ├── builder.html
│   ├── about.html
├── Dockerfile
├── docker-compose.yml
├── README.md
├── LICENSE
├── .gitignore

Choosing a Version

Terre Haute is available in two versions:





Main Branch (Normal Version): For manual setup without Docker.

git clone https://github.com/ITEKONGIT/TerreHaute.git



Containerized Version (this branch): Includes Docker support for a one-command setup.

Why Terre Haute?

Unlike online APK tools, Terre Haute runs locally, ensuring privacy. It’s for:





Penetration testers



Android developers



Reverse engineers



Malware analysts



Privacy-conscious users

Credits





Built with Apktool and jarsigner



Powered by Flask and Celery



Created by Cocofelon

Disclaimer

⚠ For legal and ethical use only. Do not modify or redistribute apps without authorization.

License

MIT License