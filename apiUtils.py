import os
import subprocess
import shutil
import zipfile
import threading
import time
import qrcode
import utils
from qrcode.image.pure import PyPNGImage

ROOT = os.getcwd()
OUTPUT_FOLDER = "OUTPUT" # folder where to put user's files
APP_FOLDER = 'APP'
LOG_FILE = 'logs.txt'
MAX_LOG_LINES = 100 # the maximum number of lines that can be logged
CSV_FILE = 'qrcodes.csv'
FOLDER_BATCH = 20128 # 21216
MAX_ZIP_THREADS=8

# db
ACTIVE_OBJECTS = dict()

def add_qrgen_object(key, obj):
    global ACTIVE_OBJECTS
    ACTIVE_OBJECTS[key] = obj

def remove_qrgen_request(key):
    global ACTIVE_OBJECTS
    if key in ACTIVE_OBJECTS:
        del ACTIVE_OBJECTS[key]

def get_qrgen_object(key):
    global ACTIVE_OBJECTS
    if key in ACTIVE_OBJECTS:
        return ACTIVE_OBJECTS[key]
    return None

def setup():
    appfolder = os.path.join(ROOT, APP_FOLDER)
    if not os.path.exists(appfolder):
        os.makedirs(appfolder)

def log(message, key='message'):
    '''adds data to log'''
    logfile = os.path.join(APP_FOLDER, LOG_FILE)
    log_manager = utils.CollectionsManager(max_collections=MAX_LOG_LINES, init_value=None)
    log_manager.add_collection("{} >> {}:{}".format(time.ctime(), key, message))
    log_manager.write(filename=logfile)

def _zip_and_delete_folder(base_folder, target_folder_name):
    '''
    zips a file setting prefix before while handling and removing it after
    @params
    base_folder
        the folder where the folder to be zipped exists. Also, the folder where the result will be placed
    target_folder_name
        the folder inside base_folder that contains the files to be zipped
    '''
    incomplete_prefix="__"
    target_folder_path = os.path.join(base_folder, target_folder_name)
    file_list = [os.path.join(target_folder_path, fl) for fl in os.listdir(target_folder_path)]
    pending_zipfilename = os.path.join(base_folder, "{}{}.zip".format(incomplete_prefix, target_folder_name))
    final_zipfilename = os.path.join(base_folder, "{}.zip".format(target_folder_name))
    with zipfile.ZipFile(pending_zipfilename, 'w') as zip:
        for file in file_list:
            filename = os.path.basename(file)
            zip.write(file, compress_type=zipfile.ZIP_DEFLATED, arcname=filename)
    shutil.rmtree(target_folder_path)
    os.rename(pending_zipfilename, final_zipfilename)

def generate_qrcode(data, version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=1, fgcolor=(0, 0, 0), bgcolor=(255, 255, 255)):
    """
    returns image of qrcode with data
    @params
    version : int; range(1, 40); default=1
        a determinant of size of qrcode generated (1 is the smallest size)
    error_correction : int ; constant
        error correction criteria
    box_size : int; default=4
        the size of the qrcode black boxes
    border : int
        this controls how many boxes thick the border should be
    """
    qr = qrcode.QRCode(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fgcolor, back_color=bgcolor)
    return img

