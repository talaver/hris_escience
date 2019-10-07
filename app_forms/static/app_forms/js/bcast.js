function deleteBcast(bcast){
    var $bcast = $(bcast)
    $bcast.parent().remove()
    var id = $bcast.data('id')

    $.ajax({
        url: 'dashboard/delete/' + id,
        method: 'DELETE',
        beforeSend: function(xhr){
            xhr.setRequestHeader('X-CSRFToken', csrf_token)
        }
    })
}
