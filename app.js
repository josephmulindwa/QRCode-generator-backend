
// Require the package
const QRCode = require('qrcode');
const express =  require('express');

app = express();
app.use(express.json());

app.get('/', function(req, res){  
    res.send("You've reached the main page of QRCode Generator");
});

app.post('/qrcode', function(req, res){
    console.log('received item :', req.body.name);
    var user = req.body.user;
    var count = req.body.count;
    var length = req.body.length;
    var serial_string = req.body.serial_string;
});

app.listen(4500);