<?php

# This file is based on the Apache 2.0 licensed version of the project
# https://raw.githubusercontent.com/Woersty/LoxBerry-Plugin-cam-connect/
# file v2018.10.28/webfrontend/html/index.php .
# It has been modified to accomodate changes wrt. the webUI in use as well as
# adjust style (max. 80 cpl), fix minor errors, and add new features like
# cropping). For more details have a look at the NOTICE.txt file.

# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License") version 1.1!
# You may not use this file except in compliance with the License.
#
# See LICENSE.txt and NOTICE.txt included in this distribution for the specific
# language governing permissions and limitations under the License.
#
# Copyright 2018 Jens Elkner (jel+loxberry-src@cs.ovgu.de)


###############################################################################
# Loxberry Plugin to change the HTTP-Authentication of a Trendnet TV-IP310PI
# Surveillance IP-Cam from Digest to none to be used in the
# Loxone Door-Control-Object.
###############################################################################

// Error Reporting off
error_reporting(~E_ALL & ~E_STRICT);
ini_set('display_errors', false);		// Fehler nicht direkt via PHP ausgeben
require_once 'loxberry_system.php';
require_once 'loxberry_log.php';
$L = LBSystem::readlanguage('language.ini');
$plugindata = LBSystem::plugindata();
ini_set('log_errors', 1);
ini_set('error_log', $lbplogdir . '/' . LBPPLUGINDIR . '.log');

if (!isset($_GET['cam'])) {
	$cam = '';
	error_image($L['ERR.NO_CAM_PARAM']);
	exit;
}
$cam = intval($_GET['cam']);
debug("Camera $cam requested.", 7);

$datetime = new DateTime;

function debug($message = '', $loglevel = 7, $raw = 0) {
	global $L, $cam, $plugindata;

	if ($plugindata['PLUGINDB_LOGLEVEL'] < intval($loglevel) && $loglevel != 8)
		return;

	if ($raw != 1)
		$message = 'Cam #'. $cam .': ' . $message;

	switch ($loglevel) {
	    case 0:
	        // OFF
	        break;
	    case 1:
	        error_log(strftime("%A") . ' <ALERT> PHP: ' . $message);
	        break;
	    case 2:
	    case 8:
	        error_log(strftime("%A") . ' <CRITICAL> PHP: ' . $message);
	        break;
	    case 3:
	        error_log(strftime("%A") . ' <ERROR> PHP: ' . $message);
	        break;
	    case 4:
	        error_log(strftime("%A") . ' <WARNING> PHP: ' . $message);
	        break;
	    case 5:
	        error_log(strftime("%A") . ' <OK> PHP: ' . $message);
	        break;
	    case 6:
	        error_log(strftime("%A") . ' <INFO> PHP: ' . $message);
	        break;
	    case 7:
	    default:
	        error_log(strftime("%A") . ' PHP: ' . $message);
	        break;
	}
	if ($loglevel < 4 && isset($message) && $message != '' ) {
		notify(LBPPLUGINDIR, $L['CC.MY_NAME'], $message);
	}
	return;
}

// Check for GD Library
if (!function_exists (@ImageCreate)) {
	debug($L['ERR.IMG_FN_MISSING'], 8);
	die($L['ERR.IMG_FN_MISSING']);
}
if (!function_exists (@curl_init)) {
	debug($L['ERR.INIT_CURL'], 8);
	die($L['ERR.INIT_CURL']);
}

$cfg = LBPCONFIGDIR . '/' . LBPPLUGINDIR . '.cfg';
$cfg_handle = fopen($cfg, 'r') or debug($L['ERR.READING_CFG'], 4);
if (! $cfg_handle) {
	debug('Plugin config file ' . $cfg . ' not found.', 7);
	error_image($L['ERR.READING_CFG']);
	exit;
}

while (!feof($cfg_handle)) {
	$line_of_text = fgets($cfg_handle);
	if (strlen($line_of_text) > 3) {
		$config_line = explode('=', $line_of_text);
		if ($config_line[0]) {
			if (!isset($config_line[1]))
				$config_line[1] = '';
			$plugin_cfg[$config_line[0]] = preg_replace('/\r?\n|\r/', '',
				str_ireplace('"', '', $config_line[1]));
		}
	}
}
fclose($cfg_handle);

