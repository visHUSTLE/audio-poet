import os
from dotenv import load_dotenv
from twilio.rest import Client
from flask import Flask, request, render_template, redirect, session, url_for
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import os
import uuid

import openai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, url_for
from gtts import gTTS
import wave
#import pymongo


load_dotenv()
app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
app.secret_key = 'not-so-secret-key'
app.config.from_object('settings')
#client = pymongo.MongoClient("mongodb://localhost:27017/")

#lyrics_collection = client["lyric_analytics"]["lyrics"]

UPLOAD_FOLDER = 'UPLOADS'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_EXTENSIONS'] = ['jpg', 'png', 'JPG', 'PNG']

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN= os.environ.get('TWILIO_AUTH_TOKEN')
VERIFY_SERVICE_SID= os.environ.get('VERIFY_SERVICE_SID')
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

KNOWN_PARTICIPANTS = app.config['KNOWN_PARTICIPANTS']

responses = {}


def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['UPLOAD_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        if username in KNOWN_PARTICIPANTS:
            session['username'] = username
            send_verification(username)
            return redirect(url_for('verify_passcode_input'))
        error = "User not found. Please try again."
        return render_template('index.html', error=error)
    return render_template('index.html')

def send_verification(username):
    phone = KNOWN_PARTICIPANTS.get(username)
    client.verify \
        .services(VERIFY_SERVICE_SID) \
        .verifications \
        .create(to=phone, channel='sms')
    


@app.route('/verifyme', methods=['GET', 'POST'])
def verify_passcode_input():
    username = session['username']
    phone = KNOWN_PARTICIPANTS.get(username)
    error = None
    if request.method == 'POST':
        verification_code = request.form['verificationcode']
        if check_verification_token(phone, verification_code):
            #return render_template('uploadpage.html', username = username)
            return render_template('lyrics.html')
        else:
            error = "Invalid verification code. Please try again."
            return render_template('verifypage.html', error=error)
    return render_template('verifypage.html', username=username)


def check_verification_token(phone, token):
    check = client.verify \
        .services(VERIFY_SERVICE_SID) \
        .verification_checks \
        .create(to=phone, code=token)    
    return check.status == 'approved'

@app.route("/get_response")
def get_response():
    message = request.args.get("message")
    completion = openai.ChatCompletion.create(
        # You can switch this to `gpt-4` if you have access to that model.
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}],
    )
    # response = completion["choices"][0]["message"]["content"]
    # print(response)
    response = completion["choices"][0]["message"]["content"]
    response_id = uuid.uuid4().hex
    responses[response_id] = response
    filename = f"{response_id}.mp3"
    filepath = os.path.join("venv\static", filename)
    tts = gTTS(response)
    tts.save(filepath)

    #document = {response_id: response}
    #lyrics_collection.insert_one(document)

    return jsonify({"id": response_id, "text": response, "audio_url": url_for('static', filename=filename)})

# @app.route('/upload')
# def upload_file():
#    return render_template('uploadpage.html')
        
# @app.route('/uploader', methods=['GET', 'POST'])
# def submitted_file():
#    username = "vishnu"  #session['username']
#    if request.method == 'POST':
#       f = request.files['file']
#       if f and allowed_file(f.filename):
#          f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
#          return render_template('success.html',  username=username)
#       else:
#          error = "Please upload a valid file."
#          return render_template('uploadpage.html', username = username, error = error)
