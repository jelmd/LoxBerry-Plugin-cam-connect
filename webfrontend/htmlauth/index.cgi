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
no  strict "refs";
#use diagnostics;

# Variables
my $maintemplatefilename 		= "cam_connect.html";
my $errortemplatefilename 		= "error.html";
my $successtemplatefilename 	= "success.html";
my $helptemplatefilename		= "help.html";
my $pluginconfigfile 			= "cam-connect.cfg";
my $languagefile 				= "language.ini";
my $logfile 					= "cam_connect.log";
my $template_title;
my $no_error_template_message	= "<b>Cam-Connect:</b> The error template is not readable. We must abort here. Please try to reinstall the plugin.";
my $version 					= LoxBerry::System::pluginversion();
my $helpurl 					= "http://www.loxwiki.eu/display/LOXBERRY/Cam-Connect";
my @pluginconfig_strings 		= ('EMAIL_FILENAME');
my @pluginconfig_cameras 		= (
	"CAM_HOST_OR_IP", "CAM_PORT", "CAM_MODEL", "CAM_USER", "CAM_PASS", "CAM_NOTE",
	"CAM_RECIPIENTS", "CAM_NAME", "WATERMARK", "CAM_IMAGE_RESIZE",
	"CAM_EMAIL_FROM_NAME", "CAM_EMAIL_SUBJECT1", "CAM_EMAIL_DATE_FORMAT",
	"CAM_EMAIL_SUBJECT2", "CAM_EMAIL_TIME_FORMAT",
	"CAM_EMAIL_SUBJECT3", "CAM_EMAIL_BODY", "CAM_EMAIL_SIGNATURE",
	"CAM_EMAIL_RESIZE", "CAM_NO_EMAIL_CB",
	"CAM_EMAIL_USED_CB", "CAM_EMAIL_MULTIPICS", "CAM_EMAIL_INLINE_CB");
my $cam_model_list				= "";
my @lines						= [];
my $log 						= LoxBerry::Log->new (
	name => 'CamConnect', filename => $lbplogdir ."/". $logfile, append => 1
);
my $plugin_cfg = $lbpconfigdir . "/" . $pluginconfigfile;
LOGDEB "Loading '$plugin_cfg' ...\n";
$plugin_cfg 					= new Config::Simple($plugin_cfg);
my %Config 						= $plugin_cfg->vars() if ( $plugin_cfg );

our $error_message				= "";

# Logging
my $plugin = LoxBerry::System::plugindata();

LOGSTART "New admin call."      if $plugin->{PLUGINDB_LOGLEVEL} eq 7;
$LoxBerry::System::DEBUG 	= 1 if $plugin->{PLUGINDB_LOGLEVEL} eq 7;
$LoxBerry::Web::DEBUG 		= 1 if $plugin->{PLUGINDB_LOGLEVEL} eq 7;
$log->loglevel($plugin->{PLUGINDB_LOGLEVEL});

LOGDEB "Init CGI and import names in namespace R::";
my $cgi 	= CGI->new;
$cgi->import_names('R');
if ($LoxBerry::Web::DEBUG) {
	use Data::Dumper;
	my %hash = $cgi->Vars(",");
	LOGDEB Dumper(\%hash);
}
if ( $R::delete_log )
{
	LOGDEB "Oh, it's a log delete call. ".$R::delete_log;
	LOGWARN "Delete Logfile: ".$logfile;
	my $logfile = $log->close;
	system("/bin/date > $logfile");
	$log->open;
	LOGSTART "Logfile restarted.";
	print "Content-Type: text/plain\n\nOK";
	exit;
}
else
{
	LOGDEB "No log delete call. Go ahead";
}

LOGDEB "Get language";
my $lang	= lblanguage();
LOGDEB "Resulting language is: " . $lang;

$main::htmlhead = '<link rel="stylesheet" href="index.css" />';