$log = LBPLOGDIR . '/' . LBPCONFIGDIR . '.log';
debug($L['ERR.ENTER_PLUGIN'] . ' ' . $_SERVER['REMOTE_ADDR']
	. "\n+ + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + +"
	. "+ + + + + + + + + + + + + + + + + + + + + +", 5);
$logsize = filesize($log);
if ($logsize > 5242880) {
    debug($L['ERR.LOGFILE_TOO_BIG'] . ' (' . $logsize . ' Bytes)', 4);
    debug('Set Logfile notification: ' . $log
		. ' => ' . $L['ERR.LOGFILE_TOO_BIG'], 7);
    notify(LBPPLUGINDIR, $L['CC.MY_NAME'], $L['ERR.LOGFILE_TOO_BIG']
		. ' (' . $logsize . ' Bytes)');
	system("echo '' > " . $log);
}

$camera_models_file = LBPDATADIR . '/camera_models.dat';
debug('Reading cameras from ' . $camera_models_file, 7);
$lines_of_text = file($camera_models_file);

if (!isset($plugin_cfg['MODEL' . $cam])) {
	error_image($L["ERR.READING_MODEL"]);
	exit;
}

$cam_model = intval($plugin_cfg['MODEL' . $cam]);
debug("Camera model for camera $cam is " . $cam_model, 7);

foreach($lines_of_text as $line_num => $line_of_text) {
	debug("Read cameras line $line_num: " . $line_of_text, 7);
	$line_of_text = preg_replace('/\r?\n|\r/', '', $line_of_text);
	$config_line = explode('|', $line_of_text);
	if (count($config_line) == 5) {
		if (intval($config_line[0]) == $cam_model) {
			$plugin_cfg['httpauth'] = $config_line[4];
			$plugin_cfg['imagepath'] = $config_line[3];
			$plugin_cfg['model'] = $config_line[2];
			debug($L['ERR.CAM_FOUND'] . ' ' . ($line_num + 1) . "\n"
				. $line_of_text, 5);
			debug('Stop reading camera file', 7);
			break;
		} else {
			debug("Did not found the camera we're looking for at line "
				. $line_num . ": " . $line_of_text, 7);
		}
	} else {
		debug($L['ERR.CAM_LIST_LINE'].' '. $line_num .' => '. $line_of_text, 4);
	}
}

if ($plugin_cfg['model'] == '' || $plugin_cfg['httpauth'] == ''
	|| $plugin_cfg['imagepath'] == '')
{
	error_image($L['ERR.READING_CAMS']);
	exit;
}

debug('Read LoxBerry global eMail config', 7);
if ($plugin_cfg['MAIL' . $cam] == 1) {
	$mail_cfg = LBSCONFIGDIR . '/mail.cfg';
	debug("MAIL$cam enabled, reading config from " . $mail_cfg, 7);
	$mail_cfg = parse_ini_file($mail_cfg, true);
	if (!isset($mail_cfg)) {
		debug("Can't read eMail config", 7);
		error_image($L['ERR.READING_MAIL_CFG']);
		exit;
	}
	debug($L['ERR.MAIL_CONFIG_OK'] .' ['. $mail_cfg['SMTP']['SMTPSERVER'] .':'
			. $mail_cfg['SMTP']['PORT'] . ']', 5);
	if ($mail_cfg['SMTP']['ISCONFIGURED'] == '0') {
		debug('eMail ist not configured: SMTP.ISCONFIGURED is 0', 7);
		error_image($L['ERR.INVALID_MAIL_CFG']);
		exit;
	}
	if (!isset($plugin_cfg['EMAIL_FILENAME'])) {
		$plugin_cfg['EMAIL_FILENAME'] = 'Snapshot';
	}
} else {
	debug($L['ERR.MAIL_NOT_USED'], 5);
}

if (isset($plugin_cfg['NAME'.$cam]) && $plugin_cfg['NAME'.$cam] != '') {
	$cam_name = '[' . addslashes($plugin_cfg['NAME' . $cam]) . '] ';
} else {
	$cam_name = '';
}
debug('NAME=' . $cam_name, 7);

if (!isset($plugin_cfg['ADDR' . $cam])) {
	error_image($L['ERR.INVALID_ADDR']);
	exit;
}

