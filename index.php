<!DOCTYPE html>
<html>
<head>
	<!--<meta http-equiv="refresh" content="10">-->
	<!-- Better refresh tip http://www.d3noob.org/2013/02/update-d3js-data-dynamically-button.html
						and http://www.d3noob.org/2013/02/update-d3js-data-dynamically.html 
						
					   Read:https://leanpub.com/D3-Tips-and-Tricks/read#leanpub-auto-update-data-dynamically---on-click		-->
					   
					   
	<title>Welcome Littos thermal heaven!</title>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    body {
        max-width: 960px;
        /*margin: 0 auto;*/
        font-family: Tahoma, Verdana, Arial, sans-serif;
        font: 12px Arial;
    }
    
    
	.axis--x path {
		display: none;
	}
	.axis--op path {
		
	}	
	.axis--temp path {
		
	}

	.line {
		fill: none;
		stroke: steelblue;
		stroke-width: 1.5px;
	}
		
	.sp_line {
		fill: none;
		stroke: tomato;
		stroke-width: 1.5px;
	}
		
	.mv_line {
		fill: none;
		/*stroke: steelblue;*/
		stroke: green;
		stroke-width: 2.5px;
	}
		
	.op_line {
		fill: none;
		stroke: grey;
		stroke-width: 1px;
		stroke-dasharray: 6 2 3 2 6 2;
	}	
	
	.grid line {
		stroke: lightgrey;
		stroke-opacity: 0.7;
		shape-rendering: crispEdges;
	}

	.grid path {
		stroke-width: 0;
	}
	
	
	/*CSS rules for parts of the documents not related to Graph drawing (3djs) */
	
	.clear_float {
		clear: both;
	}
	
	.floatbox:nth-of-type(1) {
		width: 40%;
		margin: 20px auto;
		border: 1px solid black;
		padding: 10px;
		background-color: ghostwhite;
		float:left;
	}
	
	.floatbox:nth-of-type(2) {
		width: 40%;
		margin: 20px auto;
		border: 1px solid black;
		padding: 10px;
		background-color: ghostwhite;
		float:right;
	}
	
	form {
		width: 100%;
	}
	
	label {
		display: inline-block;
		width: 35%;
		text-align: left;
	}
	.radio, .numeric_short_important {
		font: 1.2em sans-serif;
		font-weight: bold;
	}
	
	input {
		width: 25%;
	}
	
	form div p{
		margin: 3px;
	}


</style>
</head>

<body>
	
	
<svg width="960" height="500"></svg>
<script src="/java/d3/d3.min.js"></script>
<!--<script src="https://d3js.org/d3.v5.min.js"></script>-->
<script> //PID graph
var svg = d3.select("svg"),
    margin = {top: 20, right: 50, bottom: 50, left: 50},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom,
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var parseTime = d3.timeParse("%Y-%m-%d %H:%M:%S");

var x = d3.scaleTime().range([0, width]);		// Time scale
var y = d3.scaleLinear().range([height, 0]);	//Temperature scale
var y_op = d3.scaleLinear().range([height, 0]);	//Output scale

var sp_valueline = d3.line()
    .x(function(d) { return x(d.time); })	//Time stamp
    .y(function(d) { return y(d.sp); });	//Set Point   y value scaled to Temperature ,(y), scale
    
var mv_valueline = d3.line()
    .x(function(d) { return x(d.time); })	//Time stamp
    .y(function(d) { return y(d.mv); });	//Measured value (temperature)   y value scaled to Temperature ,(y), scale
    
var op_valueline = d3.line()
    .x(function(d) { return x(d.time); })	//Time stamp
    .y(function(d) { return y_op(d.op); });	//PID controller output, 0-100%  y value scaled to Output ,(y_op), scale     

var x_axis = d3.axisBottom(x)
	.ticks(10);

var temp_axis = d3.axisRight(y)
	.ticks(10);
	
var op_axis = d3.axisLeft(y_op)
	.ticks(10);
	
// gridlines in x axis function
function make_x_gridlines() {		
    return d3.axisBottom(x)
        .ticks(10)
}

// gridlines in y axis function
function make_y_gridlines() {		
    return d3.axisLeft(y)
        .ticks(10)
}	
    
