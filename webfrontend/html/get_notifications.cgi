#!/usr/bin/perl

# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License") version 1.1!
# You may not use this file except in compliance with the License.
#
# See LICENSE.txt and NOTICE.txt included in this distribution for the specific
# language governing permissions and limitations under the License.
#
# Copyright 2018 Jens Elkner (jel+loxberry-src@cs.ovgu.de)

# Get notifications in html format
use HTML::Template;
use LoxBerry::Log;
use CGI qw/:standard/;

my $num_args = $#ARGV + 1;
my $package;
my $nname;
if ( param("package") ne "" )
{
	print "Content-Type: text/html\n\n";
	$package = param("package");
	$nname   = param("name");
	LOGDEB "package: $package ; nname = $nname";
} elsif ($ARGV[0] ne "") {
	$package = $ARGV[0];
	$nname   = $ARGV[1];
	LOGDEB "package: $package ; nname = $nname";
} else {
	print "Content-Type: text/plain\n\nInvalid request.";
	LOGDEB "Invalid request.";
	exit 1;
}
print LoxBerry::Log::get_notifications_html($package , $nname);
exit;