exec('/bin/ping -c 1 ' . $plugin_cfg['ADDR' . $cam], $output, $return_var);
if ($return_var != 0) {
	error_image($L['ERR.PING_ERR'] . ' ' . $plugin_cfg['ADDR' . $cam]);
	exit;
}

$plugin_cfg['url'] = 'http://' . trim(addslashes($plugin_cfg['ADDR' . $cam]
	. ':' . $plugin_cfg['PORT'.$cam] . $plugin_cfg['imagepath']));
debug('Using url: ' . $plugin_cfg['url'], 7);
$plugin_cfg['user'] = addslashes($plugin_cfg['USERNAME' . $cam]);
debug('Using user: ' . $plugin_cfg['user'], 7);
$plugin_cfg['pass'] = addslashes($plugin_cfg['PW' . $cam]);
debug('Using pass: ' . $plugin_cfg['pass'], 7);

function get_image($retry = 0) {
	global $plugin_cfg, $curl, $lbpplugindir, $L, $cam, $plugindata;
	$retry = intval($retry);
	debug("Function get_image called ($retry) for camera $cam with hostname/IP:"
		. $plugin_cfg['Addr' . $cam], 7);
	if (!($curl = curl_init())) {
		error_image($L['ERR.INIT_CURL']);
		exit;
	}
	curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
	curl_setopt($curl, CURLOPT_HTTPAUTH, constant($plugin_cfg['httpauth']));
	curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'GET');
	curl_setopt($curl, CURLOPT_USERPWD,
		$plugin_cfg['user'] . ':' . $plugin_cfg['pass']);
	curl_setopt($curl, CURLOPT_URL, $plugin_cfg['url']);
	if ($plugin_cfg['model'] == 'DN-16049') {
		debug('Digitus DN-16049 - special handling ...', 7);
		foreach(split("\n", curl_exec($curl)) as $k => $html_zeile) {
			if (preg_match("/\b.jpg\b/i", $html_zeile)) {
				$anfang = stripos($html_zeile, '"../../..') + 9;
				$ende = strrpos($html_zeile, '.jpg"') - 5 - 9;
				$plugin_cfg['url'] = 'http://'
					. trim(addslashes($plugin_cfg['ADDR' . $cam] . ':'
					. $plugin_cfg['PORT' . $cam]
					. substr($html_zeile, $anfang, $ende)));
				debug("Line with '.jpg' found => URL:" . $plugin_cfg['url'], 7);
				break;
			} else {
				debug("No line with '.jpg' found. Keep going ...", 7);
			}
		}
	} else {
		debug($plugin_cfg['model'] . ' - normal handling', 7);
		debug("Image URL: " . $plugin_cfg['url'], 7);
		$picture = curl_exec($curl)
			or debug($L['ERR.CURL'] . ' ' . $plugin_cfg['url'], 3);
	    if ($curl) {
			curl_close($curl);
		}

		if (strlen($picture) < 2000 && $retry <= 1) {
			debug($L['ERR.IMG_RETRY'] . "\n" . $picture, 7);
			sleep(.25);
			$picture = get_image($retry + 1);
		}
		if (strlen($picture) < 2000 && $retry <= 2) {
			debug($L['ERR.IMG_LAST_RETRY'], 4);
			debug($L['ERR.IMG_LAST_RETRY_DEBUG'] . "\n"
				. $picture, 7);
			sleep(.25);
			$picture = get_image($retry + 1);
		} else {
			debug('Image successfully read from the camera.', 7);
			if ($plugindata['PLUGINDB_LOGLEVEL'] == 7) {
				$finfo = new finfo(FILEINFO_MIME);
				$type = explode(';', $finfo->buffer($picture), 2)[0];
				debug('Type: ' . $type
					. ' Size: ' . strlen($picture) . ' Bytes', 7);
				if (!isset($_GET['stream'])) {
//debug("<img src='data:".$type.";base64,".base64_encode($picture)."' />",7);
//debug("<img src='data:".$type.";base64,".base64_encode($picture)."' />",7,1);
				} else {
					debug("Picture:\n[not shown in stream mode]", 7);
				}
			}
		}
	}
	if (strlen($picture) < 2000) {
		debug($L['ERR.IMG_TOO_SMALL'] . "\n" . htmlentities($picture), 5);
		error_image($L['ERR.IMG_TOO_SMALL'] . "\n" . $picture);
		exit;
	}
	debug($L['ERR.PIC_OK'] .' ['. strlen($picture) . ' Bytes]', 5);
	return $picture;
}

