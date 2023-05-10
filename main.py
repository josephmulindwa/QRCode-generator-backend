import uvicorn
from fastapi import FastAPI, status, Request
from pydantic import BaseModel
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Generator
import os
import apiutils
import utils
import threading
import re
import json
import time
import logging
import authenticate
from user import User
from project import Project
from configuration import Configuration
from user_permission import UserPermission

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

class ProjectForm(BaseModel):
    '''class for generate project'''
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

class PermissionListForm(BaseModel):
    username:str
    listing:list

html_app = FastAPI(name="html api")

html_folder = os.path.join(apiutils.APP_FOLDER, "html")
app.mount("/api", api_app)
app.mount("/", StaticFiles(directory=html_folder, html=True), name="html")

def get_user_project_key(username, projectname):
    return "{}-{}".format(utils.clean_string(username),utils.clean_string(projectname))

def get_data_from_file(file_path: str) -> Generator:
    with open(file=file_path, mode="rb") as file_like:
        yield file_like.read()

def get_user_from_request(req : Request):
    decompose = authenticate.detokenize_from_request(req)
    if decompose is None:
        return None
    _, payload, __ = decompose
    if "username" in payload.keys():
        return User.fromUsername(payload['username'])
    return None

@api_app.post('/generate')
async def generate_codes(form : ProjectForm, req:Request):
    name=utils.clean_string(form.name)
    start_value=form.start_value
    total=form.count
    description=form.description
    qr_serial_length=form.qr_serial_length
    csv_serial_length=form.csv_serial_length
    pre_string=form.pre_string
    pro_string=form.pro_string
    config_name=form.config_name

    # decompose from token
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"Project failed - no user!"}
    else:
        exist_project = user.get_project(name)
        if exist_project is not None:
            response = {"status":"failed", "message":"A project with this name already exists!"}
        else:
            config = user.get_configuration_by_name(config_name)
            if config is None:
                response = {"status":"failed", "message":"Unknown configuration `{}`".format(config_name)}
            else:
                user.add_new_project(name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,
                    config.id,progress=0,created_on=None,state=Project.STATE_ACTIVE)
                key = get_user_project_key(user.username, projectname=name)
                try:
                    qrgen = apiutils.get_generator_from_configuration(key, config, os.path.join(user.username, name))
                    apiutils.add_qrgen_object(key, qrgen)
                    generate_fn = lambda : qrgen.generate(start_number=start_value, limit=total, qr_serial_length=qr_serial_length, 
                        csv_serial_length=csv_serial_length, pre_string=pre_string, pro_string=pro_string)
                    thread = threading.Thread(target=generate_fn, args=())
                    thread.start()
                    apiutils.log('{} : Generation started'.format(key))
                    response = {"status":"success", "data":"Project added successfully!"}
                except Exception as e:
                    msg = "Error @api.generate : {}".format(e)
                    apiutils.log(msg, key='error')
                    print(msg)
                    response = {"status":"failed", "message":"An error occured on our end!"}
    return response

@app.get('/progress/{projectname}')
async def get_progress(projectname : str, req:Request):
    # returns the progress of a specific user
    user = get_user_from_request(req)
    if user is None:
        return "Failed"
    key = get_user_project_key(user.username, projectname)
    qrgen_obj = apiutils.get_qrgen_object(key)
    response = {"status":"failed", "message":"An error occured!"}
    if qrgen_obj is not None:
        response = {"status":"success", "data":{"progress":qrgen_obj.progress, "total":qrgen_obj.total}}
    else:
        # check database
        project = Project.fromName(projectname)
        if project is None:
            response = {"status":"failed", "message":"No such project!"}
        else:
            response = {"status":"success", "data":{"progress":project.progress, "total":project.total}}
    return response
        
@api_app.post('/login')
async def login(form : LoginForm):
    identifier = form.identifier
    password = form.password
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

@api_app.get('/projects/{category}')
async def get_projects_by_category(category:str, req:Request):
    categories = ["ALL", "BILLED", "ACTIVE", "COMPLETE", "INACTIVE"]
    if category not in categories:
        response = {"status":"failed", "message":"Unkown category `{}`".format(category)}
    else:
        user = get_user_from_request(req)
        if user is None:
            response = {"status":"failed", "message":"No such user"}
        else:
            projects = user.get_projects(category=category)
            if projects is not None:
                projects = [req.as_dict() for req in projects]
            else:
                projects = []
            response = {"status":"success", "data":projects}
    return response

@api_app.get('/downloads/{projectname}')
async def get_downloads(projectname : str, req:Request):
    # returns a list to currently available zip files
    user = get_user_from_request(req)
    response = {"status":"failed", "message":"An error occured!"}
    if user is None:
        response = {"status":"failed", "message":"Invalid Token!"}
    else:
        targetfolder = os.path.join(apiutils.ROOT, apiutils.APP_FOLDER, user.username, projectname)
        if os.path.exists(targetfolder):
            files = os.listdir(targetfolder)
            downloadables = [(file, "{}/{}".format(user.username,file)) for file in files if len(re.findall('^\d+_\d+\.zip$', file))>0] 
            response = {"status":"success", "data":downloadables}
        else:
            response = {"status":"failed", "message":"Not Found!"}
    return response

