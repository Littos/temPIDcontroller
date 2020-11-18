<?php
/*
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
*/

$sequencetext=$_POST['sequence'];

//echo($sequencetext);

$ret = file_put_contents('sequence', $sequencetext);
    if($ret === false) {
        die('There was an error writing this file');
    }
    else {
    }

header("location:index.php");

?>
