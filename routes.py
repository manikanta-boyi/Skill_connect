from extensions import db
from flask import render_template,redirect,flash,url_for,request,Blueprint, current_app # Import current_app
from models import User, Requirements, Bid
from forms import RegistrationForm,LoginForm,RequirementForm,BidForm
from flask_login import login_required,current_user,login_user,logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from google.cloud import speech_v1p1beta1 as speech # Or just speech if you prefer

import base64
import uuid
import os
import io

# REMOVE or COMMENT OUT this global UPLOAD_FOLDER definition
# if you are defining it in app.config as recommended.
# If you keep it here, ensure it's still correct.
# UPLOAD_FOLDER = 'static/audio_uploads'
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)


main =Blueprint('main',__name__)

# Helper function for AI transcription
def transcribe_audio(file_path):
    client = speech.SpeechClient()

    # Read the audio file
    with io.open(file_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        # CRITICAL CHANGE: Use OGG_OPUS for webm from frontend
        encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=48000, # Ensure this matches what MediaRecorder provides (often 48000Hz default for webm)
        language_code="en-US",
    )

    try:
        operation = client.long_running_recognize(config=config, audio=audio)
        print("Waiting for operation to complete...")
        response = operation.result(timeout=300) # Increased timeout for larger files
        
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        return transcript

    except Exception as e:
        print(f"Google Speech-to-Text API Error: {e}")
        # Return a clear error message instead of re-raising
        return f"Transcription Error: {e}"

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
        if user and user.check_password(form.password.data): # Assumes check_password is a method on User model
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html',form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main.route('/requirement',methods=['GET','POST'])
@login_required
def post_requirement():
    if current_user.role != 'user':
        flash('Only users can post requirements.', 'warning')
        return redirect(url_for('main.dashboard'))
    form = RequirementForm()
    if form.validate_on_submit():
        voice_file_path_db = None # Renamed to clearly indicate this is for DB storage
        voice_transcription = None

        if form.voice_recording.data:
            base64_audio = form.voice_recording.data
            
            if "," in base64_audio:
                header, encoded_data = base64_audio.split(',', 1)
                
                # Infer extension from the MIME type in the header
                mime_type_part = header.split(":", 1)[1]
                mime_type = mime_type_part.split(";", 1)[0]
                
                file_extension = ".webm" # Default to .webm as our JS sends this
                if "audio/wav" in mime_type:
                    file_extension = ".wav"
                elif "audio/mpeg" in mime_type or "audio/mp3" in mime_type:
                    file_extension = ".mp3"
                # Add more conditions if you expect other mime types

                try:
                    audio_data = base64.b64decode(encoded_data)
                    filename = f"req_voice_{uuid.uuid4().hex}{file_extension}"
                    
                    # Access UPLOAD_FOLDER from current_app.config
                    upload_folder = current_app.config.get('UPLOAD_FOLDER')
                    if not upload_folder:
                        raise ValueError("UPLOAD_FOLDER not configured in current_app.config")
                    
                    os.makedirs(upload_folder, exist_ok=True) # Ensure directory exists
                    full_file_path = os.path.join(upload_folder, filename)
                    
                    with open(full_file_path, 'wb') as f:
                        f.write(audio_data)
                    print(f"Audio file saved to: {full_file_path}")

                    # --- CRUCIAL CHANGE HERE: Store relative path for DB ---
                    # The UPLOAD_FOLDER is typically 'path/to/project/static/audio_uploads'
                    # We want to store 'audio_uploads/filename.webm' in the DB
                    # os.path.basename(upload_folder) will give 'audio_uploads'
                    # Then join with the filename
                    voice_file_path_db = os.path.join(os.path.basename(upload_folder), filename)
                    # Convert to forward slashes for URL compatibility, regardless of OS
                    voice_file_path_db = voice_file_path_db.replace(os.path.sep, '/')
                    print(f"Path stored in DB: {voice_file_path_db}")

                    # Perform transcription - use the full_file_path as the transcription function needs it
                    voice_transcription = transcribe_audio(full_file_path)
                    print(f"Transcription: {voice_transcription}")

                except Exception as e:
                    print(f"Error processing voice recording for Requirement: {e}")
                    flash(f"Error processing voice recording: {e}", 'danger')
                    voice_file_path_db = None # Ensure it's None on error
                    voice_transcription = f"Transcription Error: {e}" # Store error message

            else:
                flash("Invalid voice recording data format.", 'warning')
                print("Invalid base64_audio format for Requirement. No comma found.")
        else:
            print("No voice recording data provided for requirement.")


        req = Requirements(title=form.title.data,
                           description=form.description.data,
                           skill_needed = form.skill_needed.data,
                           location=form.location.data,
                           user_id = current_user.id,
                           voice_file_path = voice_file_path_db, # Use the new DB-friendly path
                           voice_transcription = voice_transcription)
        db.session.add(req)
        db.session.commit()
        flash('Requirement posted successfully.', 'success')

        return redirect(url_for('main.dashboard'))
    return render_template('post_requirement.html', form=form)


@main.route('/requirements')
@login_required
def requirements():
    if current_user.role=='skilled':
        reqs = Requirements.query.filter_by(skill_needed=current_user.skill).all()
    else:
        reqs = Requirements.query.filter_by(user_id=current_user.id).all()
    return render_template('requirements.html',reqs=reqs)