function stream() {
	#global $plugin_cfg, $curl, $lbpplugindir, $L, $cam;
	debug('Looping the picture as mjpeg_stream.', 7);
	$boundary = 'mjpeg_stream';
	header('Cache-Control: no-cache');
	header('Cache-Control: private');
	header('Pragma: no-cache');
	header("Content-type: multipart/x-mixed-replace; boundary=$boundary");
	print "--$boundary\n";
	// don't timeout during a long stream
	set_time_limit(0);
	#@apache_setenv('no-gzip', 1);
	@ini_set('zlib.output_compression', 0);
	@ini_set('implicit_flush', 1);
	for ($i = 0; $i < ob_get_level(); $i++)
		ob_end_flush();
	ob_implicit_flush(1);
	debug("Start looping stream now, max $maxloops times",7);
	if (substr($_SERVER['SERVER_SOFTWARE'], 0, 6) == 'Apache') {
		while (true) {
			print "Content-type: image/jpeg\n\n";
			$picture = get_image();
			// Try again if last call failed e.g. device busy
			if (strlen($picture) < 2000) {
				debug('Fail, try again', 7);
				$picture = get_image();
			}
			// Try again if last call failed - but last time we try it...
			if (strlen($picture) < 2000) {
				debug('Fail again, try last time', 7);
				$picture = get_image();
			}
			debug('Send frame to ' . $_SERVER['REMOTE_ADDR'], 7);
			echo $picture;
			print "--$boundary\n";
		}
	} else {
		$maxloops=180;
		while ($maxloops > 0) {
			print "Content-type: image/jpeg\n\n";
			$picture = get_image();
			// Try again if last call failed e.g. device busy
			if (strlen($picture) < 2000) {
				debug('Fail, try again', 7);
				$picture = get_image();
			}
			// Try again if last call failed - but last time we try it...
			if (strlen($picture) < 2000) {
				debug('Fail again, try last time', 7);
				$picture = get_image();
			}
			debug("Send frame $maxloops to " . $_SERVER['REMOTE_ADDR'], 7);
			echo $picture;
			print "--$boundary\n";
			$maxloops = $maxloops - 1;
		}
	}
	debug("stream mode reached max loop count " . $maxloops . ' - exiting.', 7);
}

function main() {
	global $plugin_cfg, $curl, $lbpplugindir, $L, $cam, $plugindata;
	debug("Function 'main' reached", 7);
	$picture = get_image();
	if ($plugin_cfg["WATERMARK" . $cam] == 1) {
		$watermarkfile = LBPHTMLDIR . '/watermark.png';
		debug('WATERMARK == 1: Using ' . $watermarkfile, 7);
		if (!($watermarked_picture = imagecreatefromstring($picture))) {
			error_image($L['ERR.WATERMARK_UNDERLAY']);
			exit;
		}
		list($ix, $iy, $type, $attr) = getimagesizefromstring($picture);
		if ($type <> 2) {
			error_image($L['ERR.WATERMARK_IMGTYPE']);
			exit;
		}
		if (!($stamp = imagecreatefrompng($watermarkfile))) {
			error_image($L['ERR.WATERMARK_OVERLAY']);
			exit;
		}
		$sx = imagesx($stamp);
		$sy = imagesy($stamp);
		debug('Target image width/height: ' . $sx . '/' . $sy, 7);
		$logo_width = 120;
		$logo_height = 86;
		debug('Logo width/height: ' . $logo_width . '/' . $logo_height, 7);
		$margin_right = $ix - $logo_width - 20;
		$margin_bottom = 20;
		debug('Margin: ' . $margin_right . '/' . $margin_bottom, 7);
		if (!ImageCopyResized($watermarked_picture, $stamp,
			$ix - $logo_width - $margin_right,
			$iy - $logo_height - $margin_bottom,
			0, 0, $logo_width, $logo_height, $sx, $sy))
		{
			error_image($L['ERR.WATERMARK_LAYERS']);
			exit;
		}
		ImageDestroy($stamp);
		ob_start();
		if (!ImageJPEG($watermarked_picture)) {
			error_image($L['ERR.BUILD_JPEG']);
			exit;
		}
		$picture = ob_get_contents();
		if ($plugindata['PLUGINDB_LOGLEVEL'] == 7) {
			if (!isset($_GET['stream'])) {
//debug("<img src='data:image/jpeg;base64,".base64_encode($picture)."' />",7);
//debug("<img src='data:image/jpeg;base64,".base64_encode($picture)."' />",7,1);
			} else {
				debug("Converted picture:\n[not shown in stream mode]", 7);
			}
		}
		ob_end_clean();
		ImageDestroy($watermarked_picture);
	} else {
		debug('WATERMARK == 0 => no LoxBerry logo', 7);
	}
	debug('Reading IMG_WIDTH value from config file', 7);
	$width = isset($plugin_cfg['IMG_WIDTH' . $cam])
		? intval($plugin_cfg['IMG_WIDTH' . $cam])
		: 0;
	if ($width <> 0) {
		debug('Resize image: ' . $width, 7);
		if ($width >= 200 && $width <= 1920) {
			debug('IMG_WIDTH ok');
			debug("Resizing picture to " . $width, 7);
			if (!$resized_picture = resize_cam_image($picture, $width)) {
				error_image($L['ERR.RESIZE']);
				exit;
			}
		} else {
			debug('IMG_WIDTH is not >= 200 and <= 1920.', 7);
			debug('No resizing here, keep picture as it is.', 7);
			$resized_picture = $picture;
		}
	} else {
		debug('No resizing wanted in config. Keep picture size.', 7);
		$resized_picture = $picture;
	}
	return [$picture, $resized_picture];
}

