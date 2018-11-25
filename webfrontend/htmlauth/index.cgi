#!/usr/bin/perl

# This file is based on the Apache 2.0 licensed version of the project
# https://raw.githubusercontent.com/Woersty/LoxBerry-Plugin-cam-connect/
# file v2018.10.28/webfrontend/htmlauth/index.cgi
# Copyright 2018 Wörsty (git@loxberry.woerstenfeld.de)
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

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use MIME::Base64;
use List::MoreUtils 'true','minmax';
use HTML::Entities;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw/:standard/;
use Config::Simple '-strict';
use JSON;
use warnings;
use strict;
no  strict 'refs';
#use diagnostics;

# Variables
my $maintemplatefile = 'config.html';
my $errortemplatefile = 'error.html';
my $successtemplatefile = 'success.html';
my $helptemplatefile = 'help.html';
my $pluginconfigfile = $lbpplugindir . '.cfg';
my $languagefile = 'language.ini';
my $logfile = $lbpplugindir . '.log';
my $template_title;
my $no_error_template_message = '<b>Snap-Cam:</b> The error template is not readable. We must abort here. Please try to reinstall the plugin.';
my $version = LoxBerry::System::pluginversion();
my $helpurl = 'http://www.loxwiki.eu/display/LOXBERRY/Cam-Connect';
my @cfg_vars = ('NAME', 'NOTE', 'ADDR', 'PORT', 'MODEL',
	'USERNAME', 'PW', 'IMG_WIDTH', 'WATERMARK', 'MAIL', 'RECIPIENTS',
	'MAIL_FROM', 'MAIL_SUBJECTA', 'MAIL_DATE', 'MAIL_SUBJECTB', 'MAIL_TIME',
	'MAIL_SUBJECTC', 'MAIL_BODY', 'MAIL_SIG', 'MAIL_IMG_WIDTH',
	'MAIL_IMG_INLINE', 'MAIL_PICS');
my $cam_model_list				= '';
my @lines						= [];
my $log 						= LoxBerry::Log->new(
	name => 'SnapCam',
	filename => $lbplogdir ."/". $logfile,
	append => 1
);
my $plugin_cfg = $lbpconfigdir . '/' . $pluginconfigfile;
LOGDEB "Loading '$plugin_cfg' ...\n";
$plugin_cfg = new Config::Simple($plugin_cfg);
my %Config = $plugin_cfg->vars() if ($plugin_cfg);
our $error_message = '';

# Logging
my $plugin = LoxBerry::System::plugindata();

if ($plugin->{PLUGINDB_LOGLEVEL} eq 7) {
	LOGSTART 'New admin call.';
	$LoxBerry::System::DEBUG = 1;
	$LoxBerry::Web::DEBUG = 1;
}
$log->loglevel($plugin->{PLUGINDB_LOGLEVEL});

LOGDEB 'Init CGI and import names in namespace R::';
my $cgi = CGI->new;
$cgi->import_names('R');
if ($LoxBerry::Web::DEBUG || 1) {
	use Data::Dumper;
	my %hash = $cgi->Vars(',');
	LOGDEB Dumper(\%hash);
}

if ($R::delete_log) {
	LOGWARN 'Delete Logfile: ' . $logfile;
	LOGDEB 'Debug = ' . $R::delete_log;
	my $logfile = $log->close;
	system("/bin/date > $logfile");
	$log->open;
	print "Content-Type: text/plain\n\nOK";
	LOGSTART 'Logfile restarted - exiting';
	exit;
}

my $lang = lblanguage();
LOGDEB 'Using language: ' . $lang;

$main::htmlhead = '<link rel="stylesheet" href="index.css" />';


stat($lbptemplatedir . '/' . $errortemplatefile);
if (! -r _) {
	$error_message = $no_error_template_message;
	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefile);
	print $error_message;
	LOGCRIT $error_message;
	LoxBerry::Web::lbfooter();
	LOGCRIT 'Exiting due to an unrecoverable error';
	exit;
}
my $errortemplate = HTML::Template->new(
	filename => $lbptemplatedir . "/" . $errortemplatefile,
	global_vars => 1,
	loop_context_vars => 1,
	die_on_bad_params=> 0,
	associate => $cgi,
	%htmltemplate_options,
	#debug => 1,
);
LOGDEB 'Read error strings from ' . $languagefile . ' for language ' . $lang;
my %ERR = LoxBerry::System::readlanguage($errortemplate, $languagefile);


