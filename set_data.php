<?php

$mode = $_POST['mode'];

$SP = $_POST['SP'];
$OP = $_POST['OP'];

$P = $_POST['P'];
$I = $_POST['I'];
$D = $_POST['D'];

$exec_int = $_POST['exec_int'];
$log_int = $_POST['log_int'];

#$data = 'mode,SP,OP,P,I,D' . "\n";
#$data = $data . $mode . ',' . $SP . ','. $OP . ','. $P . ','. $I . ','. $D . "\n";
$data = $data . $mode . "\n" . $SP . "\n". $OP . "\n". $P . "\n". $I . "\n". $D . "\n" . $exec_int . "\n" . $log_int . "\n";
#echo(shell_exec("whoami"));
$ret = file_put_contents('data_to_cnt', $data, LOCK_EX);
    if($ret === false) {
        die('There was an error writing this file');
    }
    else {
    }

header("location:index.php");
?>