@api_app.get('/download/{user}/{file}')
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
        return status.HTTP_404_NOT_FOUND


@api_app.get('/cancel/{user}')
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
async def add_user(form : UserForm, req:Request):
    name=form.name
    username=form.username
    email=form.email
    password=form.password

    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"Invalid token!"}
    else:
        exist_user = user.get_user(username)
        if exist_user is None:
            user.add_user(name, username, email, password, approved=True)
            response = {"status":"success", "data":"user added"}
        else:
            response = {"status":"failed", "message":"user already exists!"}
    return response

@api_app.get('/users/list')
async def get_downloads(req : Request):
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        users = user.get_users()
        response = {"status":"success", "data":users}
    return response

@api_app.post("/configurations/add")
async def add_configuration(form : ConfigurationForm, req:Request):
    name=utils.clean_string(form.name)
    version=form.version
    folder_batch=form.folder_batch
    error_correction=form.error_correction
    box_size=form.box_size
    border=form.border
    fore_color=form.fore_color
    back_color=form.back_color

    # validate input
    error=False
    if len(name)==0 or version not in Configuration.versions or folder_batch<1 or error_correction not in Configuration.error_correction_levels or box_size<1 or border<1:
        error=True
    elif utils.hex_to_rgb(fore_color) is None or utils.hex_to_rgb(back_color) is None:
        error=True

    if error:
        response = {"status":"failed", "message":"invalid input"}
    else:
        user = get_user_from_request(req)
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
async def get_configurations(req : Request):
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        configs = user.get_configurations()
        data = [config.as_dict() for config in configs]
        response = {"status":"success", "data":data}
    return response

@api_app.get("/users/count")
async def get_user_count(req : Request):
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        count = user.count_users()
        response = {"status":"success", "data":count}
        if count is None:
            response = {"status":"failed", "message":"An error occured!"}
    return response

@api_app.get("/users/search/{text}")
async def search_users_by_text(text : str, req:Request):
    user = get_user_from_request(req)
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

@api_app.get("/projects/search/{text}")
async def search_projects_by_text(text : str, req:Request):
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        projects = user.find_projects_like(text)
        if projects is None:
            response = {"status":"failed", "message":"An error occured on our end"}
        else:
            response = {"status":"success", "data":[req.as_dict()  for req in projects]}
    return response

@api_app.get("/projects/get/{name}")
async def search_projects_by_text(name : str, req:Request):
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        _project= user.get_project(name)
        if _project is None:
            response = {"status":"failed", "message":"An error occured on our end"}
        else:
             response = {"status":"success", "data":_project.as_dict()}
    return response

@api_app.get("/configurations/search/{text}")
async def search_projects_by_text(text : str, req:Request):
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        configs = user.find_configurations_like(text)
        response = {"status":"success", "data":[config.as_dict()  for config in configs]}
        if configs is None:
            response = {"status":"failed", "message":"An error occured on our end"}
    return response

@api_app.get("/projects/count/{category}")
async def get_user_count(category : str, req:Request):
    """
    returns counts for this category for this user
    """
    user = get_user_from_request(req)
    if user is None:
        response = {"status":"failed", "message":"No such user"}
    else:
        count = user.count_projects(category=category)
        response = {"status":"success", "data":count}
        if count is None:
            response = {"status":"failed", "message":"Unkown category `{}`".format(category)}
    return response

@api_app.get("/configurations/error_correction_levels")
async def get_error_corrections():
    response = {"status":"success", "data":Configuration.error_correction_levels}
    return response

@api_app.post("/preview/image")
async def get_preview_image(form : ProjectForm, req:Request):
    start_value=form.start_value
    total=form.count
    qr_serial_length=form.qr_serial_length
    pre_string=form.pre_string
    pro_string=form.pro_string
    config_name=form.config_name

    # decompose from token
    response = status.HTTP_404_NOT_FOUND
    user = get_user_from_request(req)
    if user is not None:
        config = user.get_configuration_by_name(config_name)
        if config is not None:
            first_string, _ = apiutils.get_text_samples(start_value, total, qr_serial_length, pre_string, pro_string)
            img = apiutils.generate_qrcode(first_string, version=config.version, 
                                    error_correction=config.get_error_correction(), 
                                    box_size=config.box_size, 
                                    border=config.border, 
                                    fgcolor=config.get_fore_color(), 
                                    bgcolor=config.get_back_color()
                                    )
            if img is not None:
                import io
                import base64
                b = io.BytesIO()
                img.save(b, "PNG")
                b.seek(0)
                res = base64.b64encode(b.getvalue())

                #headers = {
                #   'Content-Disposition': 'attachment; filename="image.png"'
                #}
                response = {"status":"success", "data":res}
    return response