// Get the data
// The first callback function is executed for all values, 
//the second function is executed after all values have been loaded
//d3.csv("/testtemp", function(d) {
d3.csv("/volatile/temperatures", function(d) {
  d.time = parseTime(d.time);
  d.sp = +d.sp;
  d.mv = +d.mv;
  d.op = +d.op;
  return d;
}, function(error, data) {
  if (error) throw error;
console.log(data);

  x.domain(d3.extent(data, function(d) { return d.time; }));
  //y.domain(d3.extent(data, function(d) { return Math.max(d.mv, d.sp); }));		//###The maximum value is the greater of Sp or Mv!
  //y.domain[0] = d3.min(data, function(d) { return Math.min(d.mv, d.sp); }); //Lower y domain limit is lesser of min sp and min mv
  //y.domain[1] = d3.max(data, function(d) { return Math.max(d.mv, d.sp); });//U pery domain limit is higher of max sp and max mv
  //console.log(d3.min(data, function(d) { return Math.min(d.mv, d.sp); }));
  //console.log(d3.max(data, function(d) { return Math.max(d.mv, d.sp); }));
  var ymin = d3.min(data, function(d) { return Math.min(d.mv, d.sp); }); //Lower y domain limit is lesser of min sp and min mv
  var ymax = d3.max(data, function(d) { return Math.max(d.mv, d.sp); }); //Upper y domain  limit is higher of max sp and max mv
  y.domain([ymin*0.975,ymax*1.025]);

  y_op.domain([0,100]);	//The output domain is 0-100% 
  
  // add the X gridlines
  g.append("g")			
      .attr("class", "grid")
      .attr("transform", "translate(0," + height + ")")
      .call(make_x_gridlines()
          .tickSize(-height)
          .tickFormat("")
      )

  // add the Y gridlines
  g.append("g")			
      .attr("class", "grid")
      .call(make_y_gridlines()
          .tickSize(-width)
          .tickFormat("")
      )
  
  // add x axis
  g.append("g")
      .attr("class", "axis axis--x")
      .attr("transform", "translate(0," + height + ")")
      .call(x_axis);
  
  // add y axis for temperature
  g.append("g")
      .attr("class", "axis axis--temp")
      .attr("stroke", "steelblue")
      .attr("transform", "translate(" + width + ",0)")
      .call(temp_axis)
    .append("text")
      .attr("fill", "#000")
      //.attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .style("text-anchor", "end")
      .attr("transform", "translate(35," + (height - 20) + ")")
      .text("deg C");  
  
  // add value lines for set point and measured temp
  g.append("path")
      .datum(data)
      .attr("class", "sp_line")
      .attr("d", sp_valueline);
      
  g.append("path")
      .datum(data)
      .attr("class", "mv_line")
      .attr("d", mv_valueline);
  
  // add y axis for output value
  g.append("g")
      .attr("class", "axis axis--op")
      .attr("stroke", "grey")
      .call(op_axis)
    .append("text")
      .attr("fill", "#000")
      //.attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .style("text-anchor", "end")
      .attr("transform", "translate(-10," + (height - 20) + ")")
      .text("output");
  
  // add value line for output value    
  g.append("path")
      .datum(data)
      .attr("class", "op_line")
      .attr("d", op_valueline);
      
  // Add numerials for MV C (SP C)  and OP %
  g.append("text")
      .attr("class", "mv_text")
      .attr("fill", "green")
      //.attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .style("text-anchor", "start")
      .attr("transform", "translate(" + (width/2-125) + "," + (height +25) + ")")
      .attr("font-size", "150%")
      .text(data[data.length-1].mv.toFixed(2) + " C" );
      
  g.append("text")
      .attr("class", "sp_text")
      .attr("fill", "tomato")
      //.attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .style("text-anchor", "middle")
      .attr("transform", "translate(" + width/2 + "," + (height +25) + ")")
      .attr("font-size", "150%")
      .text("(" + data[data.length-1].sp.toFixed(2) + " C )");
      
  g.append("text")
      .attr("class", "op_text")
      .attr("fill", "grey")
      //.attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .style("text-anchor", "end")
      .attr("transform", "translate(" + (width/2+125) + "," + (height +25) + ")")
      .attr("font-size", "150%")
      .text(data[data.length-1].op.toFixed(1) + "%");               
});


//Update at an interval, expressed in ms
var inter = setInterval(function() {
                updateData();
        }, 2500);

//Update data
function updateData() {

   // Get the data again
    // The first callback function is executed for all values, 
	//the second function is executed after all values have been loaded
	d3.csv("/volatile/temperatures", function(d) {
	  d.time = parseTime(d.time);
	  d.sp = +d.sp;
	  d.mv = +d.mv;
	  d.op = +d.op;
	  return d;
	}, function(error, data) {
	  if (error) throw error;
	console.log(data);
	
	//Redo the domain calculations as data may be out of bounds	
	  x.domain(d3.extent(data, function(d) { return d.time; }));
	  var ymin = d3.min(data, function(d) { return Math.min(d.mv, d.sp); }); //Lower y domain limit is lesser of min sp and min mv
	  var ymax = d3.max(data, function(d) { return Math.max(d.mv, d.sp); }); //Upper y domain  limit is higher of max sp and max mv
	  y.domain([ymin*0.975,ymax*1.025]);
	
	  y_op.domain([0,100]);	//The output domain is 0-100% 
	  
	//Select what to apply the changes to
	  var svg = d3.select("body").transition();
	  
	//Make the updates
	svg.select(".sp_line")   // change the set point line
            .duration(2)
            .attr("d", sp_valueline(data));
    svg.select(".mv_line")   // change the measured value line
            .duration(2)
            .attr("d", mv_valueline(data));
	svg.select(".op_line")   // change the output value line
            .duration(2)
            .attr("d", op_valueline(data));
            
    svg.select(".axis--x") // change the x axis
            .duration(2)
            .call(x_axis);
    svg.select(".axis--temp") // change the temp axis
            .duration(2)
            .call(temp_axis);

    // output axis will not change, so lets skip that item
    
    //Update numeric instant values under the graph too
    svg.select(".mv_text")
			.text(data[data.length-1].mv.toFixed(2) + " C" );
    svg.select(".sp_text")
			.text("(" + data[data.length-1].sp.toFixed(2) + " C )");;
    svg.select(".op_text")
			.text(data[data.length-1].op.toFixed(1) + "%");						
	  });
}


