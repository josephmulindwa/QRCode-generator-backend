import uvicorn
from fastapi import FastAPI, status
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import apiutils
import utils
import threading
import re
import time

app = FastAPI()
apiutils.setup()
apiutils.log('Server stated :', key="STARTED")

origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
    )

class GenerateRequest(BaseModel):
    '''class for generate request'''
    user:str
    start:int
    count:int
    length:int
    pre_string:str
    pro_string:str
    overwrite:int

@ app.get('/')
def get_home_message():
    html = None
    with open(os.path.join(apiutils.ROOT, apiutils.APP_FOLDER, 'home.html')) as fr:
        html = fr.read()
    return HTMLResponse(content=html, status_code=200)

@app.post('/generate')
async def generate_codes(req : GenerateRequest):
    apiutils.log(str(req))
    user = req.user
    start = req.start
    count = req.count
    length = req.length
    pre_string = req.pre_string
    pro_string = req.pro_string
    overwrite = req.overwrite
    overwrite = (overwrite==1)
    
    username = utils.get_hash(user)
    if not overwrite and apiutils.is_active(username):
        msg =  "Requests for this user are still active!"
        return msg
    qrgen = apiutils.QRCodeGenerator(username)
    apiutils.add_active_request(username, qrgen)

    generate_fn = lambda : qrgen.generate(start_number=start, limit=count, serial_length=length, pre_string=pre_string, pro_string=pre_string)
    try:
        thread = threading.Thread(target=generate_fn, args=())
        print("starting thread")
        thread.start()
        apiutils.log('{} : Generation started'.format(username))
        return 'Generation started.'
    except Exception as e:
        msg = "Error @api.generate : {}".format(e)
        apiutils.log(msg, key='error')
        print(msg)
        return 'Server error! Oops, a critical error occured on our end.'

@app.get('/progress/{user}')
async def get_progress(user : str):
    # returns the progress of a specific user
    username = utils.get_hash(user)
    user_obj = apiutils.get_user_object(username)
    if user_obj is None:
        return status.HTTP_404_NOT_FOUND
    return {"progress":user_obj.progress, "total":user_obj.total}

@app.post('/stringsample')
async def get_string_samples(req : GenerateRequest):
    '''returns sample string depending on stats'''
    user = req.user
    start = req.start
    count = req.count
    length = req.length
    pre_string = req.pre_string
    pro_string = req.pro_string
    overwrite = req.overwrite
    overwrite = overwrite == 1
    # warn subfolder exists?
    out = ''
    first =  start
    end = first + count-1
    first_str, end_str =  '', ''
    if length > 0:
        first_str = str(first).zfill(length)
        end_str = str(end).zfill(length)
    elif length < 0:
        first_str = str(first)
        end_str = str(end)
    first_string = pre_string + str(first_str) + pro_string
    out += first_string
    if end > first:
        end_string = pre_string + str(end_str) + pro_string
        out += '\n...\n' + end_string
    return out 

@app.post('/login')
async def login():
    # login page & token generator
    pass

@app.get('/downloads/{user}')
async def get_downloads(user : str):
    # returns a list to downloadable zip files
    username = utils.get_hash(user)
    user_obj = apiutils.get_user_object(username)
    if user_obj is None:
        return status.HTTP_404_NOT_FOUND
    
    #workingpath = os.path.join(apiutils.ROOT, apiutils.WORKING_FOLDER, hashed)
    #if progress > apiutils.FOLDER_BATCH or (progress/total) == 1: # there are some folders ready
    #    folders = os.listdir(workingpath) # find the folders
    #    zip_cache = [(folder, hashed+'/'+folder) for folder in folders if len(re.findall('^\d+_\d+\.zip$', folder)) > 0]
    return "still in progress"

@app.get('/download/{user}/{folder}')
async def download(user : str, folder:str):
    username = utils.get_hash(user)
    user_obj = apiutils.get_user_object(username)
    if user_obj is None:
        return status.HTTP_404_NOT_FOUND
    zip_file = os.path.join(user_obj.targetfolder, folder)
    if os.path.exists(zip_file):
        return FileResponse(path=zip_file, media_type='application/octet-stream', filename=folder)
    return status.HTTP_404_NOT_FOUND

@app.get('/cancel/{user}')
async def cancel_generation(user : str):
    '''cancels tasks being handled by this user'''
    username = utils.get_hash(user)
    user_obj = apiutils.get_user_object(username)
    if user_obj is None:
        return status.HTTP_404_NOT_FOUND
    user_obj.cancel()
    return "Task cancelled by user!"

def clean_after_self(days_time=30):
    '''
    delete files after time
    '''
    # if folder.time.diff(current) >= days_time
    pass

if __name__ == "__main__":
    uvicorn.run(app)