@api_app.post('/preview/text')
async def get_preview_text(form : ProjectForm):
    '''returns sample string depending on stats'''
    start_value=form.start_value
    total=form.count
    qr_serial_length=form.qr_serial_length
    pre_string=form.pre_string
    pro_string=form.pro_string

    first_string, last_string = apiutils.get_text_samples(start_value, total, qr_serial_length, pre_string, pro_string)
    return {"status":"success", "data":{"start":first_string, "end":last_string}}

@api_app.post("/config/preview")
async def get_config_preview(form : ConfigurationForm):
    name=utils.clean_string(form.name)
    version=form.version
    folder_batch=form.folder_batch
    error_correction=form.error_correction
    box_size=form.box_size
    border=form.border
    fore_color=form.fore_color
    back_color=form.back_color

    # validate input
    error=False
    if len(name)==0 or version not in Configuration.versions or folder_batch<1 or error_correction not in Configuration.error_correction_levels or box_size<1 or border<1:
        error=True
    elif utils.hex_to_rgb(fore_color) is None or utils.hex_to_rgb(back_color) is None:
        error=True

    if error:
        response = {"status":"failed", "message":"invalid input"}
    else:
        img = apiutils.generate_qrcode(data=name, version=version, 
                                    error_correction=Configuration.get_error_correction_from_string(error_correction), 
                                    box_size=box_size, 
                                    border=border, 
                                    fgcolor=Configuration.get_rgb_from_hex(fore_color), 
                                    bgcolor=Configuration.get_rgb_from_hex(back_color)
                                )
        if img is not None:
            import io
            import base64
            b = io.BytesIO()
            img.save(b, "PNG")
            b.seek(0)
            res = base64.b64encode(b.getvalue())
            response = {"status":"success", "data":res}
        else:
            response = {"status":"failed", "message":"An error occured!"}
    return response

@api_app.get("/configurations/get/{name}")
def get_configuration(name : str, req:Request):
    response = {"status":"failed", "message":"Failed to fetch!"}
    user = User.fromUsername(User.superadmin['username'])
    if user is not None:
        config = get_user_from_request(req)
        if config is not None:
            response = {"status":"success", "data":config.as_dict()}
    return response

@api_app.get("/users/get/{username}")
def get_user_profile(username : str, req:Request):
    user = get_user_from_request(req)
    response = {"status":"failed", "message":"Invalid token!"}
    if user is not None:
        requested_user = user.get_user(username)
        if requested_user is None:
            response = {"status":"failed", "message":"User doesn't exist!"}
        else:
            user_data=requested_user.as_dict()
            del user_data["password"]
            del user_data["id"]
            response = {"status":"success", "data":user_data}
    return response

@api_app.get("/user/permissions/{username}")
def get_user_permissions(username : str, req:Request):
    """
    returns the list of permissions for username
    """
    user = get_user_from_request(req)
    response = {"status":"failed", "message":"Invalid token!"}
    if user is not None:
        target_user = User.fromUsername(username)
        if target_user is None:
            response = {"status":"failed", "message":"User does not exist!"}
        else:
            permissions = user.get_permissions_for_user(target_user.id)
            if permissions is not None:
                data = [UserPermission.get_code_from_id(lst.permission_id) for lst in permissions]
                response = {"status":"success", "data":data}
            else:
                response = {"status":"failed", "message":"An error occured. Failed to fetch!"}
    return response

@api_app.get("/permissions") # return self-permissions
def get_user_permissions(req : Request):
    user = get_user_from_request(req)
    response = {"status":"failed", "message":"Invalid token!"}
    if user is not None:
        permissions = user.get_permissions_for_user(user.id)
        if permissions is not None:
            data = [UserPermission.get_code_from_id(lst.permission_id) for lst in permissions]
            response = {"status":"success", "data":data}
        else:
            response = {"status":"failed", "message":"An error occured. Failed to fetch!"}
    return response

@api_app.get("/permissions/list")
def get_all_permissions():
    data = UserPermission.get_permissions_as_dict()
    return {"status":"success", "data":data}

@api_app.post("/permissions/set")
def set_permissions(form : PermissionListForm, req : Request):
    username = form.username
    permissions = form.listing
    permission_ids = UserPermission.get_ids_from_codes(permissions)

    user = get_user_from_request(req)
    response = {"status":"failed", "message":"Invalid token!"}
    if user is not None:
        exist_user = User.fromUsername(username)
        if exist_user is None:
            response = {"status":"failed", "message":"User doesn't exist!"}
        else:
            user.grant_permissions(exist_user.id, permission_ids)
            response = {"status":"success", "data":"Added successfully!"}
    return response

api_app.get("/test")
def test():
    pass

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