stat($lbptemplatedir . '/' . $successtemplatefile);
if (! -r _) {
	$error_message = $ERR{'ERR.SUCCESS_TEMPLATE'};
	&error;
}
my $successtemplate = HTML::Template->new(
	filename => $lbptemplatedir . '/' . $successtemplatefile,
	global_vars => 1,
	loop_context_vars => 1,
	die_on_bad_params=> 0,
	associate => $cgi,
	%htmltemplate_options,
	#debug => 1,
);
LOGDEB 'Read success strings from ' . $languagefile . ' for language ' . $lang;
my %SUC = LoxBerry::System::readlanguage($successtemplate, $languagefile);


stat($lbptemplatedir . '/' . $maintemplatefile);
if (! -r _) {
	$error_message = $ERR{'ERR.MAIN_TEMPLATE'};
	&error;
}
my $maintemplate = HTML::Template->new(
	filename => $lbptemplatedir . "/" . $maintemplatefile,
	global_vars => 1,
	loop_context_vars => 1,
	die_on_bad_params=> 0,
	%htmltemplate_options,
	#debug => 1
);
LOGDEB 'Read main strings from ' . $languagefile . ' for language ' . $lang;
my %L = LoxBerry::System::readlanguage($maintemplate, $languagefile);


my $cfg_file = $lbpconfigdir . '/' . $pluginconfigfile;
if (! -r $cfg_file) {
	LOGWARN 'Plugin config file not readable: ' . $cfg_file;
	$error_message = $ERR{'ERR.CREATE_DIR'};
	mkdir $lbpconfigdir unless -d $lbpconfigdir or &error;
	$error_message = $ERR{'ERR.CREATE_FILE'};
	open my $cfg, '>', $cfg_file or &error;
	close $cfg;
	LOGWARN 'Default config created. Reporting an error to force a page reload';
	$error_message = $ERR{'ERR.NO_CONFIG'};
	&error;
}

$maintemplate->param('LBPPLUGINDIR', $lbpplugindir);

if ($R::saveformdata) {
	LOGDEB 'Processing save call' . $R::saveformdata;

	my @matches = grep { /ADDR[0-9]*/ } %R::;
	s/ADDR// for @matches ;

	foreach my $camID (@matches) {
		LOGDEB "Saving camera $camID";
		foreach my $vname (@cfg_vars) {
			while (my ($key, $value) = each %R::) {
				if ($key eq $vname . $camID){
					if (defined ${$value} && ${$value} ne '') {
						LOGDEB $key . '=' . "'${$value}'";
						$plugin_cfg->param($key, ${$value});
					} else {
						LOGDEB $key . ' is  missing or empty.';
					}
				}
			}
		}
	}
	$plugin_cfg->param('VERSION', $version);
	$error_message = $ERR{'ERR.SAVE_CONFIG'};
	$plugin_cfg->save() or &error;

	LOGDEB 'Set page title, load header, parse variables, set footer, end';
	$template_title = $SUC{'SAVE.MY_NAME'};
	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefile);
	$successtemplate->param('SAVE_ALL_OK', $SUC{'SAVE.SAVE_ALL_OK'});
	$successtemplate->param('SAVE_MESSAGE', $SUC{'SAVE.SAVE_MESSAGE'});
	$successtemplate->param('SAVE_BUTTON_OK', $SUC{'SAVE.SAVE_BUTTON_OK'});
	$successtemplate->param('SAVE_NEXTURL', $ENV{REQUEST_URI});
	print $successtemplate->output();
	LoxBerry::Web::lbfooter();
	LOGDEB 'Config saved - exiting.';
	exit;
}

LOGDEB 'Preparing default page';
&defaultpage;

