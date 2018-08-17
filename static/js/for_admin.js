function delete_more(e) {
    e.parentNode.parentNode.parentNode.parentNode.removeChild(e.parentNode.parentNode.parentNode);
}

function delete_less(e) {
    e.parentNode.parentNode.removeChild(e.parentNode);
}

function paste_item(e) {
    var item = document.getElementById("menu-item-to-copy").cloneNode(true);
    item.id = "menu-item";
    e.parentNode.appendChild(item);
}

function paste_small_item(e) {
    var item = document.getElementById("menu-small-item-to-copy").cloneNode(true);
    item.id = "menu-small-item";
    e.parentNode.appendChild(item);
}

function make_list(e) {
    var item = document.getElementById("menu-list-to-copy").cloneNode(true);
    item.id = "menu-list";
    var put_element = e.parentNode.parentNode.parentNode.querySelector("#put");
    put_element.innerHTML = "";
    put_element.appendChild(item);
    make_sortable();
}

function make_url(e) {
    var item = document.getElementById("menu-url-to-copy").cloneNode(true);
    item.id = "menu_url";
    var put_element = e.parentNode.parentNode.parentNode.querySelector("#put");
    put_element.innerHTML = "";
    put_element.appendChild(item);
}

function make_sortable() {
    $(".sortable").sortable();
}

function send() {
    var info = [];
    $("li#menu-item").each(function(index, val){
        var item = {};
        var element = $(val);
        var value = element.find("#menu_item").val();
        var data;
        if (element.find("#put").children().is("ul")){
            data = [];
            $("li#menu-small-item", element).each(function(sindex, sval){
                s_element = $(sval);
                var small_item = {};
                small_item['name'] = s_element.find("#menu_small_item").val();
                small_item['url'] = s_element.find("#menu_small_url").val();
                data.push(small_item);
            })
            item['is_list'] = true;
        }
        else {
            item['is_list'] = false;
            data = element.find("#menu_url").val();
        }
        item['name'] = value;
        item['data'] = data;
        info.push(item);
    })
    $.ajax({
        url: '/save_menu',
        type: 'post',
        dataType: 'json',
        data: { data: JSON.stringify(info) },
        success: function(data) {
            if (data['ok']) {
                success(data['result']);
            }
            else {
                error(data['result']);
            }
        }
    });
}

function reg_user() {
    $.ajax({
        url: '/reg_user',
        type: 'post',
        dataType: 'json',
        data: { 
            login: $("#small_login").val(),
            password: $("#small_password").val()
        },
        success: function(data) {
            if (data['ok']) {
                success(data['result']);
                window.location.reload();
            }
            else {
                error(data['result']);
            }
        }
    });
}

function edit_user(e) {
    var parent = $(e).parent().parent();
    var user = $("#edit_login", parent).val();
    if (confirm("Ви впевнені, що хочете відредагувати користувача " + user + "?")) {
        $.ajax({
            url: '/edit_user',
            type: 'post',
            dataType: 'json',
            data: {
                id: $("#edit_id", parent).val(),
                login: user,
                password: $("#edit_password", parent).val(),
                is_admin: function() {
                    if ($("#is_admin:checked", parent).val()) {
                        return true;
                    }
                    else {
                        return false;
                    }
                }
            },
            success: function(data) {
                if (data['ok']) {
                    success(data['result']);
                }
                else {
                    error(data['result']);
                }
            }
        });
    }
}

function delete_user(e) {
    var parent = $(e).parent().parent();
    var user = $("#edit_login", parent).val();
    if (confirm("Ви впевнені, що хочете видалити користувача " + user + "?")) {
        $.ajax({
            url: '/delete_user',
            type: 'post',
            dataType: 'json',
            data: {
                id: $("#edit_id", parent).val()
            },
            success: function(data) {
                if (data['ok']) {
                    success(data['result']);
                    window.location.reload();
                }
                else {
                    error(data['result']);
                }
            }
        });
    }
}

$(document).ready(function() {
    make_sortable();
});
