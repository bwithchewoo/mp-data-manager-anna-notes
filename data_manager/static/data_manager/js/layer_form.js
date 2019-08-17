

show_layertype_form = function(layertype) {
  $('.field-wms_help').parent().addClass('collapsed');
  $('.field-wms_help').parent().children('h2').children('a').text('Show');

  var url = $('#id_url').val()

  if (url.length > 0) {

    if ($('#id_wms_help').is(':checked')) {

      $.ajax({
          url: '/data_manager/wms_capabilities/',
          data: {
            url: url
          },
          success: function(data) {
            // SWITCH WMS INPUTS TO SELECTORS

            // Replace WMS Layer Name
            slug_val = $('#id_wms_slug').val();
            layer_name_html = '<select id="id_wms_slug" name="wms_slug">';
            for (var i = 0; i < data.layers.length; i++) {
              opt_val = data.layers[i];
              layer_name_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
            }
            layer_name_html += '</select>';
            $('#id_wms_slug').replaceWith( layer_name_html);
            if (data.layers.indexOf(slug_val) >= 0) {
              $('#id_wms_slug').val(slug_val);
            }
            slug_val =   $('#id_wms_slug').val();
            $('#id_wms_slug').change(function() {
              show_layertype_form($('#id_layer_type option:selected').text());
            });

            // Set wms version (only 1.1.1 supported)
            $('#id_wms_version').val(data.version);
            $('.field-wms_version.field-box').hide()

            // Replace WMS Format
            format_val = $('#id_wms_format').val();
            format_html = '<select id="id_wms_format" name="wms_format">';
            for (var i = 0; i < data.formats.length; i++) {
              opt_val = data.formats[i];
              format_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
            }
            format_html += '</select>';
            $('#id_wms_format').replaceWith(format_html);
            if (data.formats.indexOf(format_val) >= 0) {
              $('#id_wms_format').val(format_val);
            }

            // Replace SRS
            srs_val = $('#id_wms_srs').val();
            srs_html = '<select id="id_wms_srs" name="wms_srs">';

            for (var i = 0; i < data.srs[slug_val].length; i++) {
              opt_val = data.srs[slug_val][i];
              srs_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
            }
            srs_html += '</select>';
            $('#id_wms_srs').replaceWith(srs_html);
            if (data.srs[slug_val].indexOf(srs_val) >= 0) {
              $('#id_wms_srs').val(srs_val);
            }

            $('#id_wms_srs').change(function() {
              if ($('#id_wms_srs').val().toLowerCase() == 'epsg:3857') {
                $('#id_wms_time_item').prop('disabled', true);
                $('#id_wms_additional').prop('disabled', false);
              } else {
                $('#id_wms_time_item').prop('disabled', false);
                $('#id_wms_additional').prop('disabled', true);
              }
            });

            // Replace Styles
            style_keys = Object.keys(data.styles[slug_val]);
            if (style_keys.length == 0) {
              $('#id_wms_styles').val(null);
              $('#id_wms_styles').prop('disabled', true);
            } else {
              $('#id_wms_styles').prop('disabled', false);
              style_val = $('#id_wms_styles').val();
              style_html = '<select id="id_wms_styles" name="wms_srs">';
              style_html += '<option value="">Default</option>';
              for (var i = 0; i < style_keys.length; i++) {
                opt_val = style_keys[i];
                style_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
                // TODO: Test if this works with a WMS server with styles.
              }
              style_html += '</select>';
              $('#id_wms_styles').replaceWith(style_html);
              if (Object.keys(data.styles[slug_val]).indexOf(style_val) >= 0) {
                $('#id_wms_styles').val(style_val);
              }
            }

            // Replace Time
            $('#wms_timing_default').remove();
            $('#wms_timing_position_label').remove();
            $('#wms_timing_position_options').remove();

            if (data.time[slug_val].default == null) {
              $('#id_wms_timing').val(null);
              $('#id_wms_timing').prop('disabled', true);
            } else {
              $('#id_wms_timing').prop('disabled', false);
              $('<p id="wms_timing_default"><b>*** Default = ' + data.time[slug_val].default + '***</b></p>').insertAfter('#id_wms_timing');
              if (data.time[slug_val].positions.length > 0) {
                $('<p id="wms_timing_position_label">Position options:</p>').insertAfter('#wms_timing_default');
                wms_timing_positions_html = '<ul id="wms_timing_position_options">';
                for (var i = 0; i < data.time[slug_val].positions.length; i++) {
                  wms_timing_positions_html += '<li>' + data.time[slug_val].positions[i] + '</li>';
                }
                wms_timing_positions_html += '</ul>';
                $(wms_timing_positions_html).insertAfter('#wms_timing_position_label');
              }
            }

            /* CAPABILITIES */
            if (Object.keys(data.capabilities).length > 0) {
              var info_bool_field = $('#id_wms_info');
              var info_format_field = $('#id_wms_info_format');
              if (data.capabilities.hasOwnProperty('featureInfo') && data.capabilities.featureInfo.available) {
                $('.form-row.field-wms_info.field-wms_info_format').show();
                info_format_field.prop('disabled', false);
                info_bool_field.prop('disabled', false);

                var info_formats = data.capabilities.featureInfo.formats;
                var info_format_val = info_format_field.val();
                var info_format_html = '<select id="id_wms_info_format" name="wms_info_format">';
                info_format_html += '<option value="">None (no reporting)</option>';
                for (var i = 0; i < info_formats.length; i++) {
                  var opt_val = info_formats[i];
                  info_format_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
                }
                info_format_html += '</select>';
                info_format_field.replaceWith(info_format_html);

                if (info_formats.indexOf(info_format_val) >= 0) {
                    $('#id_wms_info_format').val(info_format_val);
                }

              } else {
                // set featureInfo to false, hide section
                info_bool_field.prop('checked', false);
                info_bool_field.prop('disabled', true);
                info_format_field.val(null);
                info_format_field.prop('disabled', true);
                $('.form-row.field-wms_info.field-wms_info_format').hide();
              }
            }
            check_queryable(data.queryable);
          },
          error: function(data) {
            url = $('#id_url').val();
            err_msg = 'ERROR: Layer url ' + url + ' does not appear to be a valid WMS endpoint.'
            window.alert(err_msg);
          }
      });
    } else {
      // SWITCH SELECTORS TO INPUTS

      // Replace WMS Layer Name
      slug_val = $('#id_wms_slug').val();
      $('#id_wms_slug').replaceWith('<input id="id_wms_slug" name="wms_slug" class="vTestField" maxlength="255" type="text" value="' + slug_val + '">' +
          '</input>');

      // Release lock on WMS version field
      $('.field-wms_version.field-box').show();

      // Replace WMS format
      format_val = $('#id_wms_format').val();
      $('#id_wms_format').replaceWith('<input class="vTextField" id="id_wms_format" maxlength="100" name="wms_format" type="text" value="' + format_val + '">' +
          '</input>');

      // Replace SRS
      srs_val = $('#id_wms_srs').val();
      $('#id_wms_srs').replaceWith('<input class="vTextField" id="id_wms_srs" maxlength="100" name="wms_srs" type="text" value="' + srs_val +'">' +
          '</input>');

      $('#id_wms_srs').blur(function() {
        if ($('#id_wms_srs').val() == 'EPSG:3857') {
          $('#id_wms_time_item').prop('disabled', true);
          $('#id_wms_additional').prop('disabled', false);
        } else {
          $('#id_wms_time_item').prop('disabled', false);
          $('#id_wms_additional').prop('disabled', true);
        }
      });

      // Replace Styles
      style_val = $('#id_wms_styles').val();
      $('#id_wms_styles').replaceWith('<input class="vTextField" id="id_wms_styles" maxlength="255" name="wms_styles" type="text" value="' + style_val + '">' +
          '</input>');

      // Replace Time
      $('#id_wms_timing').prop('disabled', false);
      $('#wms_timing_default').remove();
      $('#wms_timing_position_label').remove();
      $('#wms_timing_position_options').remove();

    }

    switch(layertype) {
      case '---------':
        break;
      case 'WMS':
        $('.field-wms_help').parent().removeClass('collapsed');
        $('.field-wms_help').parent().children('h2').children('a').text('Hide');
        break;
      default:
        break;
    }
  }
}

