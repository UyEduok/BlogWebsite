from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, CreateUserForm, ContactForm
from flask_gravatar import Gravatar
from send_mail import SendMail
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.login_view = 'login'  # Redirect to 'login' if user is not authenticated
login_manager.init_app(app)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(50), nullable=True)
    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="commenter_user")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="commenter_blog")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # ForeignKey to link comments to users (commenters)
    commenter_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # ForeignKey to link comments to blog posts
    blog_post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    # Relationship with the User table (commenter)
    commenter_user = relationship("User", back_populates="comments")
    # Relationship with the BlogPost table (the post being commented on)
    commenter_blog = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Function to set the first user as Admin
def ensure_first_user_admin():
    with app.app_context():
        # Query to find the user with ID 1
        first_user = db.session.execute(db.select(User).where(User.id == 1)).scalars().first()

        if first_user:
            current_role = first_user.role  # Get the current role
            if current_role != 'Admin':  # Check if the role is not Admin
                # Update the role to Admin
                db.session.execute(
                    db.update(User)
                    .where(User.id == 1)
                    .values(role='Admin')
                )
                db.session.commit()  # Commit the changes


# Convert the first user to an admin
ensure_first_user_admin()

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    form_create_user = CreateUserForm()
    if form.validate_on_submit():
        email = form.email.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        # confirm the first user is an Admin
        ensure_first_user_admin()
        role = form_create_user.role.data if current_user.is_authenticated and current_user.role == "Admin" else "User"
        if user:
            if current_user.is_authenticated and current_user.role == "Admin":
                flash("Email already exist, register a new User")
                return redirect(url_for("register"))

            flash("Email already exists, login instead")
            return redirect(url_for("login"))
        else:
            hash_and_salted_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )

            new_user = User(
                email=email,
                name=form.name.data.title(),
                password=hash_and_salted_password,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()

            if current_user.is_authenticated and current_user.role == "Admin":
                flash(f"User successfully registered as a {role}, do you wish to register another user?")
                return redirect(url_for("register"))

            login_user(new_user)
            return redirect(url_for("get_all_posts"))
    return render_template(
        "register.html",
        form=form,
        create_user_form=form_create_user,
        current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('get_all_posts'))
            else:
                flash("Incorrect password!")
                return redirect(url_for("login"))
        else:
            flash(f"No account registered with {form.email.data}")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template(
        "index.html",
        all_posts=posts,
        logged_in=current_user.is_authenticated,
        current_user=current_user
    )


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    post_comment = db.session.execute(db.select(Comment).where(Comment.blog_post_id == post_id)
                                      ).scalars().all()
    # Only allow logged-in users to comment on posts
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=form.comment.data,
            commenter_user=current_user,
            commenter_blog=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))
    return render_template(
        "post.html",
        post=requested_post,
        logged_in=current_user.is_authenticated,
        current_user=current_user,
        form=form,
        comments=post_comment
    )


def admin_and_sub_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.role != "Admin" and current_user.role != "Sub_admin":
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_and_sub_admin
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template(
        "make-post.html",
        form=form,
        logged_in=current_user.is_authenticated,
        current_user=current_user
    )


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_and_sub_admin
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template(
        "make-post.html",
        form=edit_form, is_edit=True,
        logged_in=current_user.is_authenticated,
        current_user=current_user
    )


@app.route("/delete/<int:post_id>")
@login_required
@admin_and_sub_admin
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template(
        "about.html",
        logged_in=current_user.is_authenticated,
        current_user=current_user
    )


@app.route('/delete_comment/<int:comment_id>', methods=['DELETE'])
@admin_and_sub_admin
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment:
        db.session.delete(comment)
        db.session.commit()
        return '', 204  # No Content
    return '', 404  # Not Found


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    msg_sent = False
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        phone = form.phone.data if form.phone.data else "No phone number provided"
        message = f"""
{form.message.data}\n\n
Message From:
    {name}\n
    {email}\n
    {phone}
"""
        print(name, email, phone, message)
        msg_sent = True
        SendMail().send_email(message)
        return redirect(url_for("contact", msg_sent=msg_sent))
    print(msg_sent)
    return render_template(
        "contact.html",
        logged_in=current_user.is_authenticated,
        current_user=current_user,
        form=form,
        msg_sent=msg_sent
    )


if __name__ == "__main__":
    app.run(debug=False)
