from flask import Flask
from extensions import db, login_manager,mail,migrate
import os

from routes import main



app = Flask(__name__)

app.config['SECRET_KEY']= 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=587
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']= os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')



db.init_app(app)
migrate.init_app(app,db)
login_manager.init_app(app)
login_manager.login_view = 'main.login'
mail.init_app(app)

from models import User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(main)


if __name__=='__main__':
    app.run(debug=True)
