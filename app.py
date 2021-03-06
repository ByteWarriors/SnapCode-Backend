import os

import boto3

from werkzeug.utils import secure_filename

s3client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('SECRET_KEY'),
    region_name='us-west-2'
    )

textractClient = boto3.client(
    'textract',
    aws_access_key_id=os.environ.get('ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('SECRET_KEY'),
    region_name='us-west-2'
)


from flask import Flask,jsonify,request, make_response

from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

app.config["IMAGE_UPLOADS"] = "./images"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]

RUN_URL = 'https://api.hackerearth.com/v3/code/run/'
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

def runCode(source,lang):
    data = {
        'client_secret': CLIENT_SECRET,
        'async': 0,
        'source': source,
        'lang': lang,
        'time_limit': 5,
        'memory_limit': 262144
    }

    r = requests.post(RUN_URL,data=data)
    return r.json()


def allowed_image(filename):

    # We only want files with a . in the filename
    if not "." in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

@app.route('/run-code', methods = ['GET','POST'])
def runEndpoint():
    if request.method == 'POST':
        statusCode = 200
        source = request.json['source']
        lang = request.json['lang']
        resp = runCode(source,lang)
        send_res = {}
        send_res['compile_status'] = resp['compile_status']
        if 'output' not in resp['run_status'].keys():
            send_res['output'] = None
            statusCode = 201
        else:
            send_res['output'] = resp['run_status']['output']
        send_res['status'] = resp['run_status']['status']
        send_res['status_detail'] = resp['run_status']['status_detail']
        print(send_res)
        res = make_response(jsonify(send_res),statusCode)
        res.headers['Access-Control-Allow-Origin'] = "*"
        return res
    else:
        return jsonify({'message': "Send a POST request"}),400

@app.route('/upload-image',methods = ['GET','POST'])
def upload():
    if request.method == 'POST':
        if request.files:
            print("IMAGE RECEIVED")
            image = request.files["image"]
            
            if (allowed_image(image.filename)):
                filename = secure_filename(image.filename)

                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))

                print("SAVED TO LOCAL FOLDER")
            else:
                return jsonify({'message':'Upload acceptable filetype'})

            with open(f'./images/{filename}','rb') as file:
                s3client.upload_fileobj(file,'snapcode-data',filename)
            
            if os.path.exists(f"./images/{filename}"):
                os.remove(f'./images/{filename}')
            
            response = textractClient.detect_document_text(
                Document = {
                    'S3Object': {
                        'Bucket': 'snapcode-data',
                        'Name': filename
                    }
                }
            )
            blocks = response['Blocks']

            OCRtext = ""

            for item in blocks:
                if 'Text' in item.keys() and item['BlockType'] == 'LINE':
                    OCRtext += item['Text'] + '\n'

            res = make_response({'OCRtext': OCRtext})
            res.headers['Access-Control-Allow-Origin'] = "*"

            return res
    else:
        return jsonify({'message':"Send a POST request"})


if __name__ == '__main__':
    app.run(debug=True)
