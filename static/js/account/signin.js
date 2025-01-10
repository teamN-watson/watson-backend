$(document).ready(function() {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val();

    $("div.signContainer form").submit(function(e) {
        e.preventDefault();
        user_id = $("input[name='user_id']").val()
        password = $("input[name='password']").val()
        $.ajax({
            url: "/api/account/signin/",
            headers:{
                "X-CSRFToken": csrftoken
            },
            method: 'POST',
            data: {
                "user_id": user_id,
                "password": password
            },
            success: function(data){
                console.log(data)
                if(data.access_token){
                    sessionStorage.setItem('access_token', data.access_token);
                }
                if(data.refresh_token){
                    sessionStorage.setItem('refresh_token', data.refresh_token);
                }
                location.href = "/"
            },
            error: function(data){
                console.log(data)
                $("span.error_msg").text(data.responseJSON.message)
            }
        });
    })    
});
