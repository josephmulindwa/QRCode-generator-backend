const QRCode = require('qrcode')
const fs = require('fs')

var lp = 100
var serial = lp
var totalLength = 10
var total = 5000
var stop =0;

function digits_count(n) {
  var count = 0;
  if (n >= 1) ++count;

  while (n / 10 >= 1) {
    n /= 10;
    ++count;
  }

  return count;
}

function addLeadingZeros(num, totalLength) {
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

QRCode.toString([
    { data: 'shraddha.paghdar@gmail.com', mode: 'byte' },
    { data: '+78787878', mode: 'byte' }
]
).then(qrImage => {
  //console.log("terminal",qrImage)
}).catch(err => {
    console.error(err)
})

QRCode.toDataURL('Hi testing QR code', opts).then(qrImage => {
  //console.log("URL",qrImage)
}).catch(err => {
    console.error(err)
}) 

while (total != stop && lp != 0){
	//console.log(" Number of digits: ", digits_count(serial))
	//console.log(addLeadingZeros(serial, totalLength))
	serial2 = addLeadingZeros(serial, totalLength)

	qrFile = 'qrCode'.concat(lp,'.png'),'OBR-Vignette Fiscale 2022'.concat("-", serial2)
	QRCode.toFile('output/qrCode'.concat(lp,'.png'),'OBR-Vignette Fiscale 2022'.concat("-", serial2), opts).then(qrImage => {
		//console.log("File",qrImage)
	}).catch(err => {
		console.error(err)
	})

	//console.log(" Number of digits: ", digits_count(serial))
	 
	 serial = serial -1
	 --total
	 --lp
	 ++stop
	 
}

console.log(" Stop: ", stop)
console.log(" Last Serial: ", serial)
console.log(" Number of digits_1: ", digits_count(serial))
 
