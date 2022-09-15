import re
import os
import subprocess

SUCCESS = 0
FAILED_CREATE_PATH = 1
LOOP_FAILED = 2


slash_style = '\\'
indexfile = 'indext.js'

def verify(start, end, outfolder):
    # this verifies that all images came out correct
    fnames = os.listdir(outfolder)
    fails = []
    for i in range(start, end):
        fname = 'qrCode' + str(i) + '.png'
        try:
            with open(os.path.join(outfolder, fname), 'rb') as f:
                v = 0
                while v < 10:
                    f.read(1)
                    v+=1
        except:
            fails.append(i)
    if len(fails):
        return False, min(fails), max(fails)
    return True, end, start

def generate_qrcodes(from_, to_, batch=5000, totalLength=10, outfolder='output', root='.'):
    '''
    generates qrcodes by calling the indexfile repeatedly in batch-intervals until all qrcodes are generated
    @params
    from_ : int
        the (lowest) number to start from, inclusive
    to_ : int
         the (highest) number to end at, inclusive
    batch : int
        the number of qrcodes to be generated at a time
    totalLength : int
        the length of serial numbers
    outfolder : string
        the folder (from the root path) in which to place all qrcodes generated
    root : string
        the path where this code exists
    '''
    global SUCCESS, FAILED_CREATE_PATH, LOOP_FAILED
    outpath = os.path.join(root, outfolder)
    folders = [os.path.join(root,folder) for folder in os.listdir(root)]
    try:
        os.makedirs(os.path.join(root,outfolder))
    except Exception as e:
        msg = str(e)
        if 'exist' not in msg.lower():
            print(e)
            return FAILED_CREATE_PATH
    content = ''
    with open(indexfile) as f:
        content = f.read()
    content =  re.sub("QRCode\\.toFile\(\'[\w]*[//]*qrCode", "QRCode.toFile('" + outfolder + "/qrCode", content)

    max_fail_count = 3
    active_fail_count = 0
    state_l = 0
    k = to_
    while k > from_ and k > 0:
        content = re.sub("var lp = \d+", 'var lp = ' + str(k), content)
        content = re.sub("var total = \d+", 'var total = ' + str(batch), content)
        content = re.sub("var totalLength = \d+", 'var totalLength = ' + str(totalLength), content)
        
        with open(indexfile, 'w') as fw:
            fw.write(content)
        process = subprocess.Popen(['node', indexfile], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        state, vl, vm =  verify(k-batch, k, outfolder=outfolder)
        k = vm+1
        if k == state_l or abs(k - state_l) == 1:
            active_fail_count += 1
        else:
            active_fail_count = 0
        if active_fail_count >= max_fail_count:
            print('An error occurred : no progress from {}.'.format(k))
            return LOOP_FAILED
        state_l = k
        print('@batch >>', k, state, vl, vm+1)
    return SUCCESS
