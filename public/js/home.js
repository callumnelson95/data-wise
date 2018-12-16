$('#submit-button').click(function(){

	var program = $('#program').val();
	var year = $('#year').val();
	var day = $('#day').val();
	var survey_id = $('#survey_id').val();

	var data = {
		p : program,
		y : year,
		d : day,
		sid : survey_id
	}

	$.post( "/run", data, function( data ) {

		alert( data.response );

		console.log(data);
		
	});

})
