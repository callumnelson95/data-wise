var express = require('express');
var bodyParser = require('body-parser');
var engines = require('consolidate');
var path = require('path');
var app = express();
 
// set up the template engine
app.engine('html', engines.hogan);
app.set('views', './views');
app.set('view engine', 'html');
app.use(express.static(path.join(__dirname, 'public')));
 
// GET response for '/'
app.get('/', function (req, res) {
    // render the 'index' template, and pass in a few variables
    res.render('index.html');

});

var port = process.env.PORT || 8080;





app.listen(port, function() {
	console.log("Listening on " + port);
});