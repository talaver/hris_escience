function deleteProductivityTool(prodtool){
    var $prodtool = $(prodtool)
    $prodtool.parent().remove()
    var id = $prodtool.data('id')

    $.ajax({
        url: 'productivity_tool_request/delete/' + id,
        method: 'DELETE',
        beforeSend: function(xhr){
            xhr.setRequestHeader('X-CSRFToken', csrf_token)
        }
    })
}
