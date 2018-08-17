function success(result) {
    var res = document.getElementById("result");
    res.innerHTML = "";
    var suc = document.createElement("div");
    suc.className = "alert alert-success alert-dismissible";
    suc.innerHTML = "<button type='button' class='close' data-dismiss='alert'>&times;</button>" + result;
    res.appendChild(suc);
}

function error(result) {
    var res = document.getElementById("result");
    res.innerHTML = "";
    var suc = document.createElement("div");
    suc.className = "alert alert-danger alert-dismissible";
    suc.innerHTML = "<button type='button' class='close' data-dismiss='alert'>&times;</button>" + result;
    res.appendChild(suc);
}

function progress(result) {
    var res = document.getElementById("result");
    res.innerHTML = "";
    var suc = document.createElement("div");
    suc.className = "alert alert-warning alert-dismissible";
    suc.innerHTML = "<button type='button' class='close' data-dismiss='alert'>&times;</button>" + result;
    res.appendChild(suc);
}

function goto(href) {
    window.location = href;
}

function login() {
    $.ajax({
        url: '/login',
        type: 'post',
        dataType: 'json',
        data: { 
            login: $("#login").val(),
            password: $("#password").val()
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

function edit_profile() {
    var user = $("#edit_login").val();
    var password = $("#edit_password").val()
    if (password != $("#repeat_edit_password").val()){
        error("Паролі не однакові");
        return;
    }
    if (confirm("Ви впевнені, що хочете зберігти зміни профілю?")) {
        $.ajax({
            url: '/edit_user',
            type: 'post',
            dataType: 'json',
            data: {
                login: user,
                password: password,
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

function edit_text() {
    var quill = new Quill('#text', {
        modules: {
            imageResize: {
                modules: ['Resize', 'DisplaySize']
            },
            toolbar: [
                [{ header: [1, 2, 3, false] }],
                ['bold', 'italic', 'underline', { 'align': [] }, { 'color': [] }],
                ['link', 'blockquote', 'image'],
                [{ list: 'ordered' }, { list: 'bullet' }]
            ]
        },
        theme: 'snow',
        placeholder: 'Пишіть...'
    });
}

function upload_page() {
    $.ajax({
        url: '/upload_page',
        type: 'post',
        dataType: 'json',
        data: { 
            title: $("#page_title").val(),
            url: $("#page_url").val(),
            data: $(".ql-editor").html()
        },
        success: function(data) {
            if (data['ok']) {
                success(data['result']);
                window.location = "/admin/pages";
            }
            else {
                error(data['result']);
            }
        }
    });
}

function edit_page() {
    $.ajax({
        url: '/upload_page',
        type: 'post',
        dataType: 'json',
        data: { 
            id: $("#page_id").val(),
            title: $("#page_title").val(),
            url: $("#page_url").val(),
            data: $(".ql-editor").html()
        },
        success: function(data) {
            if (data['ok']) {
                success(data['result']);
                window.location = "/admin/pages";
            }
            else {
                error(data['result']);
            }
        }
    });
}

function delete_page(page_url) {
    if (confirm("Ви впевнені, що хочете видалити сторінку?")) {
        $.ajax({
            url: '/delete_page',
            type: 'post',
            dataType: 'json',
            data: {
                url: page_url
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

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();   
});