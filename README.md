# QRCode-generator-frontend
Frontend for QR Code generator

### Dependencies:
- qrcode[pil]
- fastapi
- uvicorn

### BACKEND SETUP
- Ensure that the qrcode project files are inside htdocs inside Xampp folder.
- Manually create a database called `qrcode`.
You are set!
Additionally, if you create a database with a different name, you will have to change the value of `DB_DATABASE_NAME` inside `config.php`.

### FRONTEND USAGE
- Start the frontend API by running "main.py".
 This will start a server that is accessible on a port, most likely port 8000
- Open your browser and head to localhost:portnumber e.g localhost:8000
- Ensure that the PHP backend is active and running.
- Open `APP/html/js/utils.js` and find a function named `get_api_uri`.
  Change its return value to the base url used to access the backend.
  The default return value is `http://localhost/qrcode/index.php`.

All set!

### WARNING
- Tested only on Windows.

### NOTES AND FEATURES
- The Dashboard shows a users personal project stats.
- Users can create Configurations and Projects.
- Privileged users can view users and their projects
- There is a permission system that governs the front-end render
- All QRCodes are generated via python script
- Python scripts entry point is `script.py`.
- QRCode generation is started on as a separate process inside the script.
- PHP waits for the thread to complete (on windows) but this doesn't affect the entire flow of the program.
- Closing the PHP server or timing out does not stop the generation process.
- The only way to communicate with this process is through files. This is done automatically.
- The qeneration code listens for communicatiion files after every QRCODE is generated. That means that cancelling the program reacts in real time.
- There is always a delay of about 2 seconds when performing actions (pause,resume etc) on projects. This is intentional. During this delay, the program is actually checking if the current project state is active e.g if you request to resume a project, the program has to first assert that the project is resumable.
- The python script handles all qrcode file handling and zipping. PHP has no access to such.
- The python script has no access to the Database whatsoever, only PHP does. 
  For this reason, the states(ACTIVE, PAUSED, COMPLETED) shown when you request a list of active projects may not be accurate. However when you request to view a project, the state shown will be accurate i.e when on the `view_project` page.
- The project state is updated by requesting `state` on the python script `script.py`. This will return the accurate current state of the project i.e whether it is paused, completed or running.

