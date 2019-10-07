function deleteChangeOfWorkSchedule(cow){
    var $cow = $(cow)
    $cow.parent().remove()
    var id = $cow.data('id')

    $.ajax({
        url: 'change_of_work_schedule_request/delete/' + id,
        method: 'DELETE',
        beforeSend: function(xhr){
            xhr.setRequestHeader('X-CSRFToken', csrf_token)
        }
    })
}
