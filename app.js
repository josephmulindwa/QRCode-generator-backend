
// Require the package
const QRCode = require('qrcode')

let data = {
    name:"Employee Name",
    age:27,
    department:"Police",
    id:"aisuoiqu3234738jdhf100223"
}

// Converting into String data
let stringdata = JSON.stringify(data)

// Print the QR code to terminal
QRCode.toString(stringdata,{type:'terminal'}, function (err, url) {
   if(err) return console.log("error occurred")
   console.log(url)
 })
 
 // Get the base64 url
QRCode.toDataURL(stringdata, function (err, url) {
    if(err) return console.log("error occurred")
    console.log(url)
})


