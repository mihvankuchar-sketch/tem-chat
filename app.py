import os
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'mihvan_secret_chat_key'

GROUP_PASSWORD = "123"  # كلمة المرور للجروب

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

messages = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>واتساب جروب - ميهفان</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #efeae2; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .whatsapp-container { width: 100%; max-width: 600px; height: 90vh; background: #f0f2f5; display: flex; flex-direction: column; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden; }
        .chat-header { background: #00a884; color: #fff; padding: 15px; display: flex; align-items: center; font-size: 18px; font-weight: bold; }
        .chat-box { flex: 1; padding: 20px; overflow-y: auto; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-repeat: repeat; display: flex; flex-direction: column; gap: 10px; }
        .message { max-width: 70%; padding: 10px 14px; border-radius: 8px; position: relative; word-wrap: break-word; background: #ffffff; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }
        .message.incoming { align-self: flex-start; border-top-left-radius: 0; }
        .message.outgoing { align-self: flex-end; background: #d9fdd3; border-top-right-radius: 0; }
        .username { font-size: 12px; font-weight: bold; color: #005c4b; margin-bottom: 3px; display: block; }
        .message img, .message video { max-width: 100%; border-radius: 6px; margin-top: 5px; }
        .chat-form { background: #f0f2f5; padding: 10px 15px; display: flex; gap: 10px; align-items: center; border-top: 1px solid #d1d7db; }
        .chat-form input[type="text"] { flex: 1; padding: 10px 15px; border-radius: 20px; border: none; outline: none; font-size: 14px; }
        .file-label { background: #e9edef; padding: 8px 12px; border-radius: 50%; cursor: pointer; font-size: 16px; text-align: center; }
        .chat-form button { background: #00a884; color: white; border: none; padding: 10px 20px; border-radius: 20px; font-weight: bold; cursor: pointer; }
        .chat-form button:hover { background: #01755f; }
        .login-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background: #00a884; width: 100%; }
        .login-box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); text-align: center; width: 300px; }
        .login-box input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .login-box button { width: 100%; padding: 10px; background: #00a884; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>

{% if not session.get('logged_in') %}
    <div class="login-screen">
        <div class="login-box">
            <h2>🔒 جروب مغلق</h2>
            <p>أدخل كلمة مرور الجروب للمتابعة</p>
            {% if error %}
                <p style="color: red; font-size: 12px;">{{ error }}</p>
            {% endif %}
            <form method="POST" action="/login">
                <input type="password" name="password" placeholder="كلمة المرور..." required>
                <button type="submit">دخول</button>
            </form>
        </div>
    </div>
{% else %}
    <div class="whatsapp-container">
        <div class="chat-header">💬 جروب أصدقاء ميهفان</div>
        <div class="chat-box" id="chatBox">
            {% for msg in messages %}
                <div class="message {% if loop.index0 % 2 == 0 %}incoming{% else %}outgoing{% endif %}">
                    <span class="username">{{ msg.username }}</span>
                    {% if msg.text %}
                        <div style="font-size: 14px; color: #111;">{{ msg.text }}</div>
                    {% endif %}
                    {% if msg.filename %}
                        {% if msg.type == 'image' %}
                            <img src="{{ url_for('uploaded_file', filename=msg.filename) }}" alt="صورة">
                        {% elif msg.type == 'video' %}
                            <video controls width="100%">
                                <source src="{{ url_for('uploaded_file', filename=msg.filename) }}" type="video/mp4">
                                متصفحك لا يدعم الفيديو
                            </video>
                        {% endif %}
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        <form class="chat-form" method="POST" enctype="multipart/form-data">
            <input type="text" name="username" placeholder="اسمك..." required style="max-width: 100px;">
            <input type="text" name="text" placeholder="اكتب رسالة...">
            <label class="file-label" title="رفع صورة أو فيديو">📎
                <input type="file" name="file" accept="image/*,video/*" style="display: none;">
            </label>
            <button type="submit">إرسال</button>
        </form>
    </div>
    <script>
        var chatBox = document.getElementById("chatBox");
        chatBox.scrollTop = chatBox.scrollHeight;
    </script>
{% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def chat():
    if not session.get('logged_in'):
        return render_template_string(HTML_TEMPLATE)
    if request.method == 'POST':
        username = request.form.get('username', 'مجهول')
        text = request.form.get('text', '')
        file = request.files.get('file')
        filename = None
        file_type = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                file_type = 'image'
            elif filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
                file_type = 'video'
        if text or filename:
            messages.append({'username': username, 'text': text, 'filename': filename, 'type': file_type})
        return redirect(url_for('chat'))
    return render_template_string(HTML_TEMPLATE, messages=messages)

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == GROUP_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('chat'))
    else:
        return render_template_string(HTML_TEMPLATE, error="كلمة المرور غير صحيحة!")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)