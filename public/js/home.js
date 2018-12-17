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

		if (data.status == "Error"){
			alert( data.status + data.message );
		}
		else{
			$('#program').val('Select program');
			$('#year').val('Select year');
			$('#day').val('');
			$('#survey_id').val('');
			alert(alert( data.status + data.message );)
		}
	
		console.log(data);

	});

})