#####################################################
# Subs
#####################################################
sub defaultpage {
	LOGDEB 'Prepare Cam list';
	$cam_model_list='';
	open(F, "$lbpdatadir/camera_models.dat") || die 'Missing camera list.';
	flock(F,2);
	@lines = <F>;
	flock(F,8);
	close(F);
	foreach (@lines) {
		s/[\n\r]//g;
		our @cams = split /\|/, $_;
		$cam_model_list .=
			"<option value='$cams[0]'>$cams[1] $cams[2]</option>\n";
		LOGDEB 'Adding cam model: #' . $cams[0] . ' ' . $cams[1]
			. ' (' . $cams[2] . ')';
	}
	$template_title = $L{'CC.MY_NAME'};
	$maintemplate->param('LOGO_ICON', get_plugin_icon(64));
	$maintemplate->param('HTTP_HOST', $ENV{HTTP_HOST});
	$maintemplate->param('HTTP_PATH', '/plugins/' . $lbpplugindir);
	$maintemplate->param('cam_model_list', $cam_model_list);
	$maintemplate->param('VERSION', $version);
	$maintemplate->param('LOGLEVEL',
		$L{'CC.LOGLEVEL' . $plugin->{PLUGINDB_LOGLEVEL}});
	# Workaround due to missing var for Logview
	$lbplogdir =~ s/$lbhomedir\/log\///;
	$maintemplate->param('LOGFILE', $lbplogdir . '/' . $logfile);
	LOGDEB 'Check for pending notifications: '
		. $lbpplugindir . ' ' . $L{'CC.MY_NAME'};
	my $notifications =
		LoxBerry::Log::get_notifications_html($lbpplugindir, $L{'CC.MY_NAME'});
	LOGDEB 'No notifications pending.' if !$notifications;
	$maintemplate->param('NOTIFICATIONS', $notifications);

	my @camdata = ();
	my @known_cams = ();
	foreach (keys %Config) {
		next unless /ADDR[0-9]*/;
		s/default.ADDR//;
		push @known_cams, $_;
	}
	@known_cams = sort @known_cams;
	LOGDEB 'Found following cameras in config: ' . join(',', @known_cams);
	my ($fid, $lid) = minmax @known_cams;

	if ($R::create_cam) {
		$lid++;
		LOGDEB 'Creating new camera ' . $lid . ' ' . $R::create_cam;
		$error_message = $ERR{'ERR.CREATE_FILE'};
		open my $cfg, '>>', $lbpconfigdir . '/' . $pluginconfigfile or &error;
		print $cfg 'IMG_WIDTH' . $lid . '=9999' . "\n";
		print $cfg 'MAIL_IMG_WIDTH' . $lid . '=9999' . "\n";
		print $cfg 'ADDR' . $lid . "=''\n";
		print $cfg 'PORT' . $lid . '="' . $L{'CC.PORT_EX'} . "\"\n";
		print $cfg 'MAIL_FROM' . $lid . '="' . $L{'CC.MAIL_FROM_EX'} . "\"\n";
		print $cfg 'USERNAME' . $lid . "=''\n";
		print $cfg 'PW' . $lid . "=''\n";
		print $cfg 'NAME' . $lid . "=''\n";
		print $cfg 'MAIL_IMG_INLINE' . $lid . "=0\n";
		print $cfg 'MAIL_PICS' . $lid . "=10\n";
		print $cfg 'WATERMARK' . $lid . "=0\n";
		print $cfg 'MAIL' . $lid . "=0\n";
		print $cfg 'NOTE' . $lid . "=''\n";
		print $cfg 'RECIPIENTS' . $lid . "=''\n";
		print $cfg 'MODEL' . $lid . "=1\n";
		close $cfg;
		LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefile);
		print "OK\n";
		LOGDEB 'Create cam page done - exiting.';
		exit;
	}

	if ($R::delete_cam) {
		LOGDEB 'Deleting camera ' . $R::delete_cam;
		$error_message = $ERR{'ERR.CREATE_FILE'};
		use Tie::File;

		LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefile);
		print "Content-Type: text/plain\n\n";
		my $rm_var = '';
		foreach my $vname (@cfg_vars) {
			my $rm_var = $vname . $R::delete_cam . '=';
			LOGDEB 'Deleting var ' . $rm_var;
			tie my @file_lines,
				'Tie::File', $lbpconfigdir . '/' . $pluginconfigfile or die;
			@file_lines = grep !/^$rm_var/, @file_lines;
			untie @file_lines or die "$!";
		}
		print "OK\n";
		LOGDEB 'Delete cam page done - exiting.';
		exit;
	}

	my $cam_list = '<option value="">'.$L{'CC.CAM_SELECT_OPTION'}.'</option>';

	my %js_globals = (
		CC__MY_NAME => $template_title,
		HTTP_PATH => $maintemplate->param('HTTP_PATH'),
		LBPPLUGINDIR => $lbpplugindir,
		CAMS => \@known_cams,
	);

	foreach my $camno (@known_cams) {
		my %cam;

		my @fill_suggestions = ('MAIL_SUBJECTA', 'MAIL_DATE', 'MAIL_SUBJECTB',
			'MAIL_TIME', 'MAIL_SUBJECTC', 'MAIL_BODY', 'MAIL_SIG');
		foreach my $suggestion_field (@fill_suggestions) {
			if (!defined $plugin_cfg->param( $suggestion_field . $camno)) {
				LOGDEB "Suggested CAM config var '" . $suggestion_field . "'='"
					. $L{'CC.' . $suggestion_field . '_EX'} . "'";
				$cam{$suggestion_field}	=
					uri_unescape($L{'CC.' . $suggestion_field . '_EX'});
			} else {
				LOGDEB "CAM config var '" . $suggestion_field . $camno . "'='"
					. $plugin_cfg->param($suggestion_field . $camno) . "'";
				$cam{$suggestion_field}	=
					uri_unescape($plugin_cfg->param($suggestion_field .$camno));
			}
		}
		$cam{CAMNO} = $camno;
		$cam{ADDR} = $plugin_cfg->param('ADDR'.$camno);
		$cam{PORT} = $plugin_cfg->param('PORT'.$camno);
		$cam{MODEL} = $plugin_cfg->param('MODEL'.$camno);
		$cam{USERNAME} = uri_unescape($plugin_cfg->param('USERNAME'.$camno));
		$cam{PW} = uri_unescape($plugin_cfg->param('PW'.$camno));
		$cam{NOTE} = uri_unescape($plugin_cfg->param('NOTE'.$camno));
		$cam{RECIPIENTS} =uri_unescape($plugin_cfg->param('RECIPIENTS'.$camno));
		$cam{NAME} = uri_unescape($plugin_cfg->param('NAME'.$camno));
		$cam{MAIL_FROM} = uri_unescape($plugin_cfg->param('MAIL_FROM'.$camno));
		$cam{IMG_WIDTH} = $plugin_cfg->param('IMG_WIDTH'.$camno);
		$cam{MAIL_IMG_WIDTH} = $plugin_cfg->param('MAIL_IMG_WIDTH'.$camno);
		$cam{MAIL_PICS} = $plugin_cfg->param('MAIL_PICS'.$camno);
		foreach my $cam_parameter_to_process ('WATERMARK', 'MAIL',
			'MAIL_IMG_INLINE')
		{
			my $val, my $checked;
			my $param = $cam_parameter_to_process . $camno;
			if ($plugin_cfg->param($param)
				&& int($plugin_cfg->param($param)) eq 1)
			{
				$val = 1;
			    $checked = 'checked';
			} else {
				$val = 0;
			    $checked = '';
			}
			$cam{$cam_parameter_to_process} = $val;
		    $cam{$cam_parameter_to_process . "_VAL"} = $checked;
			LOGDEB "CAM special config var '" . $param . "'='" . $val . "'";
		}
		$cam_list .= '<option value="#camdiv' . $camno . '">#'
			. $camno . ' - ' . $cam{NAME} . '</option>';
		# select boxes
		foreach my $id ('MODEL', 'IMG_WIDTH', 'MAIL_IMG_WIDTH', 'MAIL_PICS') {
			$js_globals{$id . $camno} = $plugin_cfg->param($id . $camno);
		}
		push(@camdata, \%cam);
	}
	$maintemplate->param('CAMDATA' => \@camdata);
	$maintemplate->param('KNOWN_CAMS' => join(',', @known_cams));
	$maintemplate->param('CAM_LIST' => $cam_list);

	# all index.js required mappings
	my $txt = JSON->new->utf8->space_after->pretty->encode(\%js_globals);

	$main::htmlhead .= '<script src="index.js"></script>
<script>var js_globals = ' . $txt  . ';</script>
';

	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefile);
	print $maintemplate->output();
	LoxBerry::Web::lbfooter();
	LOGDEB 'Default page done - exiting.';
	exit;
}

sub error {
	LOGERR $error_message;
	$template_title = $ERR{'ERR.MY_NAME'} . ' - ' . $ERR{'ERR.TITLE'};
	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefile);
	$errortemplate->param('ERR_MESSAGE' , $error_message);
	$errortemplate->param('ERR_TITLE' , $ERR{'ERR.TITLE'});
	$errortemplate->param('ERR_BACK' , $ERR{'ERR.BACK'});
	print $errortemplate->output();
	LoxBerry::Web::lbfooter();
	LOGDEB 'Error page done - exiting.';
	exit;
}
