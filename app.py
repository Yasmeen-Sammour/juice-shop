import os
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(name)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------------------------------------------------
# 1. OS Command Injection (Patched)
# ---------------------------------------------------------
@app.route('/ping', methods=['GET', 'POST'])
def ping():
    output = ""
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        # PATCHED: استخدام subprocess وتمرير المدخلات كقائمة لمنع حقن الأوامر
        import subprocess
        try:
            res = subprocess.check_output(["ping", "-c", "2", ip], stderr=subprocess.STDOUT, timeout=5).decode('utf-8')
        except Exception as e:
            res = str(e)
        output = f'<div class="result-box"><pre>{res}</pre></div>'
    
    content = f'''
    <h2>Network Diagnostic Tool (Secure)</h2>
    <form method="POST">
        <label>Enter Host or IP Address:</label>
        <input type="text" name="ip" placeholder="127.0.0.1">
        <button type="submit">Run Ping Test</button>
    </form>
    {output}
    '''
    return render_template_string(content)


# ---------------------------------------------------------
# 2. Cross-Site Scripting (XSS) (Patched)
# ---------------------------------------------------------
comments = []

@app.route('/xss', methods=['GET', 'POST'])
def xss():
    if request.method == 'POST':
        comment = request.form.get('comment', '')
        if comment:
            # PATCHED: الـ Flask تلقائياً بيعمل Escaping للنصوص، لكن لتأكيد الأمان:
            from markupsafe import escape
            safe_comment = escape(comment)
            comments.append(safe_comment)
            
    comments_html = "".join([f'<div class="result-box">{c}</div>' for c in comments])
    content = f'''
    <h2>Guestbook Notes (Secure)</h2>
    <form method="POST">
        <label>Leave a Comment:</label>
        <input type="text" name="comment" placeholder="Write something...">
        <button type="submit">Submit Note</button>
    </form>
    <h3>Recent Notes:</h3>
    {comments_html}
    '''
    return render_template_string(content)


# ---------------------------------------------------------
# 3. File Upload Vulnerability (Patched)
# ---------------------------------------------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    message = ""
    if request.method == 'POST':
        if 'file' not in request.files:
            message = "No file part"
        else:
            file = request.files['file']
            if file.filename == '':
                message = "No selected file"
            else:
                # PATCHED: التحقق من الامتدادات المسموحة واستخدام secure_filename
                ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'txt'}
                def allowed_file(filename):
                    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
                
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    message = f"File successfully uploaded: {filename}"
                else:
                    message = "Invalid file type! Only images and text files are allowed."

    content = f'''
    <h2>File Upload (Secure)</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Upload</button>
    </form>
    <p>{message}</p>
    '''
    return render_template_string(content)


if name == 'main':
    app.run(host='0.0.0.0', port=5000, debug=True)
import os
import re
import sqlite3
import logging
import ipaddress
import subprocess
from markupsafe import escape
from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename

app = Flask(name)

# Upload folder config
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB cap
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Wazuh logging config
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


@app.before_request
def log_request():
    logging.info(f"Method: {request.method} Path: {request.path} Remote IP: {request.remote_addr}")