</script>
<p>
<p>
<div class="floatbox">
	<h2>Controller settings</h2>
		
	<?php 
		$datafil = fopen("data_to_cnt", "r") or die("Unable to open cntrl file!");
		$mode = rtrim(fgets($datafil));
		$SP = rtrim(fgets($datafil));
		$OP = rtrim(fgets($datafil));
		$P = rtrim(fgets($datafil));
		$I = rtrim(fgets($datafil));
		$D = rtrim(fgets($datafil));
		$exec_int = rtrim(fgets($datafil));
		$log_int = rtrim(fgets($datafil));
		fclose($datafil);
	?>
	<form action="set_data.php" method="post">
		<div class="radio">
			<p>	
			<input type="radio" name="mode" value="off" <?php if ($mode=='off') {echo ' checked'; } ?>>Off<br>
			</p>
			<p>
			<input type="radio" name="mode" value="man" <?php if ($mode=='man') {echo ' checked'; } ?>>Man<br>
			</p>
			<p>
			<input type="radio" name="mode" value="aut" <?php if ($mode=='aut') {echo ' checked'; } ?>>Auto<br>
			</p>
		</div>
		<br>
		<div class ="numeric_short_important">
			<p>
				<label for="SP">Set point: </label>
				<input type="text" name="SP" value=<?php echo $SP ?>> C<br>
			</p>
			<p>
				<label for="OP">Output: </label>
				<input type="text" name="OP" value=<?php echo $OP ?>> %<br>
			</p>
		</div>
		<br>
		<div class="numeric_short">
			<p>
				<label for="P">P:</label>
				<input type="text" name="P" value=<?php echo $P ?>><br>
			</p>
			<p>
				<label for="I">I: </label>
			    <input type="text" name="I" value=<?php echo $I ?>> s<br>
			</p>
			<p>
				<label for="D">D: </label>
				<input type="text" name="D" value=<?php echo $D ?>> s<br>
			</p>
		</div>
		<br>
		<div class="numeric_long">
			<p>
				<label for="exec_int">Exe int.: </label>
				<input type="text" name="exec_int" value=<?php echo $exec_int ?>> ms<br>
			</p>
			<p>
				<label for="log_int">Log int.: </label>
				<input type="text" name="log_int" value=<?php echo $log_int ?>> min<br>
			</p>
		</div>
		<br>
		<input type="submit" value="Set">
	</form>	
</div>
<div class="floatbox">
	<h2>Sequence</h2>
	<p>Valid items</p>
	<ul>
		<li>ramp-to-in XXX, YYY  [XXX degC, YYY min]</li>
		<li>ramp-to-at XXX, YYY  [XXX degC, YYY degC/min]</li>
		<li>hold-for XXX  [XXX min]</li>
		<li>wait-to-reach XXX  [XXX degC]</li>
		<li>new-sp XXX  [XXX degC]</li>
		<li>new-sp XXX [XXX degC]</li>
		<li>next-step # [# step number]</li>
	</ul>
	<br>
	<?php

		ini_set("auto_detect_line_endings", true);
		$seqfil = fopen("sequence", "r") or die("Unable to open sequence file!");
		$index=0;
		while(!feof($seqfil)) {
			$seq[$index]=fgets($seqfil);
			$index++;
		}
		fclose($seqfil);
		
		$seq_status_fil = fopen("volatile/sequence_status", "r") or die("Unable to open sequence_status file!");
		$index=0;
		while(!feof($seq_status_fil)) {
			$seq_status[$index]=fgets($seq_status_fil);
			$index++;
		}
		fclose($seq_status);
		
		ini_set("auto_detect_line_endings", false);
	?>
	<form action="set_step.php" method="post">
		<div>
			<?php  echo "<p>Step: " . $seq_status[0] . "    Time: " . round($seq_status[1]) ." min</p>";?>
			<input type="submit" value="Set step">
		</div>
	</form>
	<form action="set_recepy.php" method="post">
		<textarea name="sequence" cols="40" rows="12" wrap="off"><?php foreach($seq as $seqrow){echo($seqrow);}?></textarea>
		<input type="submit" value="Save">
	</form>
</div>	
<div class="clear_float"></div>

<br>
<p>Contoller interface is running on Nginx, see <a href="http://nginx.org/">nginx.org</a>.<br/>

<p>
<a href="https://developer.mozilla.org/en-US/docs/Learn/CSS">Good source of HTML and CSS knowledge.</a>.<br/>
<a href="http://www.d3noob.org">Good source of 3Djs knowledge.</a>.<br/>
</body>
</html>
