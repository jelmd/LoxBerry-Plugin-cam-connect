#!/bin/ksh93

typeset -r VERSION='1.0'

LIC='[-?'"${VERSION}"' ]
[-copyright?Copyright (c) 2017 Jens Elkner. Alle Rechte vorbehalten.]
[-license?CDDL 1.0]'
SDIR=${.sh.file%/*}
typeset -r FPROG=${.sh.file}
typeset -r PROG=${FPROG##*/}

typeset -r DEFAULT_HTDOCS="${SDIR%/*}/htdocs"
typeset -r DEFAULT_URL='http://localhost/'

typeset -r VNU_JAR='/local/share/javax/vnu.jar'

for H in log.kshlib man.kshlib ; do
	X=${SDIR}/$H
	[[ -r $X ]] && . $X && continue
	X=${ whence $H; }
	[[ -z $X ]] && print "$H nicht gefunden - Abbruch." && exit 1
	. $X
done
unset H

function showUsage {
	typeset WHAT="$1" X='--man'
	[[ -z ${WHAT} ]] && WHAT='MAIN' && X='-?'
    getopts -a "${PROG}" "${ print ${Man.FUNC[${WHAT}]}; }" OPT $X
}

function checkNuHtml {
	typeset -i ERR=0
	typeset X=${ whence java ; }
	if [[ -z $X ]]; then
		Log.fatal 'java wurde nicht gefunden. Bitte installieren bzw. PATH' \
			'environment variable entsprechend anpassen.'
		(( ERR++ ))
	fi
	if [[ ! -r ${VNU_JAR} ]]; then
		log.fatal "${VNU_JAR} nicht gefunden. Am besten das Archiv via" \
			'https://github.com/validator/validator/releases herunterladen,' \
			'auspacken und dist/vnu.jar kopieren.'
		(( ERR++ ))
	fi
	return $ERR
}

function doMain {
	[[ -z ${HTDOCS} ]] && HTDOCS="${DEFAULT_HTDOCS}"
	[[ -z ${URL} ]] && URL="${DEFAULT_URL%%/}"
	typeset -a TOCHECK
	if [[ -z ${FSET} ]]; then
		if ! cd ${HTDOCS} ; then
			Log.fatal 'Nutze Option "-d dir" um das zu durchsuchende' \
				'Verzeichnis einzustellen.'
			return 1
		fi
		typeset R='( -type d ! -name . -prune ) -o'
		(( RECURSIVE )) && R=
		find . $R \( -name "*.shtml" -o -name "*.html" \) -print | sort | \
		while read X ; do
			TOCHECK+=( "${URL}/${X:2}" )
		done
	else
		for X in "${FSET[@]}" ; do
			TOCHECK+=( "${URL}/$X" )
		done
	fi
	[[ -z ${TOCHECK} ]] && Log.info "No files to check found - exiting." && \
		return 0
	checkNuHtml || return 2
	${DRY} java -jar ${VNU_JAR} --html --format gnu "${TOCHECK[@]}"
}

Man.addFunc MAIN '' '[+NAME?'"${PROG}"' - local HTML validator]
[+DESCRIPTION?Diese script wechselt in das jeweilige \asrcdir\a Verzeichnis, sucht darin rekursiv alle *.html und *.shtml Dateien und validiert diese anschließend mittels "Nu Html Checker", indem der entsprechende Pfad an den \abaseURL\a/ angehangen wird.]
[h:help?Diese Hilfe ausgegeben und Script beenden.]
[F:functions?Liste aller definierten Funktionen im Script ausgeben (\btypeset +f\b).]
[H:usage]:[function?Hilfe für die angegebene Script-Funktion bzw. Objekttyp anzeigen (soweit verfügbar) und Script beenden. Siehe auch Option \b-F\b.]
[T:trace]:[fname_list?Eine Komma- oder Leerzeichen-separierte Liste von Funktionsnamen, die während ihrer Ausführung getracet werden sollen.]
[+?]
[d:dry?Nur anzeigen, wie validiert werden würde, aber nicht wirlich validieren.]
[R:no-recursive?Dateien nur direkt im entsprechenden \asrcdir\a suchen, d.h. nicht rekursive Suche anwenden.]
[f:file]:[file?Zu validierende Dateien nicht in \asrcdir\a suchen. Stattdessen nur die via \b-f\b \afile\a angegebenen Dateien validieren. Die angegebene Datei muß nicht lokal existieren, sondern wird einfach an den URL-Prefix angehangen. D.h. die Option kann mehrfach verwendet werden.]
[s:srcdir]:[dir?Verzeichnis, in dem nach zu validierenden *.html und *.shtml Dateien rekursiv gesucht werden soll. Default: '"'${DEFAULT_HTDOCS}'"']
[u:url]:[URL?Der URL-Prefix, der für jede gefundenene, zu validierende Datei verwendet werden soll. Ist der URL z.B. "http://my.si.te/bla" und eine gefundene Datei "foo/bar.html", so wird final "http://my.si.te/bla/foo/bar.html" validiert. Default: '"'${DEFAULT_URL}'"']
'
typeset HTDOCS= URL= DRY=
unset FSET; typeset -a FSET
typeset -i RECURSIVE=1

X="${ print ${Man.FUNC[MAIN]} ; }"
while getopts "${X}" option ; do
	case "${option}" in
		h) showUsage MAIN ; exit 0 ;;
		F) typeset +f ; exit 0 ;;
		H)  if [[ ${OPTARG%_t} != $OPTARG ]]; then
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
		R) RECURSIVE=0 ;;
		d) DRY='print -- ' ;;
		f) FSET+=( "${OPTARG##/}" ) ;;
		s) HTDOCS="${OPTARG}" ;;
		u) URL="${OPTARG%%/}" ;;
		*) showUsage ;;
	esac
done
X=$((OPTIND-1))
shift $X
unset X

doMain "$@"
