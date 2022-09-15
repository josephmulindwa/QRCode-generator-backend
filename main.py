import uvicorn
from typing import Union
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import qrcode_make
import ranged_splitter

app = FastAPI()

origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
    )

@ app.get('/')
def get_home_message():
    msg = '''
        You've reached the main page : QRCode Generator
    '''
    return HTMLResponse(content=msg, status_code=200)

@app.get('/qrcode/{user}/{count}/{length}')
async def generate_codes(user:str, count:int, length:int):
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

@app.get('/progress/{user}/{count}/{length}')
async def get_progress(user:str, count:int, length:int):
    pass

def clean_after_self():
    '''
    delete files after 24hrs
    '''
    pass


   
if __name__ == "__main__":
    uvicorn.run(app)
