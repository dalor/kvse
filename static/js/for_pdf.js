function upload_pdf() {
    var files = $('#pdf_up').prop('files');
    var data = new FormData();
    $.each(files, function(key, value)
    {
        data.append(key, value);
    });
    progress("Завантаження...");
    $.ajax({
        url: '/upload_pdf',
        dataType: 'json',
        contentType: false,
        processData: false,
        data: data,
        type: 'post',
        success: function(data) {
            if (data['ok']) {
                success(data['result']);
                my_files();
            }
            else {
                error(data['result']);
            }
        }
    });
};

function my_files() {
    $.ajax({
        url: '/admin/my_files',
        dataType: 'json',
        type: 'get',
        success: function(data) {
            if (data['ok']) {
                var my_files = document.getElementById('my_files');
                my_files.innerHTML = "";
                var results = data['result'];
                for (var i = 0, ln = results.length; i < ln; i++) {
                    var a = document.createElement('a');
                    var one = results[i];
                    a.href = '/file/' + one;
                    a.title = one;
                    a.innerHTML = one;
                    my_files.appendChild(a);
                }
            }
            else {
                error(data['result']);
            }
        }
    });
}