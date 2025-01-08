$(document).ready(function() {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val();

    $("div.signinForm form").submit(function(e) {
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
    $("div.signupForm form").submit(function(e) {
        e.preventDefault();
        $.ajax({
            url: "/api/account/signup/",
            headers:{
                "X-CSRFToken": csrftoken
            },
            method: 'POST',
            data: {
                "user_id" : $("input[name='user_id']").val(),
                "password" : $("input[name='password']").val(),
                "confirm_password" : $("input[name='confirm_password']").val(),
                "age" : $("input[name='age']").val(),
                "nickname" : $("input[name='nickname']").val(),
                "email" : $("input[name='email']").val()
            },
            success: function(data){
                console.log(data)
                if(data.access_token){
                    localStorage.setItem('access_token', data.access_token);
                }
                if(data.refresh_token){
                    localStorage.setItem('refresh_token', data.refresh_token);
                }
                // location.href = "/"
            },
            error: function(data){
                $(".error_msg").text("")
                if(data.responseJSON){
                    const keys = Object.keys(data.responseJSON)
                    for (let i = 0; i < keys.length; i++) {
                        console.log()
                        var key = keys[i]
                        $("p.error_msg."+key).text(data.responseJSON[keys[i]][0])
                        
                    }

                }
                console.log(data)
                if(data.responseJSON.message && data.responseJSON.message.length){
                    $("span.error_msg").text(data.responseJSON.message[0])
                }
            }
        });
    })
    
});
