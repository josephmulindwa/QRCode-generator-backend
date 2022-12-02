import uvicorn
from fastapi import FastAPI, status
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import apiUtils
import threading
import re
import time

app = FastAPI()
apiUtils.log('Server stated :', clear=True, key="STARTED")

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
    with open(os.path.join(apiUtils.ROOT, apiUtils.APP_FOLDER, 'home.html')) as fr:
        html = fr.read()
    return HTMLResponse(content=html, status_code=200)

@app.post('/generate')
async def generate_codes(req : GenerateRequest):
    apiUtils.log(str(req))
    user = req.user
    start = req.start
    count = req.count
    length = req.length
    pre_string = req.pre_string
    pro_string = req.pro_string
    overwrite = req.overwrite
    overwrite = overwrite == 1
    
    hashed = apiUtils.generate_hashed(user)
    progress_data = apiUtils.get_progress_atomic(user)
    lockfilepath = os.path.join(apiUtils.ROOT, apiUtils.WORKING_FOLDER, hashed, 'LOCK.lock')
    cancelled = os.path.exists(lockfilepath) # has been cancelled earlier on
    incomplete = False
    if progress_data is not None:
        prg, cnt = progress_data
        incomplete = (prg/cnt) != 1
    print('>> cancelled=', cancelled, ', incomplete :', incomplete)
    if not cancelled and incomplete:
        msg = 'Generation already in progress'
        apiUtils.log(msg, key=hashed)
        return msg

    generate_thread = lambda : apiUtils.generate_qrcodes(start, count, hashed, length, pre_string, pro_string, overwrite, root=apiUtils.ROOT)
    thread = threading.Thread(target=generate_thread, args=())
    try:
        thread.start()
        time.sleep(2) # wait for node to be activated and states written

        # start a check process
        t = threading.Thread(target=apiUtils.check_complete_folders, args=(user, ))
        t.start()
        # -> exceptions collected by main catch

        if thread.is_alive():
            state = apiUtils.get_state_atomic(user)
            if state is not None:
                key, msg = state
                apiUtils.log(msg, key=hashed)
                print(msg)
                return msg
            else:
                apiUtils.log('Undefined state; state is None.')
                return 'Undefined state.'
        else:
            state = apiUtils.get_state_atomic(user)
            if state is not None:
                key, msg = state
                apiUtils.log(msg, key=hashed)
                print(msg)
                return msg
            apiUtils.log('Failed to create genearator thread', key=hashed)
            print('Failed to create generator thread')
            return 'An Error occured at the server.'
    except Exception as e: # any failure in node & apiUtils.generate goes here
        apiUtils.log(str(e), key='error')
        print('Thread terminated unexpectedly')
        return 'Server error! Oops, a critical error occured on our end.'

@app.get('/progress/{user}')
async def get_progress(user : str):
    # returns the progress of a specific user
    return apiUtils.get_progress_atomic(user)

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
    zip_cache = []
    hashed = apiUtils.generate_hashed(user)
    progress_data = apiUtils.get_progress_atomic(user)
    if progress_data is None:
        return status.HTTP_404_NOT_FOUND
    progress, total = progress_data
    workingpath = os.path.join(apiUtils.ROOT, apiUtils.WORKING_FOLDER, hashed)
    if progress > apiUtils.FOLDER_BATCH or (progress/total) == 1: # there are some folders ready
        folders = os.listdir(workingpath) # find the folders
        zip_cache = [(folder, hashed+'/'+folder) for folder in folders if len(re.findall('^\d+_\d+\.zip$', folder)) > 0]
    return zip_cache

@app.get('/download/{hashed}/{folder}')
async def download(hashed : str, folder:str):
    workingpath = os.path.join(apiUtils.ROOT, apiUtils.WORKING_FOLDER, hashed)
    zip_file = os.path.join(workingpath, folder)
    if os.path.exists(zip_file):
        return FileResponse(path=zip_file, media_type='application/octet-stream', filename=folder)
    return status.HTTP_404_NOT_FOUND

@app.get('/cancel/{user}')
async def cancel_generation(user : str):
    '''cancels tasks being handled by this user'''
    hashed = apiUtils.generate_hashed(user)
    lockfilepath = os.path.join(apiUtils.ROOT, apiUtils.WORKING_FOLDER, hashed, 'LOCK.lock')
    if os.path.exists(lockfilepath):
        msg = 'Task already cancelled by user.'
        apiUtils.log(msg, key=hashed)
        return msg
    try:
        progress_data = apiUtils.get_progress_atomic(user)
        if progress_data is not None:
            progress, count = progress_data
            if progress/count == 1:
                msg = 'No active task to cancel.'
                apiUtils.log(msg, key=hashed)
                return msg
        with open(lockfilepath, 'w') as fw:
            pass
        apiUtils.log("Task cancelled by user!", key=hashed)
        return "Task cancelled by user!"
    except Exception as e:
        apiUtils.log(str(e))
        return "Server error, Failed to cancel!"

def clean_after_self(days_time=30):
    '''
    delete files after time
    '''
    # if folder.time.diff(current) >= days_time
    pass

if __name__ == "__main__":
    uvicorn.run(app)