@main.route('/requirement/<int:req_id>/bid',methods=['GET','POST'])
@login_required
def bid(req_id):
    req = Requirements.query.get_or_404(req_id)
    if current_user.role != 'skilled':
        flash('Unauthorized to bid.', 'warning')
        return redirect(url_for('main.requirements'))
    form = BidForm()
    if form.validate_on_submit():
        voice_file_path_db = None # Renamed for clarity
        voice_transcription = None

        if form.voice_recording.data:
            base64_audio = form.voice_recording.data
            
            if "," in base64_audio:
                header, encoded_data = base64_audio.split(',', 1)
                
                # Infer extension from the MIME type in the header
                mime_type_part = header.split(":", 1)[1]
                mime_type = mime_type_part.split(";", 1)[0]
                
                file_extension = ".webm" # Default to .webm
                if "audio/wav" in mime_type:
                    file_extension = ".wav"
                elif "audio/mpeg" in mime_type or "audio/mp3" in mime_type:
                    file_extension = ".mp3"

                try:
                    audio_data = base64.b64decode(encoded_data)
                    filename = f"bid_voice_{uuid.uuid4().hex}{file_extension}"
                    
                    # Access UPLOAD_FOLDER from current_app.config
                    upload_folder = current_app.config.get('UPLOAD_FOLDER')
                    if not upload_folder:
                        raise ValueError("UPLOAD_FOLDER not configured in current_app.config")

                    os.makedirs(upload_folder, exist_ok=True) # Ensure directory exists
                    full_file_path = os.path.join(upload_folder, filename)
                    
                    with open(full_file_path, 'wb') as f:
                        f.write(audio_data)
                    print(f"Audio file saved to: {full_file_path}")

                    # --- CRUCIAL CHANGE HERE: Store relative path for DB ---
                    voice_file_path_db = os.path.join(os.path.basename(upload_folder), filename)
                    voice_file_path_db = voice_file_path_for_db.replace(os.path.sep, '/')
                    print(f"Path stored in DB: {voice_file_path_db}")

                    voice_transcription = transcribe_audio(full_file_path) # Pass full path to transcription
                    print(f"Transcription: {voice_transcription}")

                except Exception as e:
                    print(f"Error processing bid voice recording: {e}")
                    flash(f"Error processing bid voice recording: {e}", 'danger')
                    voice_file_path_db = None # Ensure None on error
                    voice_transcription = f"Transcription Error: {e}" # Store error message
            else:
                flash("Invalid voice recording data format.", 'warning')
                print("Invalid base64_audio format for Bid. No comma found.")
        else:
            print("No voice recording data provided for bid.")

        bid_obj = Bid(price = form.price.data,
                      comment=form.comment.data,
                      requirement=req,
                      bidder = current_user,
                      voice_file_path = voice_file_path_db, # Use the new DB-friendly path
                      voice_transcription = voice_transcription)
        db.session.add(bid_obj)
        db.session.commit()
        flash('Your bid has been submitted!', 'success')
        return redirect(url_for('main.requirements'))
    return render_template('bid.html',form=form,req=req)


@main.route('/requirement/<int:req_id>/bids')
@login_required
def view_bids(req_id):
    req = Requirements.query.get_or_404(req_id)
    # Check if current_user is the poster (owner) of the requirement
    if current_user.id != req.user_id: # Use user_id for comparison
        flash('Unauthorized to view bids for this requirement.', 'warning')
        return redirect(url_for('main.dashboard'))
    return render_template('bids.html',bids=req.bids,req=req)

# New Route: To view detailed bid information including voice transcripts and confirmation buttons
@main.route('/requirement/<int:req_id>/bid_details/<int:bid_id>', methods=['GET', 'POST'])
@login_required
def view_bid_details(req_id, bid_id):
    req = Requirements.query.get_or_404(req_id)
    bid = Bid.query.get_or_404(bid_id)

    # Ensure this bid belongs to this requirement
    if bid.requirement_id != req.id:
        flash('Bid does not belong to this requirement.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Only the requirement poster or the bidder can view/confirm this page
    if current_user.id != req.user_id and current_user.id != bid.bidder_id: # Use IDs for comparison
        flash('Unauthorized to view these bid details.', 'warning')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'confirm_agreement':
            if current_user.id == req.user_id: # Poster confirms
                bid.status = 'accepted_by_poster'
                flash('You have accepted this bid. Waiting for bidder to confirm the agreement.', 'success')
            elif current_user.id == bid.bidder_id: # Bidder confirms
                if bid.status == 'accepted_by_poster':
                    bid.status = 'agreed'
                    req.status = 'in_progress' # Update requirement status
                    flash('Agreement confirmed! Work is now in progress.', 'success')
                else:
                    flash('Requirement poster has not yet accepted this bid.', 'warning')
            else:
                flash('You are not authorized to confirm this agreement.', 'danger')

            db.session.commit()
            return redirect(url_for('main.dashboard')) # Redirect to a relevant page after action

        elif action == 'reject_bid' and current_user.id == req.user_id: # Only poster can reject
            bid.status = 'rejected'
            db.session.commit()
            flash('Bid has been rejected.', 'info')
            return redirect(url_for('main.view_bids', req_id=req.id))


    return render_template('confirm_agreement.html', req=req, bid=bid)
