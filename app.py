import os
import subprocess
import zipfile
import shutil
import re
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from celery import Celery
from datetime import datetime
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Configuration
app.config.update({
    'UPLOAD_FOLDER': 'Uploads',
    'UNBUNDLED_FOLDER': 'unbundled',
    'SIGNED_FOLDER': 'signed_apks',
    'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB
    'ALLOWED_EXTENSIONS': {'apk', 'zip', 'keystore', 'jks'},
    'SECRET_KEY': os.urandom(24),  # For session security
})

# Setup Celery
celery = Celery(
    app.name,
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)
celery.conf.update(app.config)

# Setup directories
for folder in [app.config['UPLOAD_FOLDER'], 
               app.config['UNBUNDLED_FOLDER'], 
               app.config['SIGNED_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('apktool_web.log'),
        logging.StreamHandler()
    ]
)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10 per hour"],
    storage_uri="redis://localhost:6379/0"  # Use Redis for rate limit storage
)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def sanitize_public_xml(apk_dir):
    public_xml = os.path.join(apk_dir, 'res', 'values', 'public.xml')
    if os.path.exists(public_xml):
        try:
            with open(public_xml, 'r+') as f:
                content = f.read()
                content = re.sub(r'<public type="drawable" name="\$.+?" id=".+?"/>', '', content)
            with open(public_xml, 'w') as f:
                f.write(content)
            logging.info("Sanitized public.xml")
        except Exception as e:
            logging.error(f"Failed to sanitize public.xml: {str(e)}")

def run_apktool(command, args):
    try:
        result = subprocess.run(
            ['apktool', command] + args,
            check=True,
            capture_output=True,
            text=True
        )
        logging.info(f"apktool {command} succeeded")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"apktool {command} failed: {e.stderr}")
        return False

@celery.task(bind=True)
def unbundle_task(self, filename, apk_path, output_dir, zip_filename, zip_path):
    self.update_state(state='PROGRESS', meta={'progress': 20})
    shutil.rmtree(output_dir, ignore_errors=True)
    
    if not run_apktool('d', ['-f', '-o', output_dir, apk_path]):
        raise Exception("Failed to unbundle APK")
    
    self.update_state(state='PROGRESS', meta={'progress': 60})
    sanitize_public_xml(output_dir)
    
    self.update_state(state='PROGRESS', meta={'progress': 90})
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', output_dir)
    
    self.update_state(state='PROGRESS', meta={'progress': 100})
    return {'download_url': f'/download/{zip_filename}'}

@celery.task(bind=True)
def rebuild_task(self, filename, zip_path, extracted_dir, output_apk, keystore_path, keystore_password, key_alias):
    self.update_state(state='PROGRESS', meta={'progress': 20})
    shutil.rmtree(extracted_dir, ignore_errors=True)
    shutil.unpack_archive(zip_path, extracted_dir)
    
    self.update_state(state='PROGRESS', meta={'progress': 60})
    if not run_apktool('b', ['-o', output_apk, extracted_dir]):
        raise Exception("Failed to rebuild APK")
    
    self.update_state(state='PROGRESS', meta={'progress': 90})
    try:
        result = subprocess.run(
            [
                'jarsigner',
                '-keystore', keystore_path,
                '-storepass', keystore_password,
                '-keypass', keystore_password,
                output_apk,
                key_alias
            ],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info("APK signed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to sign APK: {e.stderr} (Command: {e.cmd})")
        raise Exception(f"Failed to sign APK: {e.stderr}")
    
    self.update_state(state='PROGRESS', meta={'progress': 100})
    return {'download_url': f'/download/rebuilt_{filename.replace(".zip", ".apk")}'}

@app.route('/')
def unbundler():
    return render_template('unbundler.html')

@app.route('/builder')
def builder():
    return render_template('builder.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/unbundle', methods=['POST'])
@limiter.limit("10 per hour")
def unbundle_apk():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filename = secure_filename(file.filename)
        apk_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(apk_path)
        
        output_dir = os.path.join(app.config['UNBUNDLED_FOLDER'], os.path.splitext(filename)[0])
        zip_filename = f"unbundled_{filename.split('.')[0]}.zip"
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        
        task = unbundle_task.apply_async(args=[filename, apk_path, output_dir, zip_filename, zip_path])
        return jsonify({'task_id': task.id}), 202
    
    except Exception as e:
        logging.error(f"Unbundling error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/rebuild', methods=['POST'])
@limiter.limit("10 per hour")
def rebuild_apk():
    if 'file' not in request.files:
        return jsonify({'error': 'Missing ZIP file'}), 400
    
    zip_file = request.files['file']
    keystore_file = request.files.get('keystore')
    keystore_password = request.form.get('keystore_password', 'android')
    key_alias = request.form.get('key_alias', 'androiddebugkey')
    
    if zip_file.filename == '':
        return jsonify({'error': 'No ZIP file selected'}), 400
    
    if not allowed_file(zip_file.filename):
        return jsonify({'error': 'Invalid ZIP file type'}), 400
    
    try:
        zip_filename = secure_filename(zip_file.filename)
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        zip_file.save(zip_path)
        
        if keystore_file and keystore_file.filename != '':
            if not allowed_file(keystore_file.filename):
                return jsonify({'error': 'Invalid keystore file type'}), 400
            keystore_filename = secure_filename(keystore_file.filename)
            keystore_path = os.path.join(app.config['UPLOAD_FOLDER'], keystore_filename)
            keystore_file.save(keystore_path)
        else:
            keystore_path = 'debug.keystore'  # Fallback to default
            if not os.path.exists(keystore_path):
                return jsonify({'error': 'Default keystore not found'}), 500
        
        extracted_dir = os.path.join(app.config['UNBUNDLED_FOLDER'], os.path.splitext(zip_filename)[0])
        output_apk = os.path.join(app.config['SIGNED_FOLDER'], f"rebuilt_{zip_filename.replace('.zip', '.apk')}")
        
        task = rebuild_task.apply_async(args=[
            zip_filename, zip_path, extracted_dir, output_apk,
            keystore_path, keystore_password, key_alias
        ])
        return jsonify({'task_id': task.id}), 202
    
    except Exception as e:
        logging.error(f"Rebuilding error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<task_id>')
@limiter.exempt
def task_progress(task_id):
    task = unbundle_task.AsyncResult(task_id) or rebuild_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'progress': 0}
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'progress': task.info.get('progress', 0)
        }
        if 'download_url' in task.info:
            response['download_url'] = task.info['download_url']
    else:
        response = {'state': task.state, 'progress': 0, 'error': str(task.info)}
    return jsonify(response)

@app.route('/download/<filename>')
def download_file(filename):
    if filename.endswith('.zip'):
        directory = app.config['UPLOAD_FOLDER']
    elif filename.endswith('.apk'):
        directory = app.config['SIGNED_FOLDER']
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    return send_file(os.path.join(directory, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)