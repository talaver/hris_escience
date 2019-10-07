function deleteOvertime(ots){
    var $ots = $(ots)
    $ots.parent().remove()
    var id = $ots.data('id')

    $.ajax({
        url: 'overtime_request/delete/' + id,
        method: 'DELETE',
        beforeSend: function(xhr){
            xhr.setRequestHeader('X-CSRFToken', csrf_token)
        }
    })
}
