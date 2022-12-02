from flask import Flask, request, render_template, send_from_directory
from flask_restful import Api, Resource, reqparse, abort, marshal_with, fields
#from flask_sqlalchemy import SQLAlchemy

#from flask_wtf import FlaskForm
#from wtforms import FileField, SubmitField
#from wtforms.validators import InputRequired
from werkzeug.utils import secure_filename
import os

import qrcode_make
import ranged_splitter

app = Flask(__name__)
api = Api(app)
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + DATABASE_NAME
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.route('/', methods=['GET'])
@app.route('/upload', methods=['POST', 'GET'])
def get_home_message():
    msg = '''
        You've reached the main page : QRCode Generator
    '''
    return msg

@app.route('/qrcode/<string:user>/<int:count>/<int:length>')
def generate_codes(user:str, count:int, length:int):
    state = qrcode_make.generate_qrcodes(from_=1, to_=count, totalLength=10, batch=5000, outfolder='output', root='.')
    if state == qrcode_make.SUCCESS:
        # split into folders and form csvs
        ranged_splitter.split_into_folders(from_folder='output', start=1, end=count, split_size=1000, include_csv=True, csvname='qrCode.csv', tl=length)
        return "OPERATION DONE"
    elif state ==  qrcode_make.FAILED_CREATE_PATH:
        return "FATAL ERROR @create path"
    elif state == qrcode_make.LOOP_FAILED:
        return "FATAL ERROR @ loop"
    return "ERROR"

@app.route('/progress/<string:user>/<int:count>/<int:length>')
def get_progress(user:str, count:int, length:int):
    pass

def clean_after_self():
    '''
    delete files after 24hrs
    '''
    pass

if __name__ == "__main__":
    app.run(debug=True)
