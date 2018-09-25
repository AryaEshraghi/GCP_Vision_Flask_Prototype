from flask import Flask, request, flash, redirect, render_template
from werkzeug.utils import secure_filename
import os
import requests
import json
import base64

ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
API_KEY = ""
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'raw',
                          'ico', 'pdf', 'tiff'])

app = Flask(__name__)
app.config.from_mapping(SECRET_KEY='dev')
# File size limit set to 10mb
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index.html', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if file part is present
        if 'file' not in request.files:
            flash('No file part')
            return (redirect(request.url))
        file = request.files['file']
        # Check to see if user has selected a file for upload
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        # If all goes well, the top five labels and scores are passed to the
        # result table
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            res = request_labels(file)
            if 'error' in res.keys():
                flash('Failed to retrieve labels')
                return (redirect(request.url))
            labels, scores = [], []
            labels = [elem['description'] for elem in res['responses'][0]['labelAnnotations']]
            scores = [elem['score'] for elem in res['responses'][0]['labelAnnotations']]
            return (render_template('results.html', labels=labels, scores=scores))
    return (render_template('index.html'))

def allowed_file(filename):
    """
    Ensure that all files are of the appropriate type by extension
    """
    return ('.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

def encode_image(image):
    """
    Encode uploaded image first as 64bit byte type, and then as ascii
    """
    image_content = image.read()
    byteenc = base64.b64encode(image_content)
    return (byteenc.decode('ascii'))

def request_labels(image):
    """
    Attempt to retrieve labels from Google Vision API
    """
    image_base64 = encode_image(image)
    img_request = {"requests": [{
                                'image': {'content': image_base64},
                                'features': [{
                                    'type': 'LABEL_DETECTION',
                                    'maxResults': 5
                                    }]
                                }]
                   }
    res = requests.post(ENDPOINT_URL,
                             data = json.dumps(img_request),
                             params = {'key': API_KEY},
                             headers = {'Content-Type': 'application/json'})
    return (res.json())
