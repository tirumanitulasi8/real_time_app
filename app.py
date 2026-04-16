import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect
from firebase_config import db
import re
from flask import jsonify

app = Flask(__name__)


# -------------------- LOGIN PAGE --------------------
@app.route('/')
def index():
    return render_template('login.html')


# -------------------- CREATE ADMIN (ONE TIME USE) --------------------
@app.route('/create_admin')
def create_admin():
    ref = db.reference('users')
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

    # Username validation (only alphabets)
    if not username.isalpha():
        return "Username should contain only alphabets ❌"

    # Password validation (alphanumeric)
    if not re.match("^[a-zA-Z0-9]+$", password):
        return "Password should be alphanumeric ❌"

    # Firebase check
    ref = db.reference('users')
    user = ref.child(username).get()

    if user and user['password'] == password:
        return redirect(f"/dashboard/{username}")
    else:
        return "Invalid Username or Password ❌"


# -------------------- DASHBOARD --------------------
@app.route('/dashboard/<username>')
def dashboard(username):
    ref = db.reference('users')
    user = ref.child(username).get()

    return render_template(
        'dashboard.html',
        username=username,
        role=user['role'],
        bio=user.get('bio', ''),
        profile_pic=user.get('profile_pic', 'default.png')
    )



# -------------------- FEED --------------------
@app.route('/feed/<username>')
def feed(username):
    ref = db.reference('posts')
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
        content = request.form['content']
        file = request.files['image']

        filename = ""

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        ref = db.reference('posts')
        new_post = ref.push({
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
def get_posts(username):
    ref = db.reference('posts')
    data = ref.get()

    posts = []
    if data:
        for key, value in data.items():
            if value.get("username") == username:
                value['id'] = key   # ⭐ IMPORTANT
                posts.append(value)

    return jsonify(posts)


# -------------------- FORGOT PASSWORD --------------------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        username = request.form['username']

        ref = db.reference('password_requests')
        ref.push({
            "username": username,
            "status": "pending"
        })

        return "Request Sent to Admin ✅"

    return render_template('forgot.html')

# -------------------- VIEW REQUESTS (ADMIN) --------------------
@app.route('/users/<username>')
def users(username):
    ref = db.reference('users')
    user = ref.child(username).get()

    # 🔒 Check admin or not
    if not user or user.get("role") != "admin":
        return "Access Denied ❌ (Admin only)"

    # Get requests
    ref_req = db.reference('password_requests')
    data = ref_req.get()

    requests = []
    if data:
        for key, value in data.items():
            requests.append(value)

    return render_template('users.html', requests=requests, username=username)


# -------------------- APPROVE RESET --------------------
@app.route('/approve/<target_user>/<admin>')
def approve(target_user, admin):

    ref = db.reference('users')
    admin_user = ref.child(admin).get()

    # 🔒 Admin check
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

        # Validation
        if not username.isalpha():
            return "Username only alphabets ❌"

        import re
        if not re.match("^[a-zA-Z0-9]+$", password):
            return "Password must be alphanumeric ❌"

        ref = db.reference('users')

        # Check if user exists
        if ref.child(username).get():
            return "User already exists ❌"

        # Save user
        ref.child(username).set({
            "password": password,
            "role": "user",
            "bio": "",
            "profile_pic": "default.png"
            })

        return "User Registered Successfully ✅"

    return render_template('register.html')


@app.route('/change_password/<username>', methods=['POST'])
def change_password(username):
    new_password = request.form['new_password']

    import re
    if not re.match("^[a-zA-Z0-9]+$", new_password):
        return "Password must be alphanumeric ❌"

    ref = db.reference('users')
    ref.child(username).update({
        "password": new_password
    })

    return "Password Updated Successfully ✅"

@app.route('/delete_account/<username>')
def delete_account(username):
    ref = db.reference('users')
    ref.child(username).delete()

    return "Account Deleted ❌"


@app.route('/settings/<username>')
def settings(username):
    return render_template('settings.html', username=username)

@app.route('/update_profile/<username>', methods=['POST'])
def update_profile(username):
    bio = request.form['bio']
    file = request.files['profile_pic']

    filename = ""

    if file and file.filename != "":
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        ref = db.reference('users')
        old = ref.child(username).get()
        filename = old.get("profile_pic", "default.png")

    ref = db.reference('users')
    ref.child(username).update({
        "bio": bio,
        "profile_pic": filename
    })

    return "Profile Updated ✅"

@app.route('/like/<post_id>')
def like(post_id):
    ref = db.reference(f'posts/{post_id}')
    post = ref.get()

    likes = post.get('likes', 0) + 1

    ref.update({
        "likes": likes
    })

    return jsonify({"likes": likes})


# -------------------- RUN --------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)