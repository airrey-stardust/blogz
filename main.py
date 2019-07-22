from flask import Flask, redirect, request, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
#### use 3306 port #####
#######################

app.secret_key = 'abcde'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    content = db.Column(db.Text())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pub_date = db.Column(db.DateTime)

    def __init__(self, title, content, owner):
        self.title = title
        self.content = content
        self.owner = owner

#######################

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref = 'owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


#################################

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index', 'blog_listing']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

#########################

@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html', users = users)

##################################

@app.route('/blog', methods=['POST', 'GET'])
def blog_listing():
    title = "Build a Blog"

    if session:
        owner = User.query.filter_by(username = session['username']).first()

    if "id" in request.args:
        post_id = request.args.get('id')
        blog = Blog.query.filter_by(id = post_id).all()
        owner = User.query.get(owner.username)
        return render_template('blogs.html', title = title, blog = blog, post_id = post_id)

    elif "user" in request.args:
        user_id = request.args.get('user')
        blog = Blog.query.filter_by(owner_id = user_id).all()
        return render_template('blogs.html', title = title, blog = blog)

    else:
        blog = Blog.query.order_by(Blog.id.desc()).all()
        return render_template('blogs.html', title = title, blog = blog)

######################

@app.route('/login', methods=['POST', 'GET'])
def login():
    username = ""
    username_error = ""
    password_error = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()

        if not user:
            username_error = "Error: User does not exist."
            if username == "":
                username_error = "Error: Please enter your username."

        if password == "":
            password_error = "Error:Please enter your password."

        if user and user.password != password:
            password_error = "That is the wrong password."

        if user and user.password == password:
            session['username'] = username
            return redirect('/newpost')

    return render_template('login.html', username = username, username_error = username_error, password_error = password_error)

###############################

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    username = ""
    username_error = ""
    password_error = ""
    verify_error = ""

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username = username).first()

        if (len(username) < 3) or (len(username) > 20):
            username_error = "Usernames must be between 3 and 20 characters in length."
            if username == "":
                username_error = "Please create a username."

        if password != verify:
            password_error = "Passwords must match."
            verify_error = "Passwords must match."
            
        if (len(password) < 3) or (len(password) > 20):
            password_error = "Password must be between 3 and 20 characters in length."
            if password == "":
                password_error = "Please enter a valid password."

        if password != verify:
            password_error = "Passwords must match."
            verify_error = "Passwords must match."

        if not username_error and not password_error and not verify_error:
            if not existing_user:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                return redirect('/newpost')
            else:
                username_error = "This username is already taken."

    return render_template('signup.html', username = username, username_error = username_error, password_error = password_error, verify_error = verify_error)

########################################3
@app.route('/newpost', methods=['POST', 'GET'])
def create_new_post():
    blog_title = ""
    blog_content = ""
    title_error = ""
    content_error = ""
    owner = User.query.filter_by(username = session['username']).first()

    if request.method == 'POST':
        blog_title = request.form['blog_title']
        blog_content = request.form['blog_content']

        if blog_title == "":
            title_error = "Please enter a title"

        if blog_content == "":
            content_error = "Please write a post. Content can not be blank."

        if title_error == "" and content_error == "":
            new_post = Blog(blog_title, blog_content, owner)
            db.session.add(new_post)
            db.session.commit()
            blog_id = Blog.query.order_by(Blog.id.desc()).first()
            user = owner

            return redirect('/blog?id={}&user={}'.format(blog_id.id, user.username))

    return render_template('newpost.html', title = "Create new post", blog_title = blog_title, blog_content = blog_content, title_error = title_error, content_error = content_error)


##############################
@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

#########################

if __name__ == "__main__":
    app.run()