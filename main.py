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
from request import Request
from configuration import Configuration

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
    config_name:str

class LoginForm(BaseModel):
    identifier:str
    password:str

class UserForm(BaseModel):
    name:str
    username:str
    email:str
    password:str
    created_by:str

class ConfigurationForm(BaseModel):
    name:str
    version:int
    folder_batch:int
    error_correction:str
    box_size:int
    border:int
    fore_color:str
    back_color:str

html_app = FastAPI(name="html api")

html_folder = os.path.join(apiutils.APP_FOLDER, "html")
app.mount("/api", api_app)
app.mount("/", StaticFiles(directory=html_folder, html=True), name="html")

def get_user_request_key(username, requestname):
    return "{}-{}".format(utils.clean_string(username),utils.clean_string(requestname))

def get_data_from_file(file_path: str) -> Generator:
    with open(file=file_path, mode="rb") as file_like:
        yield file_like.read()

@api_app.post('/generate')
async def generate_codes(req : RequestForm):
    name=utils.clean_string(req.name)
    start_value=req.start_value
    total=req.count
    description=req.description
    qr_serial_length=req.qr_serial_length
    csv_serial_length=req.csv_serial_length
    pre_string=req.pre_string
    pro_string=req.pro_string
    config_name=req.config_name
    config_error_correct="ERROR_CORRECT_M"

    # decompose from token
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"Request failed - no user!"}
    else:
        exist_request = user.get_request(name)
        if exist_request is not None:
            response = {"status":"failed", "message":"A request with this name already exists!"}
        else:
            config = user.get_configuration_by_name(config_name)
            if config is None:
                response = {"status":"failed", "message":"Unkonwn configuration `{}`".format(config_name)}
            else:
                # start goes here...
                user.add_new_request(name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,
                    config.id,progress=0,created_on=None,state=Request.STATE_ACTIVE)
                response = {"status":"success", "data":"Request added successfully!"}
    return response

    key = get_user_request_key(user.username, name)
    try:
        qrgen = apiutils.get_generator_from_config(key, 
            config={
                'version':1,
                'error_correction':"M",
                "box_size":box_size,
                "border":qr_padding,
                "folder_batch":folder_batch,
                "fgcolor":foreground_color,
                "bgcolor":background_color
            })
        apiutils.add_qrgen_request(key, qrgen)
        generate_fn = lambda : qrgen.generate(start_number=start, limit=total, qr_serial_length=qr_serial_length, 
                        csv_serial_length=csv_serial_length, pre_string=pre_string, pro_string=pro_string)
        thread = threading.Thread(target=generate_fn, args=())
        thread.start()
        apiutils.log('{} : Generation started'.format(username))
        return 'Generation started.'
    except Exception as e:
        msg = "Error @api.generate : {}".format(e)
        apiutils.log(msg, key='error')
        print(msg)
        return 'Server error! Oops, a critical error occured on our end.'

@app.get('/progress/{requestname}')
async def get_progress(requestname : str):
    # returns the progress of a specific user
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        return "Failed"
    key = get_user_request_key(user.username, requestname)
    qrgen_obj = apiutils.get_qrgen_object(key)
    if qrgen_obj is not None:
        return qrgen_obj.progress,  qrgen_obj.total
    else:
        # check database
        request = Request.fromName(requestname)
        if request is None:
            return "Nothing at all"
        else:
            return request.progress, request.total # if state==ACTIVE

@app.post('/imagesample')
async def get_image_samples(req : RequestForm):
    '''returns sample image depending on stats'''
    name=utils.clean_string(req.name)
    start_value=req.start_value
    total=req.count
    description=req.description
    qr_serial_length=req.qr_serial_length
    csv_serial_length=req.csv_serial_length
    pre_string=req.pre_string
    pro_string=req.pro_string
    config_name=req.config_name
    config_error_correct="ERROR_CORRECT_M"
    pass


@api_app.post('/textsample')
async def get_text_samples(req : RequestForm):
    '''returns sample string depending on stats'''
    name=utils.clean_string(req.name)
    start_value=req.start_value
    total=req.count
    description=req.description
    qr_serial_length=req.qr_serial_length
    csv_serial_length=req.csv_serial_length
    pre_string=req.pre_string
    pro_string=req.pro_string
    config_name=req.config_name
    config_error_correct="ERROR_CORRECT_M"

    first, last = start_value, start_value+total-1
    first_serial, last_serial =  str(first), str(last)
    if qr_serial_length>0:
        first_serial = first_serial.zfill(qr_serial_length)
        last_serial = last_serial.zfill(qr_serial_length)
    first_string = pre_string+first_serial+pro_string
    last_string = pre_string+last_serial+pro_string
    return {"status":"success", "data":{"start":first_string, "end":last_string}}

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