class QRCodeGenerator:
    def __init__(self, name=None, version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=1, folder_batch=FOLDER_BATCH, fgcolor=(0,0,0), bgcolor=(255,255,255)):
        """
        @params
        
        """
        self.version = version
        self.error_correction = error_correction
        self.box_size=box_size
        self.border = border
        self.error_message = None
        self.progress=0
        self.total=None
        self.cancelled=False
        self._zip_thread_data = dict()
        self._gen_zip_data = dict()
        self.name = name
        self.folder_batch = folder_batch
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.targetfolder=os.path.join(ROOT, OUTPUT_FOLDER, "__temp__")
        if self.name is not None:
            self.targetfolder=os.path.join(ROOT, OUTPUT_FOLDER, name)

        if os.path.exists(self.targetfolder):
            shutil.rmtree(self.targetfolder)
        os.makedirs(self.targetfolder)


    def generate_qrcode(self, data):
        return generate_qrcode(data, self.version, self.error_correction, self.box_size, self.border, fgcolor=self.fgcolor, bgcolor=self.bgcolor)
    
    def generate_qrcodes(self, start_number, end_number, qr_serial_length, csv_serial_length, pre_string, pro_string, outfolder, with_csv=True, update_progress=False):
        """
        generates qrcodes and places them into specified folder
        start_number :
            the number to start at
        end_number :
            the number to end at; exclusive
        """
        csv_data = ""
        try:
            if not os.path.exists(outfolder):
                os.makedirs(outfolder)
            else:
                # remove amd remake folder
                pass
            csv_path = os.path.join(outfolder, CSV_FILE)
            with open(csv_path, 'w') as fw:
                fw.write("Serials,Filename\n")
            for i in range(start_number, end_number):
                if self.cancelled:
                    self.error_message="Cancelled by User"
                    log(self.error_message)
                    # store resume value here
                    # self.start = self.progress
                    return False
                qr_serial_fill = str(i).zfill(qr_serial_length)
                csv_serial_fill = str(i).zfill(csv_serial_length)
                imname = "qrcode{}.png".format(i)
                qrdata = "{}{}{}".format(pre_string, str(qr_serial_fill), pro_string)
                img = self.generate_qrcode(qrdata)
                outpath = os.path.join(outfolder, imname) # filename changes here
                img.save(outpath)
                csv_data += "{},{}\n".format(csv_serial_fill,imname)
                if i%1000==0:
                    with open(csv_path, 'a') as fw:
                        fw.write(csv_data)
                    csv_data=""
                if update_progress:
                    self.progress+=1
            if len(csv_data) > 0:
                with open(csv_path, 'a') as fw:
                    fw.write(csv_data)
            return True
        except Exception as e:
            self.error_message = "{} : error@generate qrcodes : {}".format(self.name,e)
            log(message=self.error_message, key='error')
            return False
    
    def generate(self, start_number, limit, qr_serial_length, csv_serial_length, pre_string, pro_string, with_csv=True, zip=True):
        """
        macro qrcode generator; 
        generates qrcodes and places them in numbered subfolders
        Note:
        this function's generations are threadable
        """
        im = start_number 
        self.total = limit
        end_number = start_number+limit
        rem = limit
        while im < end_number:
            foldername="{}_{}".format(im, im+self.folder_batch-1)
            outfolder = os.path.join(self.targetfolder, foldername) 
            next_limit = min(rem, self.folder_batch)
            curr_end = im+next_limit
            state = self.generate_qrcodes(
                start_number=im, end_number=curr_end, qr_serial_length=qr_serial_length, csv_serial_length=csv_serial_length,
                pre_string=pre_string, pro_string=pro_string, outfolder=outfolder, with_csv=with_csv, update_progress=True)
            # self.progress+=next_limit
            rem = limit-self.progress
            if not state:
                break
            # start zip thread here
            if zip:
                # if the zipping threads are many; wait
                while self.get_number_active_zip_threads() > MAX_ZIP_THREADS:
                    time.sleep(60)
                try:
                    thread = threading.Thread(target=self.zip_folder, args=(foldername,))
                    thread.start()
                except Exception as e:
                    self.error_message = "{} : Error @zip : {}".format(self.name, e)
                    log(self.error_message)
            im+=self.folder_batch

    def get_number_active_zip_threads(self):
        counts = 0
        for key in self._zip_thread_data.keys():
            counts += int(self._zip_thread_data[key])
        return counts
    
    def zip_folder(self, foldername):
        """
        zips a folder and notifies when it is complete
        """
        self._zip_thread_data[foldername] = False
        _zip_and_delete_folder(base_folder=self.targetfolder, target_folder_name=foldername)
        self._zip_thread_data[foldername] = True

    def cancel(self):
        self.cancelled=True
        
    def is_complete(self):
        return self.total==self.progress  # and zipping is done

def get_generator_from_config(name, config):
    # generates a generator object that conforms to the config  
    _version = config['version']
    _error_correction = eval("qrcode.constants.{}".format(config['error_correction']))
    _box_size = config['box_size']
    _border = config['border']
    _folder_batch=config['folder_batch']
    _fg_color = config['fgcolor']
    _bg_color = config['bgcolor']

    generator = QRCodeGenerator(
        name=name, 
        version=_version, 
        error_correction=_error_correction, 
        box_size=_box_size, 
        border=_border,
        folder_batch=_folder_batch,
        fgcolor=utils.hex_to_rgb(_fg_color),
        bgcolor=utils.hex_to_rgb(_bg_color)
        )
    return generator

## user database