$ (document).ready(function() {
	console.log("Login page is ready!");
})

var signin_button = $('#signin');

signin_button.click(function(){
	var email = $('#inputEmail').val();
	var password = $('#inputPassword').val();

	$.get('/signin.json', {e: email, p: password}, function(res){
		console.log(res);
	});
})