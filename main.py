from flask import Flask, render_template, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user

app = Flask(__name__)
saved_position = {}
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CREATE Users TABLE IN DB
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    task = relationship("Task", back_populates="task_item")


# Task TABLE Configuration
class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(250), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.String(500), nullable=False)
    end_date = db.Column(db.String(250), nullable=False)
    top_position = db.Column(db.Integer, nullable=True)
    column = db.Column(db.Integer, nullable=True)
    task_item = relationship("User", back_populates="task")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# db.create_all()
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        response = request.form.to_dict()
        if response:
            if "signName" in response:
                print(response)
                if User.query.filter_by(email=response["signEmail"]).first():
                    # User already exists
                    flash("You've already signed up with that email, log in instead!")
                else:
                    salted_password = generate_password_hash(response["signPassword"],
                                                             method='pbkdf2:sha256',
                                                             salt_length=8)
                    new_user = User(email=response["signEmail"],
                                    password=salted_password,
                                    name=response["signName"],
                                    )
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user)
            elif "loginEmail" in response:
                print(response)
                # Find user by email entered.
                user = User.query.filter_by(email=response["loginEmail"]).first()
                if not user:
                    # User already exists
                    flash("that email do not exist, please try again.!")
                    print("that email do not exist, please try again.!")
                # Check stored password hash against entered password hashed.
                elif not check_password_hash(user.password, response["loginPassword"]):
                    flash('Password incorrect, please try again.')
                    print("Password incorrect, please try again.!")
                else:
                    login_user(user)
            else:
                if current_user.is_authenticated:
                    new_task = Task(name=response["name"],
                                    user_id=current_user.id,
                                    description=response["description"],
                                    start_date=response["start"],
                                    end_date=response["end"],
                                    column=1,
                                    )
                    db.session.add(new_task)
                    db.session.commit()
    # tasks = Task.query.all()
    if current_user.is_authenticated:
        tasks_col_1 = db.session.query(Task).filter_by(column=1, user_id=current_user.id).all()
        tasks_col_2 = db.session.query(Task).filter_by(column=2, user_id=current_user.id).order_by(Task.top_position)
        tasks_col_3 = db.session.query(Task).filter_by(column=3, user_id=current_user.id).order_by(Task.top_position)
        return render_template("index.html", tasks_column_1=tasks_col_1,
                               tasks_column_2=tasks_col_2,
                               tasks_column_3=tasks_col_3,
                               logged_in=current_user.is_authenticated)
    else:
        return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route("/post", methods=['GET', 'POST'])
def post():
    global saved_position
    response = request.get_json()
    saved_position[response["id"]] = response
    return redirect(url_for('home'))


@app.route("/save")
def save_position():
    global saved_position
    # serialize the re-ordered list here by changing the item MenuItem id
    # in sqlalchemy to make it match the order of the re-ordered list
    for task in saved_position:
        task_from_db = db.session.query(Task).get(task)
        task_from_db.column = saved_position[task]["column"]
        task_from_db.top_position = saved_position[task]["top"]
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
