var express = require('express');
var bodyParser = require('body-parser');
var path = require('path');
const ps = require('python-shell');
var passport = require('passport');
var Strategy = require('passport-local').Strategy;
var db = require('./db');
require('dotenv').config()
var fs = require('fs');
var csvWriter = require('csv-write-stream');
var writer = csvWriter();
var parse = require('csv-parse');



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

	if (program == "Select program"){
		data = {status: "Error",
				message:": Please be sure to select the program"}
		res.json(data);
		return
	}else if (year == "Select year"){
		data = {status: "Error",
				message:": Please be sure to select the year"}
		res.json(data);
		return
	}else if (survey_id == '' || survey_id.substring(0,2) != 'SV'){
		data = {status: "Error",
				message:": You either did not enter an ID or entered an invalid ID"}
		res.json(data);
		return
	}
	
	var input = year.concat("_").concat(program)

	if (day != 'N/A' || day != 'Select day'){
		input = input.concat("_").concat(day)
	}

	console.log(input);
	console.log(process.env.key_one);

	var match = 0;

	fs.readFile('./public/data/uploaded_surveys.csv', function (err, fileData) {
	parse(fileData, {columns: false, trim: true}, function(err, rows) {
		console.log(rows);
	    for (var i = rows.length - 1; i >= 0; i--) {
	    	var current_id = rows[i][3];
	    	console.log(current_id);
	    	if (current_id == survey_id){
	    		match = 1;
	    	}
	    }
	    if (match == 1){
			data = {status: "Error",
		  				message:  ": You have entered the ID of a survey that already exists. Please use a new survey ID."};
	  		res.json(data);
	  		console.log('IDs match! Uh oh.')
	  		return
		}
	  })
	});

	var options = {
		  mode: 'text',
		  args: [input, survey_id, process.env.key_one]
	};

	ps.PythonShell.run('qualtrics_online.py', options, function (err, results) {
	  	/*if (err) {
	  		data = {response: "Error: You may have incorrectly entered the qualtrics ID. Double check to make sure it is copied correctly."};
	  		res.json(data);
	  		//throw err;
	  		return
	  	}*/
	  	if (results == undefined){
	  		data = {status: "Error",
	  				message:  ": You may have incorrectly entered the qualtrics ID. Check to make sure you have the correct survey ID."};
	  		res.json(data);
	  		return
	  	}
	  	else{
	  		console.log('Starting process');
		  	data = {status: "Success",
		  			message: ": Visit the dashboard to see the new data!"}
			console.log(results);
			console.log('Success!');
			//add_to_surveys_csv(program, year, day, survey_id);
			res.json(data);
			return
	  	}
	  	
	});

}

function add_to_surveys_csv(program, year, day, survey_id){
	var options = {
		  mode: 'text',
		  args: [program, year, day, survey_id]
	};

	ps.PythonShell.run('write_to_csv.py', options, function (err, results) {
	  	if (err) throw err;
	});

}

function check_for_id(survey_id){
	var match = 0;

	fs.readFile('./public/data/uploaded_surveys.csv', function (err, fileData) {
	parse(fileData, {columns: false, trim: true}, function(err, rows) {
		console.log(rows);
	    for (var i = rows.length - 1; i >= 0; i--) {
	    	var current_id = rows[i][3];
	    	console.log(current_id);
	    	if (current_id == survey_id){
	    		return 1;
	    	}
	    }
	  })
	});

	console.log(match);
	return match;
}

app.listen(port, function() {
	console.log("Listening on " + port);
});