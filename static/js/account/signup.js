function prev_action(){
    const step = $("input[name='step']").val()*1
    $("div.signupStepForm").removeClass("step"+step);
    $("div.signupStepForm").addClass("step"+(step-1));
    $("input[name='step']").val(step-1)
}
function next_action(){
    const step = $("input[name='step']").val()*1
    $("div.signupStepForm").removeClass("step"+step);
    $("div.signupStepForm").addClass("step"+(step+1));
    $("input[name='step']").val(step+1)
}
function error_action(error){
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
// 회원가입시 로딩화면 필요 > 오래걸림
$(document).ready(function() {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val();
    
    $("input[type='button']").click(function(e){
        $(".error_msg").text("")
        if($(this).attr("name") == "next"){
            const step = $("input[name='step']").val()
            if(step == 1){
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
                        "step" : $("input[name='step']").val(),
                    },
                    success: function(data){
                        console.log(data)
                        next_action()
                    },error: function(error){
                        console.log(error)
                        error_action(error)
                    }
                })
                
            } else if(step == 2){
                $.ajax({
                    url: "/api/account/signup/",
                    headers:{
                        "X-CSRFToken": csrftoken
                    },
                    method: 'POST',
                    data: {
                        "age" : $("input[name='age']").val(),
                        "nickname" : $("input[name='nickname']").val(),
                        "email" : $("input[name='email']").val(),
                        "step" : $("input[name='step']").val(),
                    },
                    success: function(data){
                        console.log(data)
                        next_action()
                    },error: function(error){
                        console.log(error)
                        error_action(error)
                    }
                })
            }
            
        } 
        if($(this).attr("name") == "prev"){
            prev_action()
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
        } else if(step == 2){
            $("div.signupStepForm").removeClass('step3');
            $("div.signupStepForm").removeClass('step1');
            $("div.signupStepForm").addClass('step2');
            $("input[name='step']").val(2)
            return;
        }
        const select_id = $(".interest_img.selected").map(function () {
            return $(".interest_img").index(this);
        }).get();
        var formData = new FormData();
        formData.append("user_id", $("input[name='user_id']").val());
        formData.append("password", $("input[name='password']").val());
        formData.append("confirm_password", $("input[name='confirm_password']").val());
        formData.append("age", $("input[name='age']").val());
        formData.append("nickname", $("input[name='nickname']").val());
        formData.append("email", $("input[name='email']").val());
        formData.append("step", $("input[name='step']").val());
        formData.append("select_id", select_id.join(", "));
        formData.append("photo", $("#id_photo")[0].files[0]);  // 이미지 파일 추가

        $.ajax({
            url: "/api/account/signup/",
            headers: {
                "X-CSRFToken": csrftoken
            },
            method: 'POST',
            data: formData,
            processData: false,  // FormData를 사용하면 jQuery가 자동으로 데이터를 변환하지 않게 해야 함
            contentType: false,  // 자동으로 콘텐츠 유형을 설정하지 않게 해야 함
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
    

     // 이미지 미리보기
     $("div.signupStep1 input#id_photo").change(function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();

            reader.onload = function(e) {
                $(".signupStep1 .user_photo_wrap img").attr("src", e.target.result).show();
            };

            reader.readAsDataURL(file);
        }
    });

    // 이미지 영역 클릭시 input file 활성화
    $("img#user_photo").click(function(event){
        $("input#id_photo").click();
    })
});
