$(document).ready(function() {
    const access_token = sessionStorage.getItem('access_token')

    $.ajax({
        url: "/api/account/mypage/",
        headers:{
            "Authorization": `Bearer ${access_token}`
        },
        method: 'GET',
        success: function(data){
            const user_photo = $('div.mypageContainer div.user_photo');
            const profile = data.profile;
            if(profile.photo == null || profile.photo == ""){
                user_photo.append(`<img src="/static/images/default_profile.png" />`)
            }else{
                user_photo.append(`<img src="/media/${profile.photo}" />`)
            }
            const user_info = $('div.mypageContainer div.user_info');

            user_info.append(`<p id="user_user_id">아이디 : ${profile.user_id}</p>`)
            user_info.append(`<p id="user_email">이메일 : ${profile.email}</p>`)
            user_info.append(`<p id="user_nickname">닉네임 : ${profile.nickname}</p>`)
            user_info.append(`<p id="user_age">나이 : ${profile.age}</p>`)

            if(profile.steamId == null || profile.steamId == ""){
            user_info.append(`<a href="/view/steam/login/?user_id=${profile.user_id}" class="btn btn-steam-login">
                Login with Steam
            </a>`)
            } else {
                user_info.append(`<p id="user_steamId">스팀ID : ${profile.steamId}</p>`)
            }
            

            console.log(data)
            
        },
        error: function(data){
            console.log(data)
        }
    });
});