if (isset($_GET['stream'])) {
	stream();
	exit;
}
list($picture, $resized_picture) = main();


// Output to browser
debug('Streaming mode is not wanted, so continue normally.', 7);
if (!isset($plugin_cfg['IMG_WIDTH' . $cam])
	|| $plugin_cfg['IMG_WIDTH' . $cam] == 0)
{
	debug($L['ERR.NO_PIC_WANTED'], 5);
	ob_end_clean();
	header('Connection: close');
	ignore_user_abort(true); // just to be safe
	ob_start();
	echo $L['CC.NO_IMG_MSG'];
	$size = ob_get_length();
	header("Content-Length: $size");
	ob_end_flush(); // Strange behaviour, will not work
	flush(); // Unless both are called !
	// Do processing here
} else {
	debug($L['ERR.PIC_WANTED'], 5);
	header ('Content-type: image/jpeg');
	header ('Cache-Control: no-cache, no-store, must-revalidate');
	header ('Pragma: no-cache');
	header ('Expires: ' . gmdate('D, d M Y H:i:s', time() - 3600) . ' GMT');
	header ('Content-Disposition: inline; filename="'
		. $plugin_cfg['EMAIL_FILENAME'] . "_"
		. $datetime->format("Y-m-d_i\hh\mH\s") . '.jpg"');
	debug('Picture wanted, display it now.', 7);
	if ( $plugindata['PLUGINDB_LOGLEVEL'] == 7 ) {
		$finfo = new finfo(FILEINFO_MIME);
		$type = explode(';', $finfo->buffer($resized_picture), 2)[0];
		debug('Type: ' . $type
			. ' Size: ' . strlen($resized_picture) . ' Bytes', 7);
		if (!isset($_GET['stream'])) {
//debug("<img src='data:".$type.";base64,".base64_encode($resized_picture)." />",7);
//debug("<img src='data:".$type.";base64,".base64_encode($resized_picture)."' />",7,1);
		} else {
			debug("Picture:\n[not shown in stream mode]",7);
		}
	}
	ob_end_clean();
	ignore_user_abort(true);
	header('Connection: close');
	ob_start();
	echo $resized_picture;
	$size = ob_get_length();
	header("Content-Length: $size");
	ob_end_flush();
	flush();
}

debug('############# Normal mode done ######################', 7);

debug('############# eMail Part reached ####################', 7);

debug('Check if sending eMail is enabled', 7);
if ($plugin_cfg['MAIL' . $cam] == 1 && $mail_cfg['SMTP']['ISCONFIGURED'] == 1) {
	debug($L['ERR.SEND_EMAIL'], 5);
	$sent = send_mail_pic($picture);
} else {
	debug("MAIL=0 or SMTP server not set", 7);
	if (isset($plugin_cfg['MAIL' . $cam]))
		debug("MAIL=" . $plugin_cfg['MAIL'. $cam], 7);
	if (isset($mail_cfg['SMTP']['ISCONFIGURED']))
		debug('SMTP.ISCONFIGURED=' . $mail_cfg['SMTP']['ISCONFIGURED'], 7);
}


