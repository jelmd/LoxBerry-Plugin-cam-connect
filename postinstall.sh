#!/bin/ksh93

function cfgUpdate {
	typeset LINE ID

	# should be idempotent
	sed -e 's/^CAM_USER/USERNAME/' \
		-e 's/^CAM_//' \
		-e 's/^HOST_OR_IP/ADDR/' \
		-e 's/^PASS/PW/' \
		-e 's/^IMAGE_RESIZE/IMG_WIDTH/' \
		-e 's/^EMAIL_USED_CB/MAIL/' \
		-e 's/^EMAIL_FROM_NAME/MAIL_FROM/'  \
		-e 's/^EMAIL_SUBJECT1/MAIL_SUBJECTA/' \
		-e 's/^EMAIL_SUBJECT2/MAIL_SUBJECTB/' \
		-e 's/^EMAIL_SUBJECT3/MAIL_SUBJECTC/' \
		-e 's/^EMAIL_DATE_FORMAT/MAIL_DATE/' \
		-e 's/^EMAIL_BODY/MAIL_BODY/' \
		-e 's/^EMAIL_SIGNATURE/MAIL_SIG/' \
		-e 's/^EMAIL_RESIZE/MAIL_IMG_WIDTH/' \
		-e 's/^EMAIL_INLINE_CB/MAIL_IMG_INLINE/' \
		-e '/^NO_EMAIL_CB/ d' \
		-e 's/^EMAIL_MULTIPICS/MAIL_PICS/' \
		"$1" > "$2"

	# not very efficient, but good enough
	egrep '^NO_EMAIL_CB[0-9]+=1' "$1" | while read LINE ; do
		ID=${LINE%%=*}
		ID=${ID:11}
		sed -i -e "/^MAIL${ID}=/ s/=.*/=0/" "$2"
	done
	touch -r "$1" "$2"
	#cp -vpr /tmp/REPLACELBPPLUGINDIR/* REPLACELBPCONFIGDIR/
}

function doMain {
	echo '<INFO> Restoring old config files ...'
	[[ ! -e REPLACELBPCONFIGDIR ]] && mkdir -p REPLACELBPCONFIGDIR
	if [[ -d /tmp/REPLACELBPPLUGINDIR ]]; then
		for F in ~(N)/tmp/REPLACELBPPLUGINDIR/* ; do
			[[ -n $F && -f $F ]] || continue
			cfgUpdate "$F" "REPLACELBPCONFIGDIR/${F##*/}"
		done
	fi
	
	DST="REPLACELBPCONFIGDIR/snap-cam.cfg"
	SRC="REPLACELBPCONFIGDIR/../cam-connect/cam-connect.cfg"
	[[ -e ${SRC} && ! -s ${DST} ]] && cfgUpdate "${SRC}" "${DST}"
	
	echo '<INFO> Done.'
	rm -rf /tmp/REPLACELBPPLUGINDIR
	return 0
}	

doMain "$@"
