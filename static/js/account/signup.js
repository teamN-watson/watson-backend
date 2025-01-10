// 회원가입시 로딩화면 필요 > 오래걸림
$(document).ready(function() {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val();

    $("input[type='button']").click(function(e){
        if($(this).attr("name") == "next"){
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
                    "email" : $("input[name='email']").val(),
                    "step" : $("input[name='step']").val(),
                    "select_id" : []
                },
                success: function(data){
                    console.log(data)
                    $("div.signupStepForm").removeClass('step1');
                    $("div.signupStepForm").addClass('step2');
                    $("input[name='step']").val(2)
                },error: function(error){
                    console.log(error)
                    $(".error_msg").text("")
                    const keys = Object.keys(error.responseJSON)
                    if(keys.length){
                        for (let i = 0; i < keys.length; i++) {
                            var key = keys[i]
                            console.log(key)
                            $("p.error_msg."+key).text(error.responseJSON[keys[i]][0])   
                        }
                    } else {
                        $("span.error_msg").text(error.responseJSON.message)
                    }
                }
            })
        } 
        if($(this).attr("name") == "prev"){
            $("div.signupStepForm").removeClass('step2');
            $("div.signupStepForm").addClass('step1');
            $("input[name='step']").val(1)
        } 
    })

    $("div.signupForm form").submit(function(e) {
        e.preventDefault();
        const step = $("input[name='step']").val()
        if(step == 1){
            $("div.signupStepForm").removeClass('step1');
            $("div.signupStepForm").addClass('step2');
            $("input[name='step']").val(2)
            return;
        }
        const select_id = $(".interest_img.selected").map(function () {
            return $(".interest_img").index(this);
        }).get();
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
                "email" : $("input[name='email']").val(),
                "step" : $("input[name='step']").val(),
                "select_id" : select_id.join(", ")
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
                $(".error_msg").text("")
                if(data.responseJSON.length){
                    const keys = Object.keys(data.responseJSON)
                    for (let i = 0; i < keys.length; i++) {
                        console.log()
                        var key = keys[i]
                        $("p.error_msg."+key).text(data.responseJSON[keys[i]][0])   
                    }
                } else {
                    $("span.error_msg").text(data.responseJSON.message)
                }
                console.log(data)
                if(data.responseJSON.message && data.responseJSON.message.length){
                    $("span.error_msg").text(data.responseJSON.message[0])
                }
            }
        });
    })

    $.ajax({
        url: "/api/account/interest/",
        method: 'GET',
        success: function(data){
            console.log(data)

            const interest_list = $("div.interest_list")
            for (let i = 0; i < data.length; i++) {
                const interest = data[i];
                interest_list.append(`
                    <div class="interest_info">
                        <div class="interest_img">
                            <img src="/static/images/games/${interest.id}.jpg">
                        </div>
                    </div>`)
            }

            $("div.interest_info img").click(function(e){
                var parent = $(this).parent()

                if ($(parent).hasClass('selected')) {
                    $(parent).removeClass('selected'); // 선택 해제
                } else {
                    // $('.interest_img').removeClass('selected'); // 다른 요소 선택 해제
                    $(parent).addClass('selected'); // 클릭된 요소 선택
                }
            });
        },
        error: function(error){
            console.log(error)
        }
    })
    
});
