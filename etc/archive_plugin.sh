#!/bin/ksh93

typeset -r VERSION='1.0'
typeset -r DIRS='config bin templates cron data webfrontend icons daemon uninstall sudoers dpkg'
typeset -r FILES='plugin.cfg preroot.sh preupgrade.sh preinstall.sh postinstall.sh postupgrade.sh postroot.sh LICENSE.txt NOTICE.txt'

LIC='[-?'"${VERSION}"' ]
[-copyright?Copyright (c) 2018 Jens Elkner. All rights reserved.]
[-license?CDDL 1.0]'
SDIR=${.sh.file%/*}
typeset -r FPROG=${.sh.file}
typeset -r PROG=${FPROG##*/}

for H in log.kshlib man.kshlib ; do
	X=${SDIR}/$H
	[[ -r $X ]] && . $X && continue
	X=${ whence $H; }
	[[ -z $X ]] && print "$H not found - exiting." && exit 1
	. $X 
done
unset H

function showUsage {
	typeset WHAT="$1" X='--man'
	[[ -z ${WHAT} ]] && WHAT='MAIN' && X='-?'
	getopts -a "${PROG}" "${ print ${Man.FUNC[${WHAT}]}; }" OPT $X
}

function doMain {
	typeset SRC ARC VERS TMP

	cd ${SDIR}/.. || return 1
	[[ ! -f plugin.cfg ]] && Log.fatal "${PWD}/plugin.cfg not found" && return 2
	TMP=${ mktemp -d -t ${DST}.XXXXXX ; }
	[[ -z ${TMP} ]] && return 3

	VERS=${ grep '^VERSION=' plugin.cfg; }
	VERS=${VERS:8}
	[[ -z ${DST} ]] && DST=${PWD##*/} || DST=${DST##*/}
	[[ -n ${VERS} ]] && DST+="-${VERS}"
	# zip itself does not have a prefix option. 
	# on linux ZFS one cannot create hard links even on the same FS =8-( .
	# 'git archive' cannot arc the current dir, but only commited stuff.
	# So we do it the crazy way
	mkdir ${TMP}/${DST} || return 4

	ARC="/tmp/${DST}.zip"
	rm -f ${ARC}
	for T in ${FILES} ; do
		[[ -e $T ]] && SRC+="$T\n"
	done
	for T in ${DIRS} ; do
		[[ -e $T ]] || continue
		find $T -depth | while read LINE; do
			SRC+="${LINE}\n"
		done
	done
	print -n  "${SRC}" | cpio -pumd ${TMP}/${DST}
	
	cd ${TMP}
	${ECHO} zip -9yr "${ARC}" "${DST}"
	${ECHO} ls -al "${ARC}"
	cd -
	${ECHO} rm -rf "${TMP}"
}

Man.addFunc MAIN '' '[+NAME?'"${PROG}"' - create the plugin zip archive]
[+DESCRIPTION?Create a zip file of this repo clone without any overhead, ready to be used for LoxBerry installation.]
[h:help?Print this help and exit.]
[F:functions?Print out a list of all defined functions. Just invokes the \btypeset +f\b builtin.]
[H:usage]:[function?Show the usage information for the given function if available and exit. See also option \b-F\b.]
[T:trace]:[fname_list?A comma or whitspace separated list of function names, which should be traced during execution.]
[+?]
[n:dry?Just show, what would be done, but do not do it.]
[p:prefix]:[name?Use the given \aname\a as path prefix for all files and directories in the archive and for the archive name itself. By default the basename of the directory containing the repo will be used.]
'
X="${ print ${Man.FUNC[MAIN]} ; }"
ECHO=
DST=
while getopts "${X}" option ; do
	case "${option}" in
		h) showUsage MAIN ; exit 0 ;;
		F) typeset +f ; exit 0 ;;
		H)  if [[ ${OPTARG%_t} != ${OPTARG} ]]; then
				${OPTARG} --man   # self-defined types
			else
				showUsage "${OPTARG}"   # function
			fi
			exit 0
			;;
		T)	if [[ ${OPTARG} == 'ALL' ]]; then
				typeset -ft ${ typeset +f ; }
			else
				typeset -ft ${OPTARG//,/ }
			fi
			;;
		n) ECHO='print -- ';;
		p) DST="${OPTARG}" ;;
		*) showUsage ;;
	esac
done
X=$((OPTIND-1))
shift $X

doMain "$@"