debug($L['ERR.EXIT_PLUGIN'] . "\n"
	. '+ + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + '
	. '+ + + + + + + + + + + + + + + + + + + + +', 5);
exit;

function error_image ($error_msg) {
	global $L, $plugin_cfg, $plugindata;
	if (strlen($error_msg) == 0) {
		$error_msg=$L['ERR.UNKNOWN'];
	}
	debug(explode("\n", $error_msg)[0], 3);
	debug($error_msg, 7);
	// Display an Error-Picture
	$error_image = @ImageCreate(640, 480) or die ($error_msg);
	$background_color = ImageColorAllocate($error_image, 0, 0, 0);
	$text_color = ImageColorAllocate($error_image, 255, 0, 0);
	$line_height = 20;
	$line_pos = 50;
	$line_nb = '';
	foreach (explode("\n", $error_msg) as $err_line) {
		if ($err_line != '') {
			$err_line = str_ireplace(array("\r\n", "\r", "\n",
				'\r\n', '\r', '\n'), '', $err_line);
			$line_pos = $line_pos + $line_height;
			ImageString($error_image, 20, 10, $line_pos, $line_nb . $err_line,
				$text_color);
			if ($line_nb == '')
				$text_color = ImageColorAllocate($error_image, 128,128,128);
			$line_nb++;
		}
	}
	header('Content-type: image/jpeg');
	header('Cache-Control: no-cache, no-store, must-revalidate');
	header('Pragma: no-cache');
	header('Expires: 0');
	ImageJPEG($error_image);
	if ($plugindata['PLUGINDB_LOGLEVEL'] == 7) {
		$finfo = new finfo(FILEINFO_MIME);
		$type = explode(';', $finfo->buffer(ImageJPEG ($error_image)), 2)[0];
		debug('Type: ' . $type
			. ' Size: ' . strlen(ImageJPEG ($error_image)) . ' Bytes', 7);
		if (!isset($_GET['stream'])) {
//debug("<img src='data:".$type.";base64,".base64_encode(ImageJPEG($error_image))."'></>",7);
//debug("<img src='data:".$type.";base64,".base64_encode(ImageJPEG($error_image))."'></>",7,1);
		} else {
			debug("Picture:\n[not shown in stream mode]", 7);
		}
	}
	ImageDestroy($error_image);
	debug('error_image() done - exiting.', 7);
	exit;
}

