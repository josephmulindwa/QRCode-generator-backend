/*
  functions to create QRCodes
*/

const QRCode = require('qrcode')
const fs = require('fs');
const path = require('path');

var STATE_SUCCESS = 0;
var STATE_ERROR_GENERIC = 1;
var STATE_ERROR_PATH = 2;
var STATE_ERROR_LOOP = 3;
var STATE_ERROR_MINV = 4;
var STATE_PATH_EXISTS = 5;
var cache_total = 0;

function digits_count(n) {
  var count = 0;
  if (n >= 1) ++count;
  while (n / 10 >= 1) {
    n /= 10;
    ++count;
  }
  return count;
}

function zfill(num, totalLength) {
  return String(num).padStart(totalLength, '0');
}

const opts = {
  errorCorrectionLevel: 'M1',
  type: 'terminal',
  quality: 0.95,
  margin: 1,
  color: {
    dark: '#000000',
    light: '#FFF',
  },
}

function verify_existence(start_val, end_val, lookfolder){
  // returns the descending number where generation may have last failed at
  var filepath;
  var count = 0;
  var fail_id = -1;
  for (var i=end_val; i>=start_val; i--){
    qrfile = 'qrCode'.concat(i.toString(),'.png');
    filepath = path.join(lookfolder, qrfile)
    if (fs.existsSync(filepath)){
      count++;
    }else{
      if (fail_id == -1){ fail_id = i; }
    }
  }
  return [fail_id, count];
}

async function generate_qrcodes(start_val, end_val, serial_length, serial_string_pre, serial_string_end, outpath, 
  batch, folder_batch, csv_write_batch, csv_filename, progress_file, report_progress_after, overwrite){
  /*
    @params
    total_required : int
      the number of QRCodes you want to generate
    serial_length : int
      the length of the serial code; the number that appears beside the serial_string
      - setting this value to 0 ensures that no (zero-filled) number is added
      - setting this value to a negative ensures that the number is included but not zero-filled
    serial_string_pre : str
      the string that appears before the serial number
    serial_string_end : str
      the string that appears after the serial number
    outpath : str
      the folder/path where files and folders are going to be output
    batch : int
      the number of QRCodes to generate at a time, to regulate resource usage
    folder_batch : int
      group QRCodes into folders of length
    csv_write_batch : int
      write to csv after this amount of lines have been appended
    csv_filename : str
      the name of the csv file to create per folder
    progress_file : str
      the file where progress statistics are stored
    report_progress_after : int
      write progress statistics after these number of cycles have occurred
    overwrite : bool
      whether to delete and write new data OR throw an error if target directories exist
  */
  // start from here & descend
  var curr = end_val; // copy of start_val

  if (start_val <= 0){
    return STATE_ERROR_MINV;
  }

  outpath = path.join('.', outpath);
  // WRITING MAIN FOLDER
  if(fs.existsSync(outpath)){
    if(overwrite){
      fs.rmSync(outpath, {recursive:true, force:true});
    }else{
      return STATE_PATH_EXISTS;
    }
  }

  if (!fs.existsSync(outpath)){
    fs.mkdirSync(outpath, {recursive:true}, err => {
      if (err){
        console.log('Error creating path', outpath, err);
        //throw(err);
        return STATE_ERROR_PATH;
      }
    });
  }

  var serial, donecount, zfilled;
  var foldername, outfolder_path;
  var lines = '';
  var progress_count = 0;
  var l=-1, u=-1;
  var pl=l, pu=u;
  
  while(curr>=start_val){
    serial = curr;
    donecount = 0;
    while ((batch>donecount) && (serial>=start_val)){
      // DECIDING FOLDER OF PLACEMENT
      var range_key = Math.floor((serial-1)/folder_batch);
      l = (range_key*folder_batch)+1;
      u = (l+folder_batch)-1;

      // onchange -> write previous csv parts and reset
      if ((pu!=u) && (pl!= l) && (lines.length > 0)){
        fs.appendFileSync(path.join(outfolder_path, csv_filename), lines);
        lines = '';
      }
      foldername = l.toString()+'_'+u.toString();
      outfolder_path = path.join(outpath, foldername);
      if (!fs.existsSync(outfolder_path)){
        console.log("Creating path : ", outfolder_path);
        fs.mkdirSync(outfolder_path, {recursive : true}, err => {
          if(err){
            throw(err);
          }
        });
      }
      if (pu != u && pl != l){
        // write a new csv here; when the foldername has been created
        fs.writeFileSync(path.join(outfolder_path, csv_filename), "Serials, FileName");
        pu = u;
        pl = l;
      }

      // GENERATING QRCODES
      zfilled = zfill(serial, serial_length);
      imfilename = 'qrCode'.concat(serial,'.png');
      qrinfo = serial_string_pre;
      if (serial_length > 0){ // positive -> include zfilled
        qrinfo = qrinfo+zfilled;
      }else if(serial_length < 0){ // negative -> adaptive serial
        qrinfo = qrinfo+serial.toString();
      }
      qrinfo = qrinfo+serial_string_end;
      try{
        let response = await QRCode.toFile(path.join(outfolder_path, imfilename), qrinfo, opts);
        cache_total--;
      }catch(err){
        console.error(err);
      }

      // WRITE CSV after N lines
      if ((progress_count%csv_write_batch==0)){
        if (lines.length > 0){
          fs.appendFileSync(path.join(outfolder_path, csv_filename), lines);
        }
        lines = '';
      }

      // WRITE PROGRESS
      if ((progress_count%report_progress_after == 0) || (progress_count == 1)){
        fs.writeFileSync(path.join(outpath, progress_file), '['+progress_count.toString()+','+(1+end_val-start_val).toString()+']'); // stores progress
      }
      
      // pause progress until batch
      lines += "\r\n'"+zfilled+','+imfilename;
      --serial;
      ++donecount;
      ++progress_count;
    }
    curr -= donecount;  
  }

  // write unwritten updates
  if (lines.length > 0){
    console.log('final writing lines to ', outfolder_path);
    fs.appendFileSync(path.join(outfolder_path, csv_filename), lines);
  }
  fs.writeFileSync(path.join(outpath, progress_file), '['+progress_count.toString()+','+(1+end_val-start_val).toString()+']');

  console.log("DONE at", serial);
}

var args = process.argv.slice(2); // start_val, count, serial_length, pre_string, pro_string, sub_folder, overwrite

var start_val = parseInt(args[0]);
var end_val = start_val + parseInt(args[1]);
end_val -= 1;
var serial_length = parseInt(args[2]);
var serial_string_pre = args[3];
var serial_string_end = args[4];

if (serial_string_pre == ' '){
  serial_string_pre = '';
}

if (serial_string_end == ' '){
  serial_string_end = '';
}

var outpath = args[5];
var batch = 250;
var folder_batch = parseInt(args[9]);
var csv_write_batch = 100;
var overwrite = parseInt(args[6]);
var csv_filename = args[7];
var progress_file =  args[8]
var report_progress_after = 10;

async function run(){
  await generate_qrcodes(start_val, end_val, serial_length, serial_string_pre, serial_string_end,
                  outpath, batch, folder_batch, csv_write_batch, csv_filename,
                  progress_file, report_progress_after, overwrite);

  var state = verify_existence(800, 850, './OUTPUT/dedan/801_1000/');
  console.log('state :', state);
}

run();