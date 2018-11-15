#!/bin/ksh93

typeset -r VERSION='1.0' FPROG=${.sh.file} PROG=${FPROG##*/} SDIR=${FPROG%/*}

function showUsage {
	[[ -n $1 ]] && X='-?' ||  X='--man'
	getopts -a ${PROG} "${ print ${USAGE} ; }" OPT $X
}

typeset -A SMAP=(
	['icons']='webfrontend/html/system/images/icons'
	['templates']='templates/plugins'
	['data']='data/plugins'
	['webfrontend/html']='webfrontend/html/plugins'
	['webfrontend/htmlauth']='webfrontend/htmlauth/plugins'
)

function linkPlugin {
	typeset PNAME="$1" D S
	[[ -z ${PNAME} ]] && print -u2 'Plugin name required. Exiting' && return 10

	for S in ${!SMAP[@]} ; do
		D="${DST}/${SMAP[$S]}/${PNAME}"
		S="${SRC}/$S"
		if [[ -d $D ]]; then
			[[ -e "${D}.orig" ]] && ${DRY} rm -rf "$D" || \
				${DRY} mv "$D" "${D}.orig"
		fi
		${DRY} ln -s "$S" "$D"
	done
}

function unlinkPlugin {
	typeset PNAME="$1" D S
	[[ -z ${PNAME} ]] && print -u2 'Plugin name required. Exiting' && return 10

	for S in ${!SMAP[@]} ; do
		D="${DST}/${SMAP[$S]}/${PNAME}"
		[[ -h $D ]] || continue				# no symlink -> not from us
		[[ -e "${D}.orig" ]] || continue	# no original -> leave it as is
		${DRY} rm -f "${D}" || continue
		${DRY} mv "${D}.orig" "${D}"
	done
}

function doMain {
	typeset L X
	integer C=0
	if [[ -z ${SRC} ]]; then
		print -u2 'Source directory not specified. Exciting.'
		return 1
	else
		cd ${SRC} || return 2
		SRC="${PWD}"
		if [[ ! -e plugin.cfg ]]; then
			print -u2 "${SRC}/plugin.cfg not found. Exiting."
			return 3
		fi
		while read L X; do
			if [[ ${L:0:1} == '[' ]]; then
				[[ $L == '[PLUGIN]' ]] && C=1 || C=0
				continue
			fi
			(( C )) || continue
			[[ ${L:0:5} == 'NAME=' ]] || continue
			X="${L:5}"
			break
		done <plugin.cfg
		if [[ -z $X ]]; then
			print -u2 "Plugin name not found in ${SRC}/plugin.cfg! Exiting."
			return 4
		fi
	fi
	if [[ -z ${DST} ]]; then
		[[ -n ${LBHOMEDIR} ]] && DST="${LBHOMEDIR}" || DST='/opt/loxberry'
	fi
	cd ${DST} || return 5
	DST="${PWD}"
	cd - >/dev/null
	(( UNDO )) && unlinkPlugin "$X" || linkPlugin "$X"
}

USAGE="[-?${VERSION}"' ]
[-copyright?Copyright (c) 2018 Jens Elkner. All rights reserved.]
[-license?CDDL 1.0]
[+NAME?'"${PROG}"' - symlinks developer source directory into a live instance.]
[+DESCRIPTION?This script can be used to symlink the source code of a plugin (probably cloned via github) into a live instance of Loxberry. It does this for the default html related directories by renaming them into \adir\a\b.orig\b and than symlinking the corresponding directory from the source directory.]
[h:help?Print this help and exit.]
[F:functions?Print a list of all functions available.]
[T:trace]:[functionList?A comma separated list of functions of this script to trace (convinience for troubleshooting).]
[d:dest]:[lbhome?The Loxberry install directory. If not given, \bLBHOMEDIR\b env var will be used. If it is not set, \b/opt/loxberry\b will be used. No action is taken if the destination directory does not exist.]
[n:dry?Just show, what would be done, but do not do it.]
[s:src]:[srcdir?The base directory containing the source code of the plugin in question.]
[u:undo?Remove plugin related symlinks created by this script and restore the original directories by renaming them back to its original name.]
'

X="${ print ${USAGE} ; }"
unset SRC DST DRY UNDO
DRY=
integer UNDO=0
while getopts "${X}" OPT ; do
	case ${OPT} in
		h) showUsage ; exit 0 ;;
		T)	if [[ ${OPTARG} == 'ALL' ]]; then
				typeset -ft ${ typeset +f ; }
			else
				typeset -ft ${OPTARG//,/ }
			fi
			;;
		F) typeset +f && exit 0 ;;
		d) DST="${OPTARG}" ;;
		s) SRC="${OPTARG}" ;;
		n) DRY="print --" ;;
		u) UNDO=1 ;;
		*) showUsage 1 ; exit 1 ;;
	esac
done

X=$((OPTIND-1))
shift $X && OPTIND=1
unset X

doMain "$@"
