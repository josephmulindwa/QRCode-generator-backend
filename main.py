import uvicorn
from fastapi import FastAPI, status
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Generator
import os
import apiutils
import utils
import threading
import re
import time
import logging
import authenticate
from user import User

app = FastAPI(title="main app")
api_app = FastAPI(title="api app")

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

class RequestForm(BaseModel):
    '''class for generate request'''
    name:str
    start_value:int
    count:int
    description:str
    qr_serial_length:int
    csv_serial_length:int
    pre_string:str
    pro_string:str
    folder_batch:int
    box_size:int
    qr_padding:int
    foreground_color:str
    background_color:str

class LoginForm(BaseModel):
    identifier:str
    password:str

html_app = FastAPI(name="html api")

html_folder = os.path.join(apiutils.APP_FOLDER, "html")
app.mount("/api", api_app)
app.mount("/", StaticFiles(directory=html_folder, html=True), name="html")

@api_app.post('/generate')
async def generate_codes(req : RequestForm):
    apiutils.log(str(req))

    name=utils.clean_string(req.name)
    start_value=req.start_value
    count=req.count
    description=req.description
    qr_serial_length=req.qr_serial_length
    csv_serial_length=req.csv_serial_length
    pre_string=req.pre_string
    pro_string=req.pro_string
    folder_batch=req.folder_batch
    box_size=req.box_size
    qr_padding=req.qr_padding
    foreground_color=req.foreground_color
    background_color=req.background_color

    # decompose from token
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"Request failed - no user!"}
        return response
    
    exist_request = user.get_request(name)
    if exist_request is not None:
        response = {"status":"failed", "message":"A request with this name already exists!"}
        return response
    
    user.set_request()

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

@api_app.post('/login')
async def login(req : LoginForm):
    identifier = req.identifier
    password = req.password
    user = User.fromUsername(identifier)
    response = {"status":"failed", "message":"username or password is invalid"}
    if user is not None:
        print(user.password, password)
        userdata = user.as_dict()
        userdata["token"] = authenticate.tokenize({"username":user.username})
        if user.password==password:
            response = {"status":"success", "data":userdata}
            if not user.approved:
                response = {"status":"failed", "message":"user not yet approved"}
        else:
            response = {"status":"failed", "message":"invalid password"}
    print(response)
    return response

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

@api_app.get("/test")
async def test():
    return "Test is active"

def clean_after_self(days_time=30):
    '''
    delete files after time
    '''
    # if folder.time.diff(current) >= days_time
    # handled by database time logger
    pass

if __name__ == "__main__":
    #uvicorn_access = logging.getLogger("uvicorn.access")
    #uvicorn_access.disabled=True
    uvicorn.run(app, host='0.0.0.0', port=8000)