@api_app.get('/requests/{category}')
async def get_downloads(category:str):
    categories = ["ALL", "BILLED", "ACTIVE", "COMPLETE", "INACTIVE"]
    if category not in categories:
        response = {"status":"failed", "message":"Unkown category `{}`".format(category)}
    else:
        user = User.fromUsername(User.superadmin['username'])
        if user is None:
            response = {"status":"failed", "message":"No such user"}
        else:
            requests = user.get_requests(category=category)
            if requests is not None:
                requests = [req.as_dict() for req in requests]
            else:
                requests = []
            response = {"status":"success", "data":requests}
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

@api_app.post("/user/add")
async def add_user(req : UserForm):
    name=req.name
    username=req.username
    email=req.email
    password=req.password
    created_by=req.created_by

    user = None
    if created_by is None or len(created_by)==0:
        created_by=None
    else:
        user = User.fromUsername(username)
        if user is not None:
            created_by = user.id
    if user is None:
        user = User()
    exist_user = user.get_user(username)
    if exist_user is None:
        user.add_user(name, username, email, password, approved=(created_by is not None))
        response = {"status":"success", "data":"user added"}
    else:
        response = {"status":"failed", "message":"user already exists!"}
    return response

@api_app.get('/users/list')
async def get_downloads():
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        users = user.get_users()
        response = {"status":"success", "data":users}
    return response

@api_app.post("/configurations/add")
async def add_configuration(req : ConfigurationForm):
    name=utils.clean_string(req.name)
    version=req.version
    folder_batch=req.folder_batch
    error_correction=req.error_correction
    box_size=req.box_size
    border=req.border
    fore_color=req.fore_color
    back_color=req.back_color

    # validate input
    error=False
    if len(name)==0 or version not in Configuration.versions or folder_batch<1 or error_correction not in Configuration.error_correction_levels or box_size<1 or border<1:
        error=True
    elif utils.hex_to_rgb(fore_color) is None or utils.hex_to_rgb(back_color) is None:
        error=True

    if error:
        response = {"status":"failed", "message":"invalid input"}
    else:
        user = User.fromUsername(User.superadmin['username'])
        if user is None:
            response = {"status":"failed", "message":"No such user"}
        else:
            exist_config = user.get_configuration_by_name(name)
            if exist_config is not None:
                response = {"status":"failed", "message":"Configuration name already exists!"}
            else:
                user.add_configuration(name,folder_batch,version,error_correction,box_size,border,fore_color,back_color)
                response = {"status":"success", "data":"Conguration added successfully!"}
    return response

@api_app.get("/configurations/list")
async def get_configurations():
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        configs = user.get_configurations()
        data = [config.as_dict() for config in configs]
        response = {"status":"success", "data":data}
    return response

@api_app.get("/users/count")
async def get_user_count():
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        count = user.count_users()
        response = {"status":"success", "data":count}
        if count is None:
            response = {"status":"failed", "message":"Unkown category `{}`".format(category)}
    return response

@api_app.get("/users/search/{text}")
async def search_users_by_text(text : str):
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        users_by_name = user.find_users_like_name(text)
        users_by_username = user.find_users_like_username(text)
        user_ids=[]
        users = []
        if users_by_name is not None:
            for user in users_by_name:
                if user.id not in user_ids:
                    users.append(user)
                    user_ids.append(user.id)
        if users_by_username is not None:
            for user in users_by_username:
                if user.id not in user_ids:
                    users.append(user)
                    user_ids.append(user.id)
        response = {"status":"success", "data":[user.as_dict() for user in users]}
        if users is None:
            response = {"status":"failed", "message":"An error occured on our end"}
    return response

@api_app.get("/requests/search/{text}")
async def search_requests_by_text(text : str):
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        requests = user.find_requests_like(text)
        response = {"status":"success", "data":[req.as_dict()  for req in requests]}
        if requests is None:
            response = {"status":"failed", "message":"An error occured on our end"}
    return response

@api_app.get("/configurations/search/{text}")
async def search_requests_by_text(text : str):
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        configs = user.find_configurations_like(text)
        response = {"status":"success", "data":[config.as_dict()  for config in configs]}
        if configs is None:
            response = {"status":"failed", "message":"An error occured on our end"}
    return response

@api_app.get("/requests/count_all/{category}")
async def get_user_count(category : str):
    user = User.fromUsername(User.superadmin['username'])
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        count = user.count_all_requests(category=category)
        response = {"status":"success", "data":count}
        if count is None:
            response = {"status":"failed", "message":"Unkown category `{}`".format(category)}
    return response

@api_app.get("/configurations/error_correction_levels")
async def get_error_corrections():
    response = {"status":"success", "data":Configuration.error_correction_levels}
    return response

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