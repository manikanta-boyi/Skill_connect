from extensions import db
from flask import render_template,redirect,flash,url_for,request,Blueprint
from models import User, Requirements, Bid
from forms import RegistrationForm,LoginForm,RequirementForm,BidForm
from flask_login import login_required,current_user,login_user,logout_user
from werkzeug.security import generate_password_hash, check_password_hash


main =Blueprint('main',__name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw,
                    role=form.role.data, skill=form.skill.data, location=form.location.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html',form =form)


@main.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password,form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html',form=form)
    
@main.route('/logout')
def logout():
    login_user()
    return redirect('main.index')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main.route('/requirement',methods=['GET','POST'])
@login_required
def post_requirement():
    if current_user.role != 'user':
        flash('Only users can post requirements.', 'warning')
        return render_template('dashboard.html')
    form = RequirementForm()
    if form.validate_on_submit():
        req = Requirements(title=form.title.data,
                           description=form.description.data,
                           skill_needed = form.skill_nedded.data,
                           location=form.location.data,
                           user_id = current_user.id)
        db.session.add(req)
        db.session.commit()
        flash('Requirement posted successfully.', 'success')

        return redirect(url_for('main.dashboard'))
    return render_template('post_requirement.html')


@main.route('/requrements')
@login_required
def requirements():
    if current_user.role=='skilled':
        reqs = Requirements.query.filter_by(skill_needed=current_user.skill).all()
    else:
        reqs = Requirements.query.filter_by(user_id=current_user.id).all()
    return render_template('requirements.html',reqs=reqs)

@main.route('/requrement/<int:req_id>/bid',methods=['GET','POST'])
@login_required
def bid(req_id):
    req = Requirements.query.get_or_404(req_id)
    if current_user.role != 'skilled':
        flash('Unautherized','warning')
        return redirect(url_for('main.requirements'))
    form = BidForm()
    if form.validate_on_submit():
        bid = Bid(price = form.price.data,
                  coment=form.comment.data,
                  requirement=req,
                  bidder = current_user)
        db.session.add(bid)
        db.session.commit()
        return redirect(url_for('main.requirements'))
    return render_template('bid.html',form=form,req=req)
@main.route('/requirement/<int:req_id>/bids')
@login_required
def view_bids(req_id):
    req = Requirements.query.get_or_404(req_id)
    if current_user != req.poster:
        flash('Unoutherized','warning')
        return redirect(url_for('main.dashboard'))
    return render_template('bids.html',bids=req.bids,req=req)