check_queryable = function(queryable_layers) {
  var selected_layer = $('#id_wms_slug').val();
  if (queryable_layers.indexOf(selected_layer) >= 0) {
    $('#id_wms_info').attr('disabled', false);
    $('#id_wms_info_format').attr('disabled', false);
  } else {
    $('#id_wms_info').attr('checked', false);
    $('#id_wms_info').attr('disabled', true);
    $('#id_wms_info_format').attr('disabled', true);
  }
  if (!$('#queryable_layer_list').length > 0) {
    if ($('.form-row.field-wms_info.field-wms_info_format').length > 0) {
      $('.form-row.field-wms_info.field-wms_info_format').append('<div id="queryable_layer_list"></div>');
    } else {
      console.log('need to re-write identification of WMS Info section of form. See layer_form.js "check_queryable()"');
    }
  }
  if ($('#queryable_layer_list').length > 0) {
    q_layers_html = "<b>Queryable Layers: </b>" + queryable_layers.join(', ');
    $('#queryable_layer_list').html(q_layers_html);
  }
}

$(document).ready(function() {
  show_layertype_form($('#id_layer_type option:selected').text());

  $('#id_layer_type').change(function() {
    show_layertype_form($('#id_layer_type option:selected').text());
  });

  $('#id_url').blur(function() {
    show_layertype_form($('#id_layer_type option:selected').text());
  });

  $('#id_wms_help').change(function() {
    show_layertype_form($('#id_layer_type option:selected').text());
  });

});
