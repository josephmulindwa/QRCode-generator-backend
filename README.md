# QRCode-generator-backend
Backend for QR Code generator

Project for QRCODE generation API. The project comes with a quick HTML page for testing purposes.

### Dependencies:
- node.js
- fastapi
- uvicorn

### USAGE
1. Start the API by running "main_fastapi.py".
 This will be accessible on a port, preferably port 8000
2. Open your browser and head to localhost:portnumber e.g localhost:8000
  This will provide you with a link to make requests to the API

### NOTE
- You can check progress by clicking on the progress button
- Downloads (that are finished and ready) will be listed after clicking the downloads page.
  If no downloads appear, then nothing is ready yet
- The "Text Samples" option allows you to see samples of what scanned text will look like.
- Once qrcodes have been generated and placed into a folder, a thread starts to zip this folder and this may take a good amount of time.
 Once zipping completes, the zip file becomes available for download and the original folder is deleted leaving only the zip file.

### HOW IT WORKS
Upon making a request, a folder named after the username you enter on the homepage will be created in the OUTPUT folder.
All the requests for this username will be placed in this folder split into groups/zips/folders of a certain size.
That size can be controlled internally by changing the value of `FOLDER_BATCH` inside "apiUtils.py".
For example if FOLDER_BATCH = 100 and a user requests 300 QRcodes, they will end up with 3 folders/zip files each containing 100 QRcodes.