LOGDEB "Check, if filename for the errortemplate is readable";
stat($lbptemplatedir . "/" . $errortemplatefilename);
if ( !-r _ )
{
	LOGDEB "Filename for the errortemplate is not readable, that's bad";
	$error_message = $no_error_template_message;
	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefilename);
	print $error_message;
	LOGCRIT $error_message;
	LoxBerry::Web::lbfooter();
	LOGCRIT "Leaving Cam-Connect Plugin due to an unrecoverable error";
	exit;
}

LOGDEB "Filename for the errortemplate is ok, preparing template";
my $errortemplate = HTML::Template->new(
		filename => $lbptemplatedir . "/" . $errortemplatefilename,
		global_vars => 1,
		loop_context_vars => 1,
		die_on_bad_params=> 0,
		associate => $cgi,
		%htmltemplate_options,
		debug => 1,
		);
LOGDEB "Read error strings from " . $languagefile . " for language " . $lang;
my %ERR = LoxBerry::System::readlanguage($errortemplate, $languagefile);

LOGDEB "Check, if filename for the successtemplate is readable";
stat($lbptemplatedir . "/" . $successtemplatefilename);
if ( !-r _ )
{
	LOGDEB "Filename for the successtemplate is not readable, that's bad";
	$error_message = $ERR{'ERRORS.ERR_SUCCESS_TEMPLATE_NOT_READABLE'};
	&error;
}
LOGDEB "Filename for the successtemplate is ok, preparing template";
my $successtemplate = HTML::Template->new(
		filename => $lbptemplatedir . "/" . $successtemplatefilename,
		global_vars => 1,
		loop_context_vars => 1,
		die_on_bad_params=> 0,
		associate => $cgi,
		%htmltemplate_options,
		debug => 1,
		);
LOGDEB "Read success strings from " . $languagefile . " for language " . $lang;
my %SUC = LoxBerry::System::readlanguage($successtemplate, $languagefile);

LOGDEB "Check, if filename for the maintemplate is readable, if not raise an error";
$error_message = $ERR{'ERRORS.ERR_MAIN_TEMPLATE_NOT_READABLE'};
stat($lbptemplatedir . "/" . $maintemplatefilename);
&error if !-r _;
LOGDEB "Filename for the maintemplate is ok, preparing template";
my $maintemplate = HTML::Template->new(
		filename => $lbptemplatedir . "/" . $maintemplatefilename,
		global_vars => 1,
		loop_context_vars => 1,
		die_on_bad_params=> 0,
		%htmltemplate_options,
	#	debug => 1
		);
LOGDEB "Read main strings from " . $languagefile . " for language " . $lang;
my %L = LoxBerry::System::readlanguage($maintemplate, $languagefile);

LOGDEB "Check if plugin config file is readable";
if (!-r $lbpconfigdir . "/" . $pluginconfigfile)
{
	LOGWARN "Plugin config file not readable.";
	LOGDEB "Check if config directory exists. If not, try to create it. In case of problems raise an error";
	$error_message = $ERR{'ERRORS.ERR_CREATE_CONFIG_DIRECTORY'};
	mkdir $lbpconfigdir unless -d $lbpconfigdir or &error;
	LOGDEB "Try to create a default config";
	$error_message = $ERR{'ERRORS.ERR_CREATE CONFIG_FILE'};
	open my $configfileHandle, ">", $lbpconfigdir . "/" . $pluginconfigfile or &error;
		print $configfileHandle 'EMAIL_FILENAME="Snapshot"'."\n";
	close $configfileHandle;
	LOGWARN "Default config created. Display error anyway to force a page reload";
	$error_message = $ERR{'ERRORS.ERR_NO_CONFIG_FILE'};
	&error;
}

