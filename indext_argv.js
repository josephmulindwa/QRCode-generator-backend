/*
  What the code does;
  - create a number of qrcodes in folders of batch_size
*/

const QRCode = require('qrcode')
const fs = require('fs')

var args = process.argv.slice(2); // total_required, serial_length, serial_string, path

// start from here & descend
var total_required = parseInt(args[0]);
var total_requiredc = total_required; // copy of total_required
var serial_length = parseInt(args[1]);
var serial_string = args[2];
var outpath = args[3];
var batch = 5000; // how many to generate at a time to regulate resources
var folder_batch = 1000; // how many qrcodes to put in each file
var csv_write_batch = 100; // how many csv lines to write at a time
var csv_filename = "qrCode.csv";
var progress_file = 'progress.txt';
var report_progress_after = 10;

var slashstyle = '/';
if (!outpath.startsWith(slashstyle) && !outpath.startsWith('.')){
  outpath = slashstyle+outpath;
}

if (!outpath.startsWith('.')){
  outpath = '.'+outpath;
}
if (!outpath.endsWith(slashstyle)){
  outpath = outpath+slashstyle;
}

console.log('outpath :', outpath);

if (!fs.existsSync(outpath)){
  console.log('Creating path...')
  fs.mkdirSync(outpath, err => {
    if (err){
      console.log('Error :', err);
      throw(err);
    }
  });
}

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

/*QRCode.toString([
    { data: 'shraddha.paghdar@gmail.com', mode: 'byte' },
    { data: '+78787878', mode: 'byte' }
]).then(qrImage => {
  //console.log("terminal",qrImage)
}).catch(err => {
    console.error(err)
})

QRCode.toDataURL('Hi testing QR code', opts).then(qrImage => {
  //console.log("URL",qrImage)
}).catch(err => {
    console.error(err)
}) */

var serial, donecount, zfilled;
var with_serialnumber = serial_length > 0; // automatically adds or ignores serial based on value
var foldername, outfolder_path;
var lines = '';
var progress_count = 0;
var l=-1, u=-1;
var pl=l, pu=u;

while(total_required > 0){
  serial = total_required;
  donecount = 0;
  while ((batch>donecount) && (serial>0)){
    // DECIDING FOLDER OF PLACEMENT
    var range_itr = Math.floor((total_required-progress_count-1)/folder_batch);
    l = range_itr*folder_batch;
    u = (range_itr+1)*folder_batch;
    if(l == 0){ l=1; }

    // onchange -> write previous csv parts and reset
    if ((pu!=u) && (pl!= l) && (lines.length > 0)){
      fs.appendFileSync(outfolder_path+csv_filename, lines);
      lines = '';
    }
    foldername = l.toString()+'_'+u.toString();
    outfolder_path = outpath + slashstyle + foldername + slashstyle;
    if (!fs.existsSync(outfolder_path)){
      fs.mkdirSync(outfolder_path, err => {
        if(err){
          console.log('Failed to create path : "', outfolder_path, '"');
          throw(err);
        }
      });
    }
    if (pu != u && pl != l){
      // write a new csv here; when the foldername has been created
      fs.writeFileSync(outfolder_path+csv_filename, "Serials, FileName");
      pu = u;
      pl = l;
    }

    // GENERATING QRCODES
    zfilled = zfill(serial, serial_length);
    imfilename = 'qrCode'.concat(serial,'.png');
    qrinfo = serial_string;
    if (with_serialnumber){
      qrinfo = qrinfo.concat("-", zfilled);
    }
    
    QRCode.toFile(outfolder_path+imfilename, qrinfo, opts).then(qrImage => {
      //console.log("File",qrImage)
    }).catch(err => {
      console.error(err)
    });

    // WRITE CSV after N lines
    if ((progress_count%csv_write_batch==0)){
      if (lines.length > 0){
        fs.appendFileSync(outfolder_path+csv_filename, lines);
      }
      console.log(lines);
      lines = '';
    }
    lines += "\r\n'"+zfilled+','+imfilename;

    // WRITE PROGRESS
    if (progress_count%report_progress_after == 0){
      fs.writeFileSync(outpath+progress_file, '['+progress_count.toString()+','+total_requiredc.toString()+']'); // stores progress
    }
    --serial;
    ++donecount;
    ++progress_count;
  }
  total_required -= donecount;
}

// write unwritten updates
if (lines.length > 0){
  console.log('final writing lines to ', outfolder_path);
  fs.appendFileSync(outfolder_path+csv_filename, lines);
}
fs.writeFileSync(outpath+progress_file, '['+progress_count.toString()+','+total_requiredc.toString()+']');

console.log(" Stopped at: ", donecount);
console.log(" Last Serial: ", serial+1);
console.log(" Number of digits_1: ", digits_count(serial+1));
