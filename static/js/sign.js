$(document).ready(function() {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val();

    $("div.signForm form").submit(function(e) {
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
                // location.href = "/"
            },
            error: function(data){
                console.log(data)
                $("span.error_msg").text(data.responseJSON.message)

            }
        });


    })
    
    
});