LOGDEB "Parsing valid config variables into the maintemplate";
foreach my $config_value (@pluginconfig_strings)
{
	${$config_value} = $Config{'default.' . $config_value};
	if (defined ${$config_value} && ${$config_value} ne '')
	{
		LOGDEB "Set config variable: " . $config_value . " to " . ${$config_value};
  		$maintemplate->param($config_value	, ${$config_value} );
	}
	else
	{
		LOGWARN "Config variable: " . $config_value . " missing or empty.";
  		$maintemplate->param($config_value	, "");
	}
}
$maintemplate->param( "LBPPLUGINDIR" , $lbpplugindir);

$R::saveformdata if 0; # Prevent errors
LOGDEB "Is it a save call?";
if ( $R::saveformdata )
{
	LOGDEB "Yes, is it a save call";
	foreach my $parameter_to_write (@pluginconfig_strings)
	{
	    while (my ($config_variable, $value) = each %R::)
	    {
			if ( $config_variable eq $parameter_to_write )
			{
				$plugin_cfg->param($config_variable, ${$value});
				LOGDEB "Setting configuration variable [$config_variable] to value (${$value}) ";
			}
		}
	}

	my @matches = grep { /CAM_HOST_OR_IP[0-9]*/ } %R::;
	s/CAM_HOST_OR_IP// for @matches ;

	foreach my $cameras (@matches)
	{
	LOGDEB "Prepare camera $cameras config:";
		foreach my $cam_parameter_to_write (@pluginconfig_cameras)
		{

		    while (my ($cam_config_variable, $cam_value) = each %R::)
		    {
				if ( $cam_config_variable eq $cam_parameter_to_write . $cameras )
				{
					if (defined ${$cam_value} && ${$cam_value} ne '')
					{
						LOGDEB "Setting configuration variable [".$cam_config_variable . "] to value (" . ${$cam_value} .")";
						$plugin_cfg->param($cam_config_variable , ${$cam_value});
					}
					else
					{
						LOGDEB "Config variable: " . $cam_config_variable . " missing or empty. Ignoring it.";
					}
				}
			}
		}
	}
	$plugin_cfg->param('VERSION', $version);
	LOGDEB "Write config to file";
	$error_message = $ERR{'ERRORS.ERR_SAVE_CONFIG_FILE'};
	$plugin_cfg->save() or &error;

	LOGDEB "Set page title, load header, parse variables, set footer, end";
	$template_title = $SUC{'SAVE.MY_NAME'};
	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefilename);
	$successtemplate->param('SAVE_ALL_OK'		, $SUC{'SAVE.SAVE_ALL_OK'});
	$successtemplate->param('SAVE_MESSAGE'		, $SUC{'SAVE.SAVE_MESSAGE'});
	$successtemplate->param('SAVE_BUTTON_OK' 	, $SUC{'SAVE.SAVE_BUTTON_OK'});
	$successtemplate->param('SAVE_NEXTURL'		, $ENV{REQUEST_URI});
	print $successtemplate->output();
	LoxBerry::Web::lbfooter();
	LOGDEB "Leaving Cam-Connect Plugin after saving the configuration.";
	exit;
}
else
{
	LOGDEB "No, not a save call";
}
LOGDEB "Call default page";
&defaultpage;

#####################################################
# Subs
#####################################################

