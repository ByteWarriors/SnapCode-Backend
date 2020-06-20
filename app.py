import os

from flask import Flask,jsonify,request
import requests

app = Flask(__name__)

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

@app.route('/run-code', methods = ['GET','POST'])
def runEndpoint():
    if request.method == 'POST':
        source = request.json['source']
        lang = request.json['lang']
        resp = runCode(source,lang)
        send_res = {}
        send_res['compile_status'] = resp['compile_status']
        if 'output' not in resp['run_status'].keys():
            send_res['output'] = None
        else:
            send_res['output'] = resp['run_status']['output']
        send_res['status'] = resp['run_status']['status']
        send_res['status_detail'] = resp['run_status']['status_detail']
        return jsonify(send_res)
    else:
        return jsonify({'message': "Send a POST request"})



if __name__ == '__main__':
    app.run(debug=True)
