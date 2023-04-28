import uvicorn
from fastapi import FastAPI, status
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Generator
import os
import apiutils
import utils
import threading
import re
import time
import logging

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
    qr_s_length:int
    csv_s_length:int
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
    qr_s_length = req.qr_s_length
    csv_s_length = req.csv_s_length
    pre_string = req.pre_string
    pro_string = req.pro_string
    overwrite = req.overwrite
    overwrite = (overwrite==1)
    
    username = utils.get_hash(user)
    if not overwrite and apiutils.is_active(username):
        msg =  "Requests for this user are still active, set overwrite!"
        return msg
    # cancel active request
    user_obj = apiutils.get_user_object(username)
    if user_obj is not None:
        user_obj.cancel()
    # create new generation
    qrgen = apiutils.get_generator(username)
    apiutils.add_active_request(username, qrgen)

    generate_fn = lambda : qrgen.generate(start_number=start, limit=count, qr_serial_length=qr_s_length, 
                        csv_serial_length=csv_s_length, pre_string=pre_string, pro_string=pro_string)
    try:
        thread = threading.Thread(target=generate_fn, args=())
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
    qr_s_length = req.qr_s_length
    csv_s_length = req.csv_s_length
    pre_string = req.pre_string
    pro_string = req.pro_string
    overwrite = req.overwrite
    overwrite = overwrite == 1
    # warn subfolder exists?
    out = ''
    first =  start
    end = first + count-1
    first_str, end_str =  '', ''
    if qr_s_length > 0:
        first_str = str(first).zfill(qr_s_length)
        end_str = str(end).zfill(qr_s_length)
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
    # returns a list to currently available zip files
    username = utils.get_hash(user)
    user_obj = apiutils.get_user_object(username)
    if user_obj is None:
        return status.HTTP_404_NOT_FOUND

    userfolder = user_obj.targetfolder
    files = os.listdir(userfolder)
    downloadables = [(file, "{}/{}".format(username,file)) for file in files if len(re.findall('^\d+_\d+\.zip$', file))>0] 
    return downloadables

def get_data_from_file(file_path: str) -> Generator:
    with open(file=file_path, mode="rb") as file_like:
        yield file_like.read()

@app.get('/download/{user}/{file}')
async def download(user : str, file:str):
    try:
        username = utils.get_hash(user)
        user_obj = apiutils.get_user_object(username)
        if user_obj is None:
            return status.HTTP_404_NOT_FOUND
        dl_file = os.path.join(user_obj.targetfolder, file)
        if os.path.exists(dl_file):
            file_contents = get_data_from_file(file_path=dl_file)
            response = StreamingResponse(
                content=file_contents,
                status_code=status.HTTP_200_OK,
                media_type="application/octet-stream"
            )
            # media_type="application/x-zip-compressed",
            #headers = { "Content-Disposition":f"attachment;filename={}".format(file)}
            return response
        return status.HTTP_404_NOT_FOUND
    except FileNotFoundError:
        raise HTTPException(detail="File not found.", status_code=status.HTTP_404_NOT_FOUND)

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
    if user_obj.is_complete():
        return "No active task to cancel!"
    user_obj.cancel()
    return "Task cancelled by user!"

def clean_after_self(days_time=30):
    '''
    delete files after time
    '''
    # if folder.time.diff(current) >= days_time
    # handled by database time logger
    pass

if __name__ == "__main__":
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.disabled=True
    uvicorn.run(app, host='0.0.0.0', port=8000)