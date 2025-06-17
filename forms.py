from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,SelectField
from wtforms.validators import DataRequired,Email,EqualTo


class RegistrationForm(FlaskForm):
    username = StringField('Enter username',validators=[DataRequired()])
    email = StringField('Enter email',validators=[DataRequired(),Email()])
    password = PasswordField('Enter password',validators=[DataRequired()])
    confirm_password = PasswordField('Confirm password',validators=[DataRequired(),EqualTo('password')])
    role = SelectField('Role',choices=[('user','User'),('skilled','Skilled person')],validators=[DataRequired()])
    skill = StringField('Skill(if Skilled person)')
    location = StringField('Location',validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Enter your email',validators=[DataRequired(),Email()])
    password = PasswordField('Enter Password',validators=[DataRequired()])
    submit = SubmitField('Login')