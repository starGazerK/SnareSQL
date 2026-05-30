
var currentList = {};
// 显示的字段
function searchSelect(id , table , keyword , where , fields,ext , callback) {
    where = where || {};
    if(keyword && keyword != ''){
        var fs = ext && $.isArray(ext) ? fields.concat(ext) : fields;
        where[fs.join('|')] = ['like' , "%"+keyword+"%"];
    }

    var value = $('#'+id).data('value');
    //var fields = $('#'+id).data('fields');
    fields = $.isArray(fields) ? fields : fields.split(',');

    $.post( window.searchSelectUrl , {
        table:table,
        where:JSON.stringify(where)
    },function (res) {
        var sel = document.getElementById(id);
        sel.length = 1;
        sel.selectedIndex = 0;
        var values = null;
        $.each(res , function (index,obj) {
            var option = document.createElement('option');
            option.value = obj.id;
            var text = [];
            $.each(fields , function (i , o) {
                var inputs = $('[id="'+o+'"]');
                if(inputs.length > 0){
                    var tagName = inputs[0].tagName.toLocaleLowerCase();
                    if(tagName == 'select'){
                        // select 需要从select 中取指
                        var t = inputs.find('option[value="'+obj[o]+'"]').text();
                        text.push(t);
                    }else if(tagName == 'radio'){
                        // 单选框
                        inputs.each(function () {
                            if(this.value == obj[o]){
                                text.push($(this).parent().text());
                            }
                        });
                    }else if(tagName == 'checkbox'){
                        var os = obj[o].split(',');
                        var ts = [];
                        inputs.each(function () {
                            if($.inArray(this.value,os)){
                                ts.push($(this).parent().text());
                            }
                        });
                        text.push(ts.join(','));
                    }else{
                        text.push(obj[o]);
                    }
                }
            });
            if(value && value == obj.id){
                option.selected = true
                values = obj;
            }
            if(!currentList[table]){
                currentList[table] = {};
            }
            currentList[table][obj.id] = obj;
            option.text = text.join(" - ");
            sel.options.add(option);
        });
        callback && callback(res);
        if(window.layui){
            layui.use("form" , function (){
                var form = layui.form;
                form.render();
            })
        }
        if(values !== null){
            $(function () {
                setAjaxData(fields , values)
            });
        }
    },'json');
}

function setAjaxData(fields , res) {
    $.each(fields, function (i, name) {
        var inputs = $("[id='"+name+"']");
        if(inputs.length > 0){
            var tagName = inputs[0].tagName.toLocaleLowerCase();

            var type = inputs.attr('type');

            if (res[name]) {
                if(tagName == 'input')
                {
                    var type = $("#" + name).attr('type');
                    if(type == 'checkbox'){
                        // 多选
                        var checkboxs = $("input[name='" + name+"']:checkbox");
                        checkboxs.prop('checked' , false);
                        var arr = res[name].split(',');
                        checkboxs.each(function () {
                            if($.inArray(this.value , arr)){
                                $(this).prop('checked' , true);
                            }
                        });
                    }else if(type == 'radio'){
                        var radio = $("input[name='" + name+"']:radio");
                        radio.prop('checked' , false);
                        var val = res[name];
                        radio.each(function () {
                            if(this.value == val){
                                $(this).prop('checked' , true);
                            }
                        });
                    }else{
                        $("#" + name).val(res[name]);
                    }
                }else if(tagName == 'select'){
                    $("#" + name).val(res[name]);
                }else{
                    $("#" + name).val(res[name]);
                }
            }else if(res[name+'_id']){
                $("#" + name).val(res[name+'_id']);
            }else{
                if(tagName == 'input' && type == 'checkbox'){
                    $("input[name='" + name+"']:checkbox").val([]);
                }else{
                    $("#" + name).val('');
                }
            }
        }

    });
    updateFieldText(fields)
}


function updateFieldText( fields ) {
    // 将值写入到span 中
    $.each(fields, function (i,name) {
        var input = $('[id="'+name+'"]');
        if(input.length > 0){
            var tagName = input[0].tagName.toLocaleLowerCase();
            if(tagName == 'input'){
                var type = input.attr('type');
                var type = $("#" + name).attr('type');
                if(type == 'checkbox' || type == 'radio'){
                    // 多选
                    var result = [];
                    $("input[name='" + name+"']:checked").each(function () {
                        var v = $(this).parent().text();
                        v = $.trim(v);
                        result.push(v);
                    });
                    input.parents('.select-update').next().html(result.join(" "));
                }else{
                    input.next().html(input.val());
                }

            }else if(tagName == 'select'){
                var text = input.find('option:selected').text();
                input.next().html(text);
            }
        }
    });
}

function getAjaxData( table, sel , destId ) {
    var tab = $(sel);
    var fields = tab.data('fields');

    fields = $.isArray(fields) ? fields : fields.split(",")
    if (!destId || destId == "") {
        setAjaxData(fields , {});
        return;
    }

    var data = currentList[table][destId];
    setAjaxData(fields , data || {});
}


function setFieldData(fields , res) {
    fields = $.isArray(fields) ? fields : fields.split(",")
    $.each(fields, function (i, name) {
        if (res[name]) {
            $("#" + name).val(res[name]);
        }
    });
}

$(function () {
    $('.select-update').hide().after('<span class="showData"></span>');
});


