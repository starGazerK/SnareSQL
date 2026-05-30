
function ajaxTodo(url, tabid) {
    //var $callback = callback;
    //if (!$.isFunction($callback)) $callback = eval('(' + callback + ')');

    $.ajax({
        type: 'GET',
        url: url,
        dataType: "json",
        cache: false,
        success: function (data) {
            
            if (data.statusCode == 200)
                showalert(data.message);
            else
                showalert(data.message, 1);
            
            if (tabid) {
                $(tabid).bootstrapTable('refresh')
            }
            //callback;
        },
        error: function (data) { showalert(data.message, 1); }
    });
}

$('.ajaxtodo').click(function (event) {

    $this = $(this)
    event.preventDefault();
    var url = ($this.attr("href"));
    var title = $this.attr("title");

    if (title) {
        if (confirm(title) == false)
            return false;
    };
    ajaxTodo(url, $this.attr("callback"));
    return false;

});

function showmodel(mdname, url) {
    //console.info('open '+url)
    // 打开模态框

    $.ajax({
        url: url,
        type: 'GET',
        cache: false,

    }).done(function (result) {
        $(mdname).html(result)
        $(mdname).modal('show') //part of bootstrap.min.js
    });
}

$('#myModal').on('hide.bs.modal', function () {
    $(this).empty();
});

function getselect_id() {
    var ids = "";
    var rows = $('#table').bootstrapTable('getSelections');
    if (rows.length == 0) {
        showalert("请选择需要操作的记录",1);
        return;
    } else
        ids = rows[0].id
    return ids;
}

function getselect_data() {
    var ids = "";
    var rows = $('#table').bootstrapTable('getSelections');
    if (rows.length == 0) {
        showalert("请选择需要操作的记录",1);
        return;
    } else
        ids = rows[0]
    return ids;
}

//打印表格
var idTmr;
function getExplorer() {
    var explorer = window.navigator.userAgent;
    //ie  
    if (explorer.indexOf("MSIE") >= 0) {
        return 'ie';
    }
    //firefox  
    else if (explorer.indexOf("Firefox") >= 0) {
        return 'Firefox';
    }
    //Chrome  
    else if (explorer.indexOf("Chrome") >= 0) {
        return 'Chrome';
    }
    //Opera  
    else if (explorer.indexOf("Opera") >= 0) {
        return 'Opera';
    }
    //Safari  
    else if (explorer.indexOf("Safari") >= 0) {
        return 'Safari';
    }
}

function method5(tableid) {
    if (getExplorer() == 'ie') {
        var curTbl = document.getElementById(tableid);
        var oXL = new ActiveXObject("Excel.Application");
        var oWB = oXL.Workbooks.Add();
        var xlsheet = oWB.Worksheets(1);
        var sel = document.body.createTextRange();
        sel.moveToElementText(curTbl);
        sel.select();
        sel.execCommand("Copy");
        xlsheet.Paste();
        oXL.Visible = true;

        try {
            var fname = oXL.Application.GetSaveAsFilename("Excel.xls",
                "Excel Spreadsheets (*.xls), *.xls");
        } catch (e) {
            print("Nested catch caught " + e);
        } finally {
            oWB.SaveAs(fname);
            oWB.Close(savechanges = false);
            oXL.Quit();
            oXL = null;
            idTmr = window.setInterval("Cleanup();", 1);
        }

    } else {
        tableToExcel(tableid)
    }
}

function Cleanup() {
    window.clearInterval(idTmr);
    CollectGarbage();
}
var tableToExcel = (function () {
    var uri = 'data:application/vnd.ms-excel;base64,',
        template = '<html><head><meta charset="UTF-8"></head><body><table  border="1">{table}</table></body></html>',
        base64 = function (
            s) {
            return window.btoa(unescape(encodeURIComponent(s)))
        },
        format = function (s, c) {
            return s.replace(/{(\w+)}/g, function (m, p) {
                return c[p];
            })
        }
    return function (table, name) {
        if (!table.nodeType)
            table = document.getElementById(table)
        var ctx = {
            worksheet: name || 'Worksheet',
            table: table.innerHTML
        }
        window.location.href = uri + base64(format(template, ctx))
    }
})()

/*格式化日期格式*/
function changeDateFormat(cellval) {
    
    if (cellval != null) {
        var date = new Date(cellval);
        var month = date.getMonth() + 1 < 10 ? "0" + (date.getMonth() + 1) : date.getMonth() + 1;
        var currentDate = date.getDate() < 10 ? "0" + date.getDate() : date.getDate();
        var hour = date.getHours()  < 10 ? "0"+(date.getHours()) : date.getHours();
        var min =  date.getMinutes()  < 10 ? "0"+(date.getMinutes()) : date.getMinutes();
        var seon = date.getSeconds() < 10 ? "0"+(date.getSeconds()) : date.getSeconds();
        return date.getFullYear() + "-" + month + "-" + currentDate +" "+ hour +":"+ min +":"+ seon;
    }
}