function send_mail_pic($picture) {
	debug('send_mail_pic()',7);
	global $datetime, $plugin_cfg, $cam_name, $mail_cfg, $L, $cam, $plugindata;

	// Prevent sending eMails as long as stream is read from Miniserver
	// 10 s delay minimum
	$lockfilename = '/tmp/' . LBPPLUGINDIR . $cam;
	debug("Check if lockfile $lockfilename for cam $cam exists", 7);

	if (file_exists($lockfilename)) {
		debug("The file $lockfilename exists.", 7);
		if (filectime($lockfilename)) {
			if (($datetime->getTimestamp() - filectime($lockfilename)) > 10) {
				debug("Lockfile $lockfilename was changed "
					. ($datetime->getTimestamp() - filectime($lockfilename))
					. ' seconds ago. Too old, delete it and send eMail.', 7);
				unlink ($lockfilename)
					or debug($L['ERR.DELETE_LOCK'] . ' ' . $lockfilename, 3);
			} else {
				debug("Lockfile $lockfilename was changed "
					. ($datetime->getTimestamp() - filectime($lockfilename))
					. ' seconds ago. Not old enough, keeping it, refresh it,'
					. ' and send no eMail.', 7);
				$handle = fopen($lockfilename, 'w')
					or debug($L['ERR.OPEN_LOCK'] . ' ' . $lockfilename, 3);
				fwrite($handle, $datetime->getTimestamp())
					or debug($L['ERR.WRITE_LOCK'] . ' ' . $lockfilename, 3);
				exit;
			}
		}
	} else {
		debug("The file $lockfilename doesn't exists, create it.", 7);
		$handle = fopen($lockfilename, 'w')
			or debug($L['ERR.OPEN_LOCK'] . ' ' . $lockfilename, 3);
		fwrite($handle, $datetime->getTimestamp())
			or debug($L['ERR.WRITE_LOCK'] . ' ' . $lockfilename, 3);
		fclose($handle);
	}

	if (!isset($mail_cfg['SMTP']['EMAIL'])) {
		debug($L['ERR.NO_SENDER'], 3);
		return 'Plugin-Error: [No Sender eMail address found]';
	}

	$mailFrom =	trim(str_ireplace('"', '', $mail_cfg['SMTP']['EMAIL']));
	debug("Config value ['SMTP']['EMAIL'] found - using it: ".$mailFrom, 7);
	if (isset($plugin_cfg['MAIL_FROM' . $cam])) {
		$mailFromName = $plugin_cfg['MAIL_FROM' . $cam];
		debug('MAIL_FROM=' . $mailFromName, 7);
	} else {
		$mailFromName = '"LoxBerry"';
		debug('MAIL_FROM default=' . $mailFromName, 7);
	}
	debug('recipients: ' . $plugin_cfg['RECIPIENTS' . $cam], 7);
	$mailTo = '';
	foreach (explode(',', $plugin_cfg['RECIPIENTS' . $cam]) as $recipients_data)
	{
		debug('Recipient(s): ' . $recipients_data, 7);
		$recipients_data = trim(str_ireplace('"', '', $recipients_data));
		if (filter_var($recipients_data, FILTER_VALIDATE_EMAIL)) {
			$mailTo .= $recipients_data . ',';
			$at_least_one_valid_email = 1;
			debug('Validated recipient(s): ' . $recipients_data, 7);
		} else {
			debug($L['ERR.INVALID_RECIPIENTS'], 3);
			debug('Abort recipients manipulation.', 7);
		}
	}
	$emailSubject = utf8_decode($cam_name . $plugin_cfg['MAIL_SUBJECTA' . $cam]
		. ' ' . $datetime->format($plugin_cfg['MAIL_DATE' . $cam])
		. ' ' . $plugin_cfg['MAIL_SUBJECTB' . $cam]
		. ' ' . $datetime->format($plugin_cfg['MAIL_TIME' . $cam])
		. ' ' . $plugin_cfg['MAIL_SUBJECTC' . $cam]);
	debug('Building eMail subject: ' . $emailSubject, 7);

	if (isset($plugin_cfg['MAIL_PICS' . $cam])) {
		$pics = substr($plugin_cfg['MAIL_PICS' . $cam], 0, 1);
		$delay = substr($plugin_cfg['MAIL_PICS' . $cam], 1, 1);
		debug("Send $pics picture(s) with $delay s delay.", 7);
	} else {
		debug('MAIL_PICS unset: Sending 1 picture.', 7);
	}

	$outer_boundary = md5('o' . $cam.time());
	$inner_boundary = md5('i' . $cam.time());
	$htmlpic = '';
	$mailTo = substr($mailTo, 0, -1);

	debug($L['ERR.SEND_MAIL']
		. ' From: ' . $mailFromName.htmlentities(' <' . $mailFrom . '> ')
		. ' To: ' . $mailTo, 5);
	$html = 'From: ' . $mailFromName . ' <' . $mailFrom. '>
To: ' . $mailTo . '
Subject: ' . utf8_encode($emailSubject) . '
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="------------' . $outer_boundary . '"

This is a multi-part message in MIME format.
--------------' . $outer_boundary . '
Content-Type: text/plain; charset=utf-8; format=flowed
Content-Transfer-Encoding: 8bit

' . strip_tags($plugin_cfg['MAIL_BODY' . $cam]) . "
\n--\n" . strip_tags($plugin_cfg['MAIL_SIG' . $cam]) . '

--------------' . $outer_boundary . '
Content-Type: multipart/related;
 boundary="------------' . $inner_boundary . '"


--------------' . $inner_boundary . '
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: 8bit

<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
  </head>
  <body style"color: #000000; background-color: #FFFFFF">

  ' . $plugin_cfg['MAIL_BODY' . $cam] . '<br>';

	$htmlpicdata = '';
	for ($i = 1; $i <= $pics; $i++) {
		debug("Add picture $i of $pics.", 7);
		if ($i > 1) {
			debug("Wait $delay seconds before getting next picture.", 7);
			sleep($delay);
			list($picture , $resized_picture ) = main();
		}
		if ($plugin_cfg['MAIL_IMG_INLINE' . $cam] == 1) {
			debug('Place image inline', 7);
			$inline = 'inline';
			$email_image_part = "\n<img src=\"cid:"
				. $plugin_cfg['EMAIL_FILENAME'] . '_'
				. $datetime->format('Y-m-d_i\hh\mH\s') . '_' . $i . '" alt="'
				. $plugin_cfg['EMAIL_FILENAME'] . '_'
				. $datetime->format('Y-m-d_i\hh\mH\s') . '_' . $i
				. ".jpg\" />\n<br>";
			} else {
				debug('Place image as attachment', 7);
				$inline = 'attachment';
				$email_image_part = "\n";
			}

			debug("Boundary for picture $i of $pics is: " . $outer_boundary, 7);
			$width = intval($plugin_cfg['MAIL_IMG_WIDTH' . $cam]);
			debug('Check if resize value is valid.', 7);
			if ($width >= 240) {
				debug('Minimum width >= 240 : yes => ' . $width, 7);
				if ($width > 1920) {
					debug('width > 1920, adjusting '. $width .' to 1920', 7);
					$width = 1920;
				}
				debug('Resizing to: ' . $width, 7);
				$picture = resize_cam_image($picture, $width);
			} else {
				debug('width < 240, keeping ' . $width, 7);
			}
			$htmlpic .= $email_image_part;
			$htmlpicdata .= '--------------' . $inner_boundary . '
Content-Type: image/jpeg; name="' . $plugin_cfg['EMAIL_FILENAME'] . '_'
				. $datetime->format('Y-m-d_i\hh\mH\s') . '_' . $i . '.jpg"
Content-Transfer-Encoding: base64
Content-ID: <' . $plugin_cfg['EMAIL_FILENAME'] . '_'
				. $datetime->format('Y-m-d_i\hh\mH\s') . '_' . $i . '>
Content-Disposition: ' . $inline . '; filename="'
				. $plugin_cfg['EMAIL_FILENAME'] . '_'
				. $datetime->format('Y-m-d_i\hh\mH\s') . '_' . $i . '.jpg"

' . chunk_split(base64_encode($picture)) . "\n";

	}

	$html .= $htmlpic . " \n--<br>"
		. $plugin_cfg['MAIL_SIG' . $cam] . "</body></html>\n\n"
		. $htmlpicdata
		. '--------------' . $inner_boundary . "--\n\n"
		. '--------------' . $outer_boundary . "--\n\n";

	debug('eMail-Body will be:', 7);
	debug($html, 7, 1);
	$tmpfname = tempnam('/tmp', LBPPLUGINDIR . '_');
	debug("Write eMail tempfile  $tmpfname", 7);
	$handle = fopen($tmpfname, 'w')
		or debug($L['ERR.OPEN_TMPFILE'] . ' ' . $tmpfname, 3);
	fwrite($handle, $html)
		or debug($L['ERR.WRITE_TMPFILE'] . ' ' . $tmpfname, 3);
	fclose($handle);
	debug("Sending eMail from tempfile $tmpfname", 7);
	exec("/usr/sbin/sendmail -t 2>&1 < $tmpfname", $last_line, $retval);
	debug("Delete tempfile $tmpfname", 7);
	unlink($tmpfname)
		or debug($L['ERR.DELETE_TMPFILE'] . ' ' . $tmpfname, 3);
	debug('Sendmail Ausgabe: ' . join("\n", $last_line), 7);
	if ($retval) {
		debug($L['ERR.MAIL_FAIL'] . 'Code: ' . $retval, 3);
		return 'Plugin-Error: [' . $last_line . ']';
	}
	debug('Send eMail ok.', 7);
	return 'Mail ok.';
}

function resize_cam_image ($picture, $width=720) {
	debug('resize_cam_image()', 7);
    list($w, $h) = getimagesizefromstring($picture);
    $height = $h / ($w / $width);
    $thumb = imagecreatetruecolor($width, $height);
    $source = imagecreatefromstring($picture);
    imagecopyresampled($thumb, $source, 0, 0, 0, 0, $width, $height, $w, $h);
    ob_start();
    ImageJPEG($thumb);
    $picture = ob_get_contents();
    ob_end_clean();
    ImageDestroy($thumb);
    ImageDestroy($source);
    return $picture;
}
