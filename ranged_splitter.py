import shutil
import os

def csv_from_list(arr, folder_path, csv_name='qCode.csv', tl=10):
    '''
    creates a csv with serials of length t1 into the folder_path from arr
    arr : list
        a list of tuples (key:int, val:str)
    '''
    arr = sorted(arr)
    with open(os.path.join(folder_path, csv_name), 'w') as fw:
        fw.write('Serials, FileName')
        for key, val in arr:
            addend = "\n"+"'"+str(key).zfill(tl)+","+val
            fw.write(addend)

def create_csv_in_folders(where='.', pre_str='qrCode'):
    '''find folders with images and writes csvs in them'''
    for folder in os.listdir(where):
        try:
            batch = []
            files = os.listdir(os.path.join(where, folder))
            for filename in files:
                #print(filename, 'qrCode' in filename, '.png' in filename)
                if pre_str in filename and '.png' in filename:
                    n = filename.replace(pre_str, '').replace('.png', '')
                    batch.append((int(n), filename))
            csv_from_list(batch, os.path.join(where, folder))
        except:
            pass

def split_into_folders(from_folder, to_folder, start, end, split_size=1000, include_csv=False, csvname='qCode.csv', tl=10):
    '''
    splits the images in from_folder into groups of size split_size
    @params
    from_folder : str
        the folder path in which images to be split exists
    to_folder : str
        the folder path in which images are to be written; 
        Folders will be created inside this folder with ranges appended to them
    start : int
        the value to start the splitting from, inclusive
    end : int
        the value to end the splitting at, inclusive
    split_size : int
        the number of files in each split folder
    '''
    k = start
    le, ue = k, k+split_size-1
    collects = []
    athead = True
    while k < end+1:
        foldername = '_'.join([str(le), str(ue)])
        filename = 'qrCode' + str(k) + '.png'
        to_path = os.path.join(to_folder, foldername)
        if not os.path.exists(to_path):
            os.makedirs(to_path)
        collects.append((k, filename))

        file_r = os.path.join(from_folder, filename)
        file_w = os.path.join(to_path, filename)
        shutil.copyfile(file_r, file_w)
        os.remove(file_r)
        if k>=le and k<ue:
            pass
        else:
            # write_csv here
            if include_csv:
                csv_from_list(collects, to_path, csv_name=csvname, tl=tl)
            collects = []
            le = ue + int(not athead)
            ue = le+split_size-1
        athead = False
        k+=1
    if include_csv and len(collects) > 0:
        csv_from_list(collects, to_path, csv_name=csvname, tl=tl)