var express = require('express');
var bodyParser = require('body-parser');
var engines = require('consolidate');
var path = require('path');
var PythonShell = require('python-shell');
var app = express();
 
// set up the template engine
app.engine('html', engines.hogan);
app.set('views', './views');
app.set('view engine', 'html');
app.use(express.static(path.join(__dirname, 'public')));
 
// GET response for '/'
app.get('/', function (req, res) {
    // render the 'home' template
    res.render('index.html');

});

app.get('/signin.json', function(req, res) {

	var email = req.query.e;
	var password = req.query.p;

	console.log(email);
	console.log(password);

	if (email == "datawiseproject@gmail.com" && password == "dwharvard123!"){

		res.render('home.html');
	}else{
		res.json({status: "Failure"})
	}

});

var port = process.env.PORT || 8080;


function successPrediction(request, response) {
	var n = request.query
	var fields = n.fields;
	var values = n.values;
	console.log(fields.concat(values));

	var options = {
	  	mode: 'text',
	  	pythonPath: '/usr/local/bin/python3',
	  	pythonOptions: ['-u'],
	  	scriptPath: 'public/ml',
	  	args: fields.concat(values)
	};

	PythonShell.run('edit_feat.py', options, function (err, results) {
	  	if (err) throw err;


		var options = {
		  mode: 'text',
		  pythonPath: '/usr/local/bin/python3',
		  pythonOptions: ['-u'],
		  scriptPath: 'public/ml',
		  args: []
		};

	  	PythonShell.run('predict_success.py', options, function (err, results) {
		  if (err) throw err;
		  // results is an array consisting of messages collected during execution
		  label = parseFloat(results[0])
		  response.json(label);
		  console.log('results: %j', results[0]);
	  
		});
	});
}


app.listen(port, function() {
	console.log("Listening on " + port);
});