function deleteUndertime(uts){
    var $uts = $(uts)
    $uts.parent().remove()
    var id = $uts.data('id')

    $.ajax({
        url: 'undertime_request/delete/' + id,
        method: 'DELETE',
        beforeSend: function(xhr){
            xhr.setRequestHeader('X-CSRFToken', csrf_token)
        }
    })
}
