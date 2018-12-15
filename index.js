var express = require('express');
var bodyParser = require('body-parser');
var engines = require('consolidate');
var path = require('path');
var engines = require('consolidate');
var PythonShell = require('python-shell');
var passport = require('passport');
var Strategy = require('passport-local').Strategy;
var db = require('./db');

// Configure the local strategy for use by Passport.
//
// The local strategy require a `verify` function which receives the credentials
// (`username` and `password`) submitted by the user.  The function must verify
// that the password is correct and then invoke `cb` with a user object, which
// will be set at `req.user` in route handlers after authentication.
passport.use(new Strategy(
  function(username, password, cb) {
    db.users.findByUsername(username, function(err, user) {
      if (err) { return cb(err); }
      if (!user) { return cb(null, false); }
      if (user.password != password) { return cb(null, false); }
      return cb(null, user);
    });
  }));


// Configure Passport authenticated session persistence.
//
// In order to restore authentication state across HTTP requests, Passport needs
// to serialize users into and deserialize users out of the session.  The
// typical implementation of this is as simple as supplying the user ID when
// serializing, and querying the user record by ID from the database when
// deserializing.
passport.serializeUser(function(user, cb) {
  cb(null, user.id);
});

passport.deserializeUser(function(id, cb) {
  db.users.findById(id, function (err, user) {
    if (err) { return cb(err); }
    cb(null, user);
  });
});


var app = express();

// set up the template engine
app.engine('html', engines.hogan);
app.set('views', 'views');
app.set('view engine', 'html');
app.use(express.static(path.join(__dirname, 'public')));

app.use(passport.initialize());
app.use(passport.session());
// GET response for '/'
app.get('/',
  function(req, res) {
    res.render('login.html', { user: req.user });
    console.log(res.user);
  });

app.post('/login', 
  passport.authenticate('local', { 
  	successRedirect: '/home.html',
  	failureRedirect: '/',
  	failureFlash: true 
  }));

app.get('/login',
  function(req, res){
    res.render('home.html');
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