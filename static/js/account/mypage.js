$(document).ready(function() {
    const access_token = sessionStorage.getItem('access_token')

    $.ajax({
        url: "/api/account/mypage/",
        headers:{
            "Authorization": `Bearer ${access_token}`
        },
        method: 'GET',
        success: function(response){
            console.log(response)
            const user_photo = $('div.mypageContainer div.user_photo');
            const profile = response.data.profile_data;
            if(profile.photo == null || profile.photo == ""){
                user_photo.append(`<img src="/static/images/default_profile.png" />`)
            }else{
                user_photo.append(`<img src="/media/${profile.photo}" />`)
            }
            const animated_avatar = response.data.animated_avatar;
            user_photo.append(`<img src="https://cdn.fastly.steamstatic.com/steamcommunity/public/images/${animated_avatar.avatar.image_small}" />`)

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
            const owned_games = response.data.owned_games;
            const div_owned_games = $("div.owned_game")
            for (let i = 0; i < owned_games["games"].length; i++) {
                const game = owned_games["games"][i]
                const date = new Date(game.rtime_last_played * 1000); // 밀리초로 변환

                // 날짜를 YYYY년 mm월 dd일 형식으로 변환
                const formattedDate = `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;

                div_owned_games.append(`<div>
                    <img src="https://avatars.fastly.steamstatic.com/${game.img_icon_url}.jpg">
                    <span>${game.name}</span>
                    <span>${(game.playtime_forever/60).toFixed(1)}시간</span>
                    <span>최근 플레이${formattedDate}</span>
                    </div>`)                
            }
            
            const recent_games = response.data.recent_games;
            const div_recent_games = $("div.recent_game")
            for (let i = 0; i < recent_games["games"].length; i++) {
                const game = recent_games["games"][i]

                div_recent_games.append(`<div>
                    <img src="https://avatars.fastly.steamstatic.com/${game.img_icon_url}.jpg">
                    <span>${game.name}</span>
                    <span>총 플레이타임${(game.playtime_forever/60).toFixed(1)}시간</span>
                    <span>지난 2주간 플레이타임${(game.playtime_2weeks/60).toFixed(1)}시간</span>
                    </div>`)                
            }

            
        },
        error: function(data){
            console.log(data)
        }
    });
});
