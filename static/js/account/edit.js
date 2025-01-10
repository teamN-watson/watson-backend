function get_user(access_token){
    $.ajax({
        url: "/api/account/mypage/",
        headers:{
            "Authorization": `Bearer ${access_token}`
        },
        method: 'GET',
        success: function(response){
            console.log(response)
            const user = response.data.profile_data
            $("input[name='age']").val(user.age)
            $("input[name='nickname']").val(user.nickname)
            $("input[name='email']").val(user.email)
            if(user.photo !== "" && user.photo !== null){
                $("img#user_photo").attr("src", user.photo)
            }
        },
        error: function(error){
            console.log(error)
        }
    })
}
$(document).ready(function() {
    const access_token = sessionStorage.getItem('access_token')
    get_user(access_token);
    var csrftoken = $("[name=csrfmiddlewaretoken]").val();
    $("div.editContainer form").submit(function(e) {
        e.preventDefault();
        
        var formData = new FormData();
        formData.append("age", $("input[name='age']").val());
        formData.append("nickname", $("input[name='nickname']").val());
        formData.append("email", $("input[name='email']").val());
        if($("#id_photo")[0].files.length){
            formData.append("photo", $("#id_photo")[0].files[0]);  // 이미지 파일 추가
        }

        $.ajax({
            url: "/api/account/mypage/",
            headers: {
                "X-CSRFToken": csrftoken,
                "Authorization": `Bearer ${access_token}`
            },
            method: 'PUT',
            data: formData,
            processData: false,  // FormData를 사용하면 jQuery가 자동으로 데이터를 변환하지 않게 해야 함
            contentType: false,  // 자동으로 콘텐츠 유형을 설정하지 않게 해야 함
            success: function(data){
                console.log(data)
                location.href = "/view/mypage"
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
    

     // 이미지 미리보기
     $("div.editForm input#id_photo").change(function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();

            reader.onload = function(e) {
                $(".editForm .user_photo_wrap img").attr("src", e.target.result).show();
            };

            reader.readAsDataURL(file);
        }
    });

    // 이미지 영역 클릭시 input file 활성화
    $("img#user_photo").click(function(event){
        $("input#id_photo").click();
    })
});
