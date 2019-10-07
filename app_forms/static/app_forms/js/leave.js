function deleteLeave(leave){
    var $leave = $(leave)
    $leave.parent().remove()
    var id = $leave.data('id')

    $.ajax({
        url: 'leave_request/delete/' + id,
        method: 'DELETE',
        beforeSend: function(xhr){
            xhr.setRequestHeader('X-CSRFToken', csrf_token)
        }
    })
}