sub defaultpage
{
	LOGDEB "Sub defaultpage";
	LOGDEB "Prepare Cam list";
	$cam_model_list="";
	open(F,"$lbpdatadir/camera_models.dat") || die "Missing camera list.";
	 flock(F,2);
	 @lines = <F>;
	 flock(F,8);
	close(F);
	foreach (@lines)
	{
	  s/[\n\r]//g;
	  our @cams = split /\|/, $_;
	    $cam_model_list .= "<option value=\"$cams[0]\">$cams[1] $cams[2]</option>\n";
		LOGDEB "Adding cam model: #" . $cams[0] . " " . $cams[1] . " (" . $cams[2] . ")";
	}
	LOGDEB "Set page title, load header, parse variables, set footer, end";
	$template_title = $L{'CC.MY_NAME'};

	$maintemplate->param( "LOGO_ICON"		, get_plugin_icon(64) );
	$maintemplate->param( "HTTP_HOST"		, $ENV{HTTP_HOST});
	$maintemplate->param( "HTTP_PATH"		, '/plugins/' . $lbpplugindir);
	$maintemplate->param( "cam_model_list"	, $cam_model_list);
	$maintemplate->param( "VERSION"			, $version);
	$maintemplate->param( "LOGLEVEL" 		, $L{"CC.LOGLEVEL".$plugin->{PLUGINDB_LOGLEVEL}});
	$lbplogdir =~ s/$lbhomedir\/log\///; # Workaround due to missing variable for Logview
	$maintemplate->param( "LOGFILE" , $lbplogdir . "/" . $logfile );
	LOGDEB "Check for pending notifications for: " . $lbpplugindir . " " . $L{'CC.MY_NAME'};
	my $notifications = LoxBerry::Log::get_notifications_html($lbpplugindir, $L{'CC.MY_NAME'});
	LOGDEB "Notifications are:\n".encode_entities($notifications) if $notifications;
	LOGDEB "No notifications pending." if !$notifications;
	$maintemplate->param( "NOTIFICATIONS" , $notifications);

	my @camdata = ();
	my @known_cams = ();
	foreach (keys %Config) {
		#LOGDEB ($Config{$_}) ? "$_ : $Config{$_}\n" : "$_ :\n";
		next unless /CAM_HOST_OR_IP[0-9]*/;
		s/default.CAM_HOST_OR_IP//;
		push @known_cams, $_;
	}
	@known_cams = sort @known_cams;
	LOGDEB "Found following cameras in config: ".join(",",@known_cams);
	my ($first_cam_id, $last_cam_id) = minmax @known_cams;
	$maintemplate->param(@known_cams.length == 0 ? "NOCAMS" : "SOMECAMS", 1);

	if ( $R::create_cam )
	{
		LOGDEB "Oh, it's a create_cam call. " . $R::create_cam;
		$last_cam_id++;
		LOGDEB "Create new camera: ".$last_cam_id;
		$error_message = $ERR{'ERRORS.ERR_CREATE_CONFIG_FILE'};
		open my $configfileHandle, ">>", $lbpconfigdir . "/" . $pluginconfigfile or &error;
			print $configfileHandle 'CAM_IMAGE_RESIZE'.$last_cam_id.'=9999'."\n";
			print $configfileHandle 'CAM_EMAIL_RESIZE'.$last_cam_id.'=9999'."\n";
			print $configfileHandle 'CAM_HOST_OR_IP'.$last_cam_id.'="'.$L{'CC.CAM_HOST_SUGGESTION'}.'"'."\n";
			print $configfileHandle 'CAM_PORT'.$last_cam_id.'="'.$L{'CC.CAM_PORT_SUGGESTION'}.'"'."\n";
			print $configfileHandle 'CAM_USER'.$last_cam_id.'="'.$L{'CC.CAM_USER_SUGGESTION'}.'"'."\n";
			print $configfileHandle 'CAM_PASS'.$last_cam_id.'=""'."\n";
			print $configfileHandle 'CAM_NAME'.$last_cam_id.'="'.$L{'CC.CAM_NAME_SUGGESTION'}.'"'."\n";
			print $configfileHandle 'CAM_EMAIL_FROM_NAME'.$last_cam_id.'="'.$L{'CC.CAM_EMAIL_FROM_NAME_SUGGESTION'}.'"'."\n";
			print $configfileHandle 'CAM_NO_EMAIL_CB'.$last_cam_id."=0\n";
			print $configfileHandle 'CAM_EMAIL_INLINE_CB'.$last_cam_id."=0\n";
			print $configfileHandle 'CAM_EMAIL_MULTIPICS'.$last_cam_id."=10\n";
			print $configfileHandle 'WATERMARK'.$last_cam_id."=0\n";
			print $configfileHandle 'CAM_EMAIL_USED_CB'.$last_cam_id."=0\n";
			print $configfileHandle 'CAM_NOTE'.$last_cam_id.'="'.$L{'CC.CAM_NOTE_SUGGESTION'}.'"'."\n";
			print $configfileHandle 'CAM_RECIPIENTS'.$last_cam_id.'="'.$L{'CC.EMAIL_RECIPIENTS_SUGGESTION'}.'"'."\n";
			print $configfileHandle 'CAM_MODEL'.$last_cam_id.'=1'."\n";
		close $configfileHandle;
		LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefilename);
		print "OK\n";
		exit;
	} else {
		LOGDEB "No create_cam call. Go ahead";
	}
	if ( $R::delete_cam ) {
		LOGDEB "Oh, it's a delete_cam call. ";
		LOGDEB "Delete camera: ".$R::delete_cam;
		$error_message = $ERR{'ERRORS.ERR_CREATE_CONFIG_FILE'};
		use Tie::File;

		LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefilename);
		print "Content-Type: text/plain\n\n";
		my $cam_param_to_delete = "";
		foreach my $param_to_delete (@pluginconfig_cameras)
	    {
			my $cam_param_to_delete = $param_to_delete.$R::delete_cam."=";
			LOGDEB "Delete cam parameter: ".$cam_param_to_delete;
			tie my @file_lines, 'Tie::File', $lbpconfigdir . "/" . $pluginconfigfile or die;
			@file_lines = grep !/^$cam_param_to_delete/, @file_lines;
			untie @file_lines or die "$!";
		}
		print "OK\n";
		exit;
	} else {
		LOGDEB "No delete_cam call. Go ahead";
	}

	my $cam_list = '<option value="">'. $L{'CC.CAM_SELECT_OPTION'} .'</option>';

	my %js_globals = (
		CC__MY_NAME => $template_title,
		#HTTP_HOST => $maintemplate->param('HTTP_HOST'),
		HTTP_PATH => $maintemplate->param('HTTP_PATH'),
		LBPPLUGINDIR => $lbpplugindir,
		CAMS => \@known_cams,
	);

	foreach my $camno (@known_cams) {
		my %cam;

		my @fill_suggestions = ("CAM_EMAIL_SUBJECT1", "CAM_EMAIL_SUBJECT2",
			"CAM_EMAIL_SUBJECT3", "CAM_EMAIL_DATE_FORMAT", "CAM_EMAIL_TIME_FORMAT",
			"CAM_EMAIL_BODY", "CAM_EMAIL_SIGNATURE");
		foreach my $suggestion_field (@fill_suggestions) {
			if (!defined $plugin_cfg->param( $suggestion_field . $camno ) )
			{
				LOGDEB "Setting suggested CAM configuration variable [" . $suggestion_field . "] to value (" . $L{ "CC." . $suggestion_field . "_SUGGESTION" } . ")";
				$cam{$suggestion_field}	= uri_unescape($L{ "CC." . $suggestion_field . "_SUGGESTION" });
			}
			else
			{
				LOGDEB "Setting CAM configuration variable [" . $suggestion_field . $camno . "] to value (" . uri_unescape($plugin_cfg->param($suggestion_field . $camno)) . ")";
				$cam{$suggestion_field}	= uri_unescape($plugin_cfg->param($suggestion_field . $camno));
			}
		}
		$cam{CAMNO} = $camno;
		$cam{CAM_HOST_OR_IP} 		= $plugin_cfg->param("CAM_HOST_OR_IP".$camno);
		$cam{CAM_PORT} 				= $plugin_cfg->param("CAM_PORT".$camno);
		$cam{CAM_MODEL} 			= $plugin_cfg->param("CAM_MODEL".$camno);
		$cam{CAM_USER} 				= uri_unescape($plugin_cfg->param("CAM_USER".$camno));
		$cam{CAM_PASS} 				= uri_unescape($plugin_cfg->param("CAM_PASS".$camno));
		$cam{CAM_NOTE} 				= uri_unescape($plugin_cfg->param("CAM_NOTE".$camno));
		$cam{CAM_RECIPIENTS} 		= uri_unescape($plugin_cfg->param("CAM_RECIPIENTS".$camno));
		$cam{CAM_NAME} 				= uri_unescape($plugin_cfg->param("CAM_NAME".$camno));
		$cam{CAM_EMAIL_FROM_NAME}	= uri_unescape($plugin_cfg->param("CAM_EMAIL_FROM_NAME".$camno));
		$cam{CAM_IMAGE_RESIZE} 		= $plugin_cfg->param("CAM_IMAGE_RESIZE".$camno);
		$cam{CAM_EMAIL_RESIZE} 		= $plugin_cfg->param("CAM_EMAIL_RESIZE".$camno);
		$cam{CAM_EMAIL_MULTIPICS} 	= $plugin_cfg->param("CAM_EMAIL_MULTIPICS".$camno);
		foreach my $cam_parameter_to_process ('WATERMARK',
			'CAM_NO_EMAIL_CB','CAM_EMAIL_INLINE_CB','CAM_EMAIL_USED_CB')
		{
			my $param = $cam_parameter_to_process . $camno;
			if ( $plugin_cfg->param($param) && int($plugin_cfg->param($param)) eq 1 )
			{
				$cam{$cam_parameter_to_process} = 1;
			    $cam{$cam_parameter_to_process."_VAL"} = 'checked';
			}
			else
			{
				$cam{$cam_parameter_to_process} = 0;
			    $cam{$cam_parameter_to_process. "_VAL"}  = '';
			}
			LOGDEB "Set special parameter " . $param;
		}
		$cam_list .= '<option value="#camdiv' . $camno . '">#'
			. $camno . ' - ' . $cam{CAM_NAME} . '</option>';
		# select boxes
		foreach my $id ('CAM_MODEL', 'CAM_IMAGE_RESIZE', 'CAM_EMAIL_RESIZE',
			'CAM_EMAIL_MULTIPICS')
		{
			$js_globals{$id . $camno} = $plugin_cfg->param($id . $camno);
		}
		push(@camdata, \%cam);
	}
	$maintemplate->param("CAMDATA" => \@camdata);
	$maintemplate->param("KNOWN_CAMS" => join(",", @known_cams));
	$maintemplate->param("CAM_LIST" => $cam_list);

	# all index.js required mappings
	my $txt = JSON->new->utf8->space_after->pretty->encode(\%js_globals);

	$main::htmlhead .= '<script src="index.js"></script>
<script>var js_globals = ' . $txt  . ';</script>
';

	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefilename);
    print $maintemplate->output();
	LoxBerry::Web::lbfooter();
	LOGDEB "Leaving Cam-Connect Plugin normally";
	exit;
}

sub error
{
	LOGDEB "Sub error";
	LOGERR $error_message;
	LOGDEB "Set page title, load header, parse variables, set footer, end with error";
	$template_title = $ERR{'ERRORS.MY_NAME'} . " - " . $ERR{'ERRORS.ERR_TITLE'};
	LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefilename);
	$errortemplate->param('ERR_MESSAGE'		, $error_message);
	$errortemplate->param('ERR_TITLE'		, $ERR{'ERRORS.ERR_TITLE'});
	$errortemplate->param('ERR_BUTTON_BACK' , $ERR{'ERRORS.ERR_BUTTON_BACK'});
	print $errortemplate->output();
	LoxBerry::Web::lbfooter();
	LOGDEB "Leaving Cam-Connect Plugin with an error";
	exit;
}
