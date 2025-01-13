$(document).ready(function() {
    const access_token = sessionStorage.getItem('access_token')
    $("div.rCreateContainer form").submit(function(e) {
        e.preventDefault();
        $.ajax({
            url: "/api/reviews/",
            headers:{
                "Authorization": `Bearer ${access_token}`
            },
            method: 'POST',
            data: {
                "title": $("input[name='title']").val(),
                "content": $("textarea[name='content']").val(),
                "app_id": $("input[name='app_id']").val(),
                "score": $("input[name='score']").val(),
                "categories": $("input[name='categories']").val(),
            },
            success: function(data){
                console.log(data)
            },
            error: function(data){
                console.log(data)
            }
        });
    })   
});
