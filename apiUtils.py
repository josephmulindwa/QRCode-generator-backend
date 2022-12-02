import os
import re
import subprocess
import shutil
import threading
import time

SUCCESS = 0
FAILED_CREATE_PATH = 1
ERROR = 2

ROOT = '.'
WORKING_FOLDER = "OUTPUT" # folder where to put user's files
MAX_LOG_LINES = 100 # the maximum number of lines that can be logged
slash_style = '\\'
indexfile = 'qrUtils.js'
PROGRESS_FILE = 'progress.txt'
CSV_FILE = 'qrCode.csv'
FOLDER_BATCH = 20128 # 21216
APP_FOLDER = 'APP'
LOG_FILE = 'logs.txt'
STATE_FILE = 'STATE.state'

def log(message, key='main', clear=False):
    '''adds data to log'''
    appfolder = os.path.join(ROOT, APP_FOLDER)
    if not os.path.exists(appfolder):
        os.makedirs(appfolder)
    logfile = os.path.join(appfolder, LOG_FILE)
    lines = []
    if not clear and os.path.exists(logfile):
        with open(os.path.join(appfolder, LOG_FILE), 'r') as fr:
            lines = fr.readlines()
    lines.append('{0} : {1}'.format(key, str(message)))
    if len(lines) > MAX_LOG_LINES:
        lines = lines[MAX_LOG_LINES*-1:]
    with open(os.path.join(appfolder, LOG_FILE), 'w') as fw:
        for line in lines:
            if line.endswith('\n'):
                line = line[:-1]
            fw.write('{}\n'.format(line))
    
def generate_hashed(s):
    s = '_'.join(re.findall('\w+', s))
    return s

def file_to_list(filepath):
    '''reads file and returns raw string list'''
    if not os.path.exists(filepath):
        return None
    content = None
    with open(filepath) as fr:
        content = fr.read().strip()
    if content is not None:
        if content.startswith('[') and content.endswith(']'):
            return content[1:-1].split(',')
    return None

def get_progress_atomic(user):
    '''return progress of user, {0, 0} is returned if an error occurs'''
    hashed = generate_hashed(user)
    frompath = os.path.join(ROOT, WORKING_FOLDER, hashed, PROGRESS_FILE)
    arr = file_to_list(frompath)
    if arr is not None:
        arr = list(map(int, arr))
        return arr
    return None

def get_state_atomic(user):
    hashed = generate_hashed(user)
    frompath = os.path.join(ROOT, WORKING_FOLDER, hashed, STATE_FILE)
    if not os.path.exists(frompath):
        return [-1, 'Still working with no errors yet.']
    results = file_to_list(frompath)
    if results is not None:
        return [int(results[0]), results[1]]
    return None

def zip_folder_atomic(sourcefolder, filename, incomplete_prefix='__'):
    '''zips a file setting prefix before while handling and removing it after'''
    tofolder = os.path.join(sourcefolder, incomplete_prefix + filename)
    fromfolder = os.path.join(sourcefolder, filename)
    shutil.make_archive(tofolder, 'zip', fromfolder)
    os.rename(tofolder+'.zip', fromfolder+'.zip')
    # delete folder
    shutil.rmtree(fromfolder)

def zip_folder_on_complete(user, incomplete_prefix='__'):
    '''
    checks for existence of folder and its zip file
    if both exist; zipping is either in progress or done, else unzipped
    -> starts thread(s) to zip folder 
    '''
    hashed = generate_hashed(user)
    searchpath = os.path.join(ROOT, WORKING_FOLDER, hashed)
    progressdata = get_progress_atomic(user)
    if progressdata is None:
        return
    cnt, total = progressdata
    files = os.listdir(searchpath)
    for filename in files:
        if len(re.findall('^\d+_\d+$', filename)) > 0:
            a, b = list(map(int, filename.split('_')))
            if (a <= cnt and b <= cnt) or (cnt/total) == 1:
                pass
            else:
                continue
            zipfile, prezipfile = filename + '.zip', incomplete_prefix + filename + '.zip'
            if zipfile in files or prezipfile in files:
                pass
            else:
                try:
                    t = threading.Thread(target=zip_folder_atomic, args=(searchpath, filename, ))
                    t.start()
                except Exception as e:
                    print('Error :', e)
                    log(str(e), 'zip')

def check_complete_folders(user):
    '''checks for complete folders and activate zip unit'''
    prev_total, prev_cnt, fail_cnt = None, 0, 0
    MAX_FAILS = 10e2
    while True:
        # handles section breaks loop if session fails or when all is done
        progressdata = get_progress_atomic(user)
        if progressdata is None:
            continue
        cnt, total = progressdata
        if cnt == prev_cnt and cnt != total:
            fail_cnt += 1
        if fail_cnt >= MAX_FAILS:
            break
        if prev_total is not None and total != prev_total: # new session confirmed
            break
        prev_cnt, prev_total = cnt, total
        # performing check
        zip_folder_on_complete(user)
        if cnt/total == 1: # <-- completed all; should run zip at least once
            break
        time.sleep(5)

def generate_qrcodes(start, count, userfolder, length, pre_string, pro_string, overwrite, root=ROOT):
    '''
    generates qrcodes by calling the indexfile repeatedly in batch-intervals until all qrcodes are generated
    @params
    start : int
        the value to start at
    count : int
        the number of qrcodes to generate
    userfolder : str
        the subfolder into which to place results
    length : int
        the length of serial padding
    pre_string : int
        the string that comes before a serial if it exists
    pro_string : int
        the string that comes after a serial if it exists
    overwrite : bool
        whether to warn if folder exists or to overwrite it if it exists
    root : string
        the path where this code exists
    '''
    global SUCCESS, FAILED_CREATE_PATH, ERROR, PROGRESS_FILE, CSV_FILE
    # ensure existence of working folder
    workingpath = os.path.join(root, WORKING_FOLDER)
    hashed = generate_hashed(userfolder)
    outpathjs = os.path.join(workingpath, hashed).replace('\\', '/')
    if len(pre_string) == 0:
        pre_string = ' '
    if len(pro_string) == 0:
        pro_string = ' '
    overwrite = int(overwrite)
    process = subprocess.Popen(['node', indexfile, str(start), str(count), str(length), pre_string, pro_string, 
                                outpathjs, str(overwrite), CSV_FILE, PROGRESS_FILE, str(FOLDER_BATCH)], 
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if len(stderr) == 0:
        log(stdout, key='stdout')
        return SUCCESS
    else:
        log(stderr, key='stderr')
        raise ValueError()

#generate_qrcodes(start=1, count=5, userfolder='app', length=5, pre_string='vid', pro_string='', overwrite=True, root=ROOT)