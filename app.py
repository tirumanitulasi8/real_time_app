import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, jsonify
from firebase_config import db
import re

app = Flask(__name__)

# -------------------- LOGIN PAGE --------------------
@app.route('/')
def index():
    return render_template('login.html')


# -------------------- CREATE ADMIN (ONE TIME USE) --------------------
@app.route('/create_admin')
def create_admin():
    ref = db.child('users')
    ref.child('admin').set({
        "password": "admin123",
        "role": "admin"
    })
    return "Admin Created ✅"


# -------------------- LOGIN LOGIC --------------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not username.isalpha():
        return "Username should contain only alphabets ❌"

    if not re.match("^[a-zA-Z0-9]+$", password):
        return "Password should be alphanumeric ❌"

    ref = db.child('users')
    user = ref.child(username).get()

    if user and user.get('password') == password:
        return redirect(f"/dashboard/{username}")
    else:
        return "Invalid Username or Password ❌"


# -------------------- DASHBOARD --------------------
@app.route('/dashboard/<username>')
def dashboard(username):
    ref = db.child('users')
    user = ref.child(username).get()

    if not user:
        return "User not found ❌"

    return render_template(
        'dashboard.html',
        username=username,
        role=user.get('role', ''),
        bio=user.get('bio', ''),
        profile_pic=user.get('profile_pic', 'default.png')
    )


# -------------------- FEED --------------------
@app.route('/feed/<username>')
def feed(username):
    ref = db.child('posts')
    data = ref.get()

    posts = []
    if data:
        for key, value in data.items():
            posts.append(value)

    return render_template('feed.html', posts=posts, username=username)


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# -------------------- UPLOAD POST --------------------
@app.route('/upload/<username>', methods=['GET', 'POST'])
def upload(username):
    if request.method == 'POST':
        content = request.form.get('content')
        file = request.files.get('image')

        filename = ""

        if file and file.filename != "":
            filename = secure_filename(file.filename)

            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # create folder if not exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            file.save(upload_path)

        ref = db.child('posts')
        ref.push({
            "username": username,
            "content": content,
            "image": filename,
            "likes": 0
        })

        return redirect(f"/feed/{username}")

    return render_template('upload.html', username=username)

# -------------------- GET POSTS API --------------------
@app.route('/get_posts')
@app.route('/get_posts/<username>')
def get_posts(username=None):
    ref = db.child('posts')
    data = ref.get()

    posts = []
    if data:
        for key, value in data.items():
            if username is None or value.get("username") == username:
                value['id'] = key
                posts.append(value)

    return jsonify(posts)


# -------------------- FORGOT PASSWORD --------------------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        username = request.form['username']

        ref = db.child('password_requests')
        ref.push({
            "username": username,
            "status": "pending"
        })

        return "Request Sent to Admin ✅"

    return render_template('forgot.html')


# -------------------- VIEW REQUESTS (ADMIN) --------------------
@app.route('/users/<username>')
def users(username):
    ref = db.child('users')
    user = ref.child(username).get()

    if not user or user.get("role") != "admin":
        return "Access Denied ❌ (Admin only)"

    ref_req = db.child('password_requests')
    data = ref_req.get()

    requests = []
    if data:
        for key, value in data.items():
            requests.append(value)

    return render_template('users.html', requests=requests, username=username)


# -------------------- APPROVE RESET --------------------
@app.route('/approve/<target_user>/<admin>')
def approve(target_user, admin):

    ref = db.child('users')
    admin_user = ref.child(admin).get()

    if not admin_user or admin_user.get("role") != "admin":
        return "Access Denied ❌"

    ref.child(target_user).update({
        "password": "new123"
    })

    return f"Password reset for {target_user} ✅"


# -------------------- REGISTER --------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username.isalpha():
            return "Username only alphabets ❌"

        if not re.match("^[a-zA-Z0-9]+$", password):
            return "Password must be alphanumeric ❌"

        ref = db.child('users')

        if ref.child(username).get():
            return "User already exists ❌"

        ref.child(username).set({
            "password": password,
            "role": "user",
            "bio": "",
            "profile_pic": "default.png"
        })

        return "User Registered Successfully ✅"

    return render_template('register.html')


# -------------------- CHANGE PASSWORD --------------------
@app.route('/change_password/<username>', methods=['POST'])
def change_password(username):
    new_password = request.form['new_password']

    if not re.match("^[a-zA-Z0-9]+$", new_password):
        return "Password must be alphanumeric ❌"

    ref = db.child('users')
    ref.child(username).update({
        "password": new_password
    })

    return "Password Updated Successfully ✅"


# -------------------- DELETE ACCOUNT --------------------
@app.route('/delete_account/<username>')
def delete_account(username):
    ref = db.child('users')
    ref.child(username).delete()

    return "Account Deleted ❌"


# -------------------- SETTINGS --------------------
@app.route('/settings/<username>')
def settings(username):
    return render_template('settings.html', username=username)


# -------------------- UPDATE PROFILE --------------------
@app.route('/update_profile/<username>', methods=['POST'])
def update_profile(username):
    bio = request.form['bio']
    file = request.files['profile_pic']

    filename = ""

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        ref = db.child('users')
        old = ref.child(username).get()
        filename = old.get("profile_pic", "default.png")

    ref = db.child('users')
    ref.child(username).update({
        "bio": bio,
        "profile_pic": filename
    })

    return "Profile Updated ✅"


# -------------------- LIKE POST --------------------
@app.route('/like/<post_id>')
def like(post_id):
    ref = db.child(f'posts/{post_id}')
    post = ref.get()

    likes = post.get('likes', 0) + 1

    ref.update({
        "likes": likes
    })

    return jsonify({"likes": likes})


# -------------------- RUN --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)