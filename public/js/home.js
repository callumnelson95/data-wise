$( document ).ready(function(){
	$.get('/data/uploaded_surveys.csv',function(data){
		console.log(data);
		create_table(data);
	})

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
				alert( data.status + data.message );
			}
		
			console.log(data);

		});

		$.get('/data/uploaded_surveys.csv',function(data){
			console.log(data);
			create_table(data);
		})

	})

	$('#reset-button').click(function(){
		console.log('Reset click!')
		$('#program').val('Select program');
		$('#year').val('Select year');
		$('#day').val('');
		$('#survey_id').val('');
	});

})

function create_table(data){
	var allRows = data.split(/\r?\n|\r/);

	$('.table').empty();

	var table;
	for (var singleRow = 0; singleRow < allRows.length; singleRow++) {
		if (singleRow === 0) {
		  table += '<thead>';
		  table += '<tr>';
		} else {
		  table += '<tr>';
		}
		var rowCells = allRows[singleRow].split(',');
		if (rowCells[rowCell] == ''){
			continue;
		}
		for (var rowCell = 0; rowCell < rowCells.length; rowCell++) {
		  if (singleRow === 0) {
		    table += '<th>';
		    table += rowCells[rowCell];
		    table += '</th>';
		  } else {
		    table += '<td>';
		    table += rowCells[rowCell];
		    table += '</td>';
		  }
		}
		if (singleRow === 0) {
		  table += '</tr>';
		  table += '</thead>';
		  table += '<tbody>';
		} else {
		  table += '</tr>';
		}
	} 
	table += '</tbody>';

	$('.table').append(table);
}

