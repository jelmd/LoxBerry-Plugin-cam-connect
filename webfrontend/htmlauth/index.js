/**
 * The contents of this file are subject to the terms of the
 * Common Development and Distribution License (the "License") version 1.1!
 * You may not use this file except in compliance with the License.
 *
 * See LICENSE.txt and NOTICE.txt included in this distribution for the specific
 * language governing permissions and limitations under the License.
 *
 * Copyright 2018 Jens Elkner (jel+loxberry-src@cs.ovgu.de)
 */
var supress_change = false;

// Scroll function for camera dropdown
jQuery.fn.extend({
	scrollToMe: function (dst) {
		var x = jQuery(dst ? dst : this).offset().top - 50;
		jQuery('html,body').animate({scrollTop: x}, 400);
	}
});

// Set initial values for Checkboxes
function initCB(num, email, email_opt) {
	var changeFn = function(ev) {
		var cid = '#' + ev.target.id;
		var vid = cid.replace('CB_', '');
		$(vid).val(ev.target.checked ? 1 : 0);
		if (cid.startsWith('#CB_MAIL') && cid.charAt(8) != '_') {
			if (ev.target.checked) {
				$(".cam_email" + num).fadeIn();
				for (let s of email_opt) {
					if ($(s + num).val() == '')
						$(s + num).val($(s + num).attr('placeholder'));
				}
				validate_chk_object(email.map(x => x + num));
			} else {
				$(".cam_email" + num).fadeOut();
				validate_clean_objects(email.map(x => x + num));
			}
		}
	};
	var all_cb = ['WATERMARK', 'MAIL', 'MAIL_IMG_INLINE'];

	for (let name of all_cb) {
		var cid = '#CB_' + name + num;
		$(cid).on('change', changeFn).trigger('change');
	}
}

function initLists(num) {
	$('#NAME' + num).keyup(function(event) {
		$('#CAM_LIST option[value="#camdiv' + num + '"]')
			.text('#' + num + ' - ' + $(this).val());
		supress_change = true;
		$('#CAM_LIST').val('#camdiv' + num).trigger('change');
		supress_change = false;
	});

	$('#camdiv' + num + ' :input').on('change', function(event) {
		$("#btntest" + num).prop('disabled', true);
	});
	$('#camdiv' + num + ' button.saveB').on('click', function(event) {
		$('#saveformdata').val(1); 
	});

	var selects = ['MODEL', 'IMG_WIDTH', 'MAIL_IMG_WIDTH', 'MAIL_PICS']
		.map(x => x + num);
	for (let x of selects) {
		if (js_globals[x] != undefined) {
			// at least on FF setting the value doesn't trigger a change - oops
			$('#' + x).val(js_globals[x]).trigger('change');
		}
	}
}

function cam_decorate(num) {
	var fields = ['#NAME', '#NOTE', '#ADDR', '#PORT'];
	var email_opt = ['#MAIL_SUBJECTA', '#MAIL_DATE', '#MAIL_SUBJECTB',
			'#MAIL_TIME', '#MAIL_SUBJECTC'];
	var email = ['#RECIPIENTS','#MAIL_FROM'];
	email = email.concat(email_opt);
	fields = fields.concat(email);

	for (var i=fields.length - 1; i >= 0; i--) {
		validate_enable(fields[i] + num);
	}
	validate_chk_object(fields);

	initLists(num);
	initCB(num, email, email_opt);

	$('#camDelete' + num).on('click', function(ev) {
		$.ajax({ url: '', type: 'GET', data: { 'delete_cam': num } })
		.done(function() {
			$('#camdiv' + num).remove();
			if ($('.camdiv').length != 0) {
				$('#CAM_LIST option[value="#camdiv' + num + '"]').remove();
				$('#CAM_LIST option[value=""]').attr('selected', true).trigger('change');
			}
		});
		return false;
	});

	$("#btntest" + num).click(function () {
		$.ajax({
			url: '/plugins/'+ js_globals.LBPPLUGINDIR +'/get_notifications.cgi',
			type: 'GET',
			data: {
				'package': js_globals.LBPPLUGINDIR,
				'name': js_globals.CC__MY_NAME
			}
		}).success(function(data) {
			$('#notifblock').html(data).trigger('create');
			if (data.length > 10) {
				$('#notifblock').scrollToMe();
			}
		});
		url2open = js_globals.HTTP_PATH + '/?cam=' + num;
		window.open(url2open, js_globals.C__MY_NAME + num,
			//'status=no,scrollbars=no,titlebar=no,toolbar=no,menubar=no'
			//+ ',location=no');
		);
	});
}

function cam_decorate_all() {
	$('#CAM_LIST').on('change', function(ev) {
		if (supress_change)
			return;
		var o = ev.target.value;
		$(o ? o : '#CAM_LIST').scrollToMe();
	});
	$('#create_cam').on('click', function(ev) {
		$.ajax({url: '', type: 'GET', async: false, data: {'create_cam': 1}})
		.success(function(data) {
			console.log('Cam created.');
		});
	});

	var no_cams = js_globals.CAMS.length == 0;

	$('.jump2select').on('click', function(ev) {
		$('#CAM_LIST').scrollToMe(); return false;
	});

	var timeoutFn = function(ev) {
		$('#del_log > span').hide();
		$('#del_log > span:nth-child(1)').show();
		$('#del_log').css('background-color', '');
	};
	timeoutFn();

	$('#del_log').on('click', function(ev) {
		$('#del_log > span:nth-child(1)').hide();
		$('#del_log > span:nth-child(2)').show();
		$('#del_log').css('background-color',
			$('#del_log > span:nth-child(2)').css('background-color'));
		$.ajax({url: '', type: 'GET', data: { 'delete_log': 1 },
			success: function (data) {
				$('#del_log > span:nth-child(2)').hide();
				$('#del_log > span:nth-child(3)').show();
				$('#del_log').css('background-color',
					$('#del_log > span:nth-child(3)').css('background-color'));
				setTimeout(timeoutFn, 2000);
			},
			error: function (textStatus, errorThrown) {
				$('#del_log > span:nth-child(2)').hide();
				$('#del_log > span:nth-child(4)').show();
				$('#del_log').css('background-color',
					$('#del_log > span:nth-child(4)').css('background-color'));
				setTimeout(timeoutFn, 2000);
			}
		});
		return false;	/* do not reload the page */
	});

	for (let cam of js_globals.CAMS) {
		cam_decorate(cam);
	}

	$('#main_form input, #main_form select, #main_form button').each(function(){
		if (!$(this).attr('name'))
			$(this).attr('name', $(this).attr('id'));
	});
}

$(document).ready(function() { cam_decorate_all(); });
