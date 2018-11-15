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
		var vid = cid.replace('_checkbox', '');
		$(vid).val(ev.target.checked ? 1 : 0);
		if (cid.startsWith('#CAM_EMAIL_USED_CB')) {
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
	var all_cb = [ 'WATERMARK',
		'CAM_NO_EMAIL_CB', 'CAM_EMAIL_INLINE_CB', 'CAM_EMAIL_USED_CB'];

	for (let name of all_cb) {
		var cid = '#' + name + '_checkbox' + num;
		$(cid).on('change', changeFn).trigger('change');
	}
}

function initLists(num) {
	$("#CAM_NAME" + num).keyup(function(event) {
		$('#CAM_LIST option[value="#camdiv' + num + '"]')
			.text('#' + num + ' - ' + $(this).val());
		supress_change = true;
		$('#CAM_LIST').val('#camdiv' + num).trigger('change');
		supress_change = false;
	});

	$("#camdiv" + num + " :input").on('change', function(event) {
		$("#btntest" + num).prop('disabled', true);
		$("#btntestsavehint" + num).hide();
	});

	var selects = ['CAM_MODEL',
		'CAM_IMAGE_RESIZE', 'CAM_EMAIL_RESIZE', 'CAM_EMAIL_MULTIPICS']
		.map(x => x + num);
	for (let x of selects) {
		if (js_globals[x] != undefined) {
			// at least on FF setting the value doesn't trigger a change - oops
			$('#' + x).val(js_globals[x]).trigger('change');
		}
	}
}

function cam_decorate(num) {
	var fields =
		['#CAM_NAME','#CAM_NOTE','#CAM_HOST_OR_IP','#CAM_PORT'];
	var email_opt =
		['#CAM_EMAIL_SUBJECT1','#CAM_EMAIL_DATE_FORMAT', '#CAM_EMAIL_SUBJECT2',
			'#CAM_EMAIL_TIME_FORMAT','#CAM_EMAIL_SUBJECT3'];
	var email = ['#CAM_RECIPIENTS','#CAM_EMAIL_FROM_NAME'];
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
			if ($('.camdiv').length == 0) {
				$('#cam_headline').prop('display', 'none');
				$('#no_cam_headline').prop('display', 'block');
			} else {
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
	$('#cam_headline').css('display', no_cams ? 'none' : 'block');
	$('#no_cam_headline').css('display', no_cams ? 'block' : 'none');

	$('.jump2CamSelect').on('click', function(ev) {
		$('#CAM_LIST').scrollToMe(); return false;
	});

	$('#delete_log_btn > span').hide();
	$('#delete_log_btn > span:nth-child(1)').show();

	$('delete_log_btn').on('click', function(ev) {
		$('#delete_log_div').css('background-color','yellow');
		$('#delete_log_btn > span:nth-child(1)').hide();
		$('#delete_log_btn > span:nth-child(2)').show();
		$.ajax({url: '', type: 'GET', data: { 'delete_log': 1 },
			success: function (data) {
				$('#delete_log_div').css('background-color', 'green');
				$('#delete_log_btn > span:nth-child(2)').hide();
				$('#delete_log_btn > span:nth-child(3)').show();
				setTimeout( function() {
					$('#delete_log_div').css('background-color','');
					$('#delete_log_btn > span:nth-child(2)').hide();
					$('#delete_log_btn > span:nth-child(1)').show();
				}, 2000);
			},
			error: function (textStatus, errorThrown) {
				$('#delete_log_div').css('background-color','red');
				$('#delete_log_btn > span:nth-child(2)').hide();
				$('#delete_log_btn > span:nth-child(4)').show();
				setTimeout( function() {
					$('#delete_log_div').css('background-color','');
					$('#delete_log_btn > span:nth-child(2)').hide();
					$('#delete_log_btn > span:nth-child(1)').show();
				}, 2000);
			}
		});
		return false;
	});

	for (let cam of js_globals.CAMS) {
		cam_decorate(cam);
	}

	$('#main_form input, #main_form select, #main_form button').each(function() {
		if (!$(this).attr('name'))
			$(this).attr('name', $(this).attr('id'));
	});
}

$(document).ready(function() { cam_decorate_all(); });
