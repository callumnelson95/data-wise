var express = require('express');
var bodyParser = require('body-parser');
var path = require('path');
const ps = require('python-shell');
var passport = require('passport');
var Strategy = require('passport-local').Strategy;
var db = require('./db');
require('dotenv').config()

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

const port = process.env.PORT || 8080;

// set up the template engine
app.set('views', __dirname + '/views');
app.set('view engine', 'ejs');
app.use(express.static(path.join(__dirname, 'public')));

app.use(require('morgan')('combined'));
app.use(require('cookie-parser')());
app.use(require('body-parser').urlencoded({ extended: true }));
app.use(require('express-session')({ secret: 'keyboard cat', resave: false, saveUninitialized: false }));


app.use(passport.initialize());
app.use(passport.session());
// GET response for '/'
app.get('/',
  function(req, res) {
    res.render('home', { user: req.user });
    console.log(res.user);
  });

app.get('/login',
  function(req, res){
    res.render('login');
  });
  
app.post('/login', 
  passport.authenticate('local', { failureRedirect: '/login', failureFlash: true}),
  function(req, res) {
    res.redirect('/');
  });

app.get('/logout',
  function(req, res){
    req.logout();
    res.redirect('/');
  });

app.post('/run', runNormalizer);

function runNormalizer(req, res) {

	var program = req.body.p;
	var year = req.body.y;
	var day = req.body.d;
	var survey_id = req.body.sid;

	console.log(program);
	console.log(year);
	console.log()

	if (program == "Select program"){
		data = {response: "Error: Please be sure to select the program"}
		res.json(data);
		return
	}else if (year == "Select year"){
		data = {response: "Error: Please be sure to select the year"}
		res.json(data);
		return
	}else if (survey_id == '' || survey_id.substring(0,2) != 'SV'){
		data = {response: "Error: You either did not enter an ID or entered an invalid ID"}
		res.json(data);
		return
	}
	
	var input = year.concat("_").concat(program)

	if (day != 'N/A' || day != 'Select day'){
		input = input.concat("_").concat(day)
	}

	console.log(input);
	console.log(process.env.X_API_TOKEN);

	var options = {
		  mode: 'text',
		  args: [input, survey_id, process.env.X_API_TOKEN]
	};

	ps.PythonShell.run('qualtrics_online.py', options, function (err, results) {
	  	if (err) throw err;
	  	console.log('Starting process');
	  	data = {response: "Success: Visit the dashboard to see the new data!"}
		console.log(results);
		console.log('Success!');
		res.json(data);
		return
	});

}


app.listen(port, function() {
	console.log("Listening on " + port);
});