import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

APP_FOLDER = "APP"

app = FastAPI(title="main app")
api_app = FastAPI(title="api app")

origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
    )

html_app = FastAPI(name="html api")

html_folder = os.path.join(APP_FOLDER, "html")
app.mount("/api", api_app)
app.mount("/", StaticFiles(directory=html_folder, html=True), name="html")

@api_app.get('/stop')
async def stop_server(req : Request):
    # not set
    pass

if __name__ == "__main__":
    #uvicorn_access = logging.getLogger("uvicorn.access")
    #uvicorn_access.disabled=True
    uvicorn.run(app, host='0.0.0.0', port=8000)