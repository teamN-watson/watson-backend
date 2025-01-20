$(document).ready(function() {
    const access_token = sessionStorage.getItem('access_token')

    function steam_profile_action(){
        if(confirm("스팀 프로필 이미지를 가져오시겠습니까?")){
            $.ajax({
                url: "/api/account/steam_profile/",
                headers:{
                    "Authorization": `Bearer ${access_token}`
                },
                method: 'GET',
                success: function(response){
                    location.reload()
                },error: function(error){
                    console.log(error)
                }
            })
        }
    }
    function get_profile(access_token){
        id = $("input[name='id']").val()
        const headers = {}
        if (access_token) {
            headers["Authorization"] = `Bearer ${access_token}`;
        }

        $.ajax({
            url: "/api/account/profile/",
            headers:headers,
            data: {
                id: id
            },
            method: 'GET',
            success: function(response){
                console.log(response)
                is_mypage = response.data.is_mypage
                const user_photo = $('div.profileContainer div.user_photo');
                const profile = response.data.profile_data;
                if(profile.photo == null || profile.photo == ""){  // 사용자 프로필
                    user_photo.append(`<img src="/static/images/default_profile.png" />`)
                }else{
                    photo = profile.photo.split("/").splice(2)
                    if(photo[0] == "items"){
                        user_photo.append(`<img src="https://cdn.fastly.steamstatic.com/steamcommunity/public/images/${photo.join("/")}" />`)
                    } else {
                        user_photo.append(`<img src="${profile.photo}" />`)
                    }
                }

                // 사용자 정보
                const user_info = $('div.profileContainer div.user_info');
                if(is_mypage){
                    user_info.append(`<a href="/view/edit/"><button>편집하기</button></a>`)
                }

                user_info.append(`<p id="user_user_id">아이디 : ${profile.user_id}</p>`)
                user_info.append(`<p id="user_email">이메일 : ${profile.email}</p>`)
                user_info.append(`<p id="user_nickname">닉네임 : ${profile.nickname}</p>`)
                user_info.append(`<p id="user_age">나이 : ${profile.age}</p>`)

                // 스팀 정보
                if(profile.steamId != null && profile.steamId != ""){
                    user_info.append(`<p id="user_steamId">스팀ID : ${profile.steamId}</p>`)
                } 
                if (is_mypage) {
                    
                    if(profile.steamId != null && profile.steamId != ""){
                        user_info.append(`<input type="button" name="steam_profile" class="steam_profile" value="스팀 프로필 이미지 가져오기">`)
                        $("input[name='steam_profile']").click(steam_profile_action);
                    } else {
                        user_info.append(`<a href="/view/steam/login/?user_id=${profile.user_id}" class="btn btn-steam-login">Login with Steam</a>`)

                    }
                }
                // if(profile.steamId == null || profile.steamId == ""){
                // user_info.append(`<a href="/view/steam/login/?user_id=${profile.user_id}" class="btn btn-steam-login">
                //     Login with Steam
                // </a>`)
                // } else {
                //     user_info.append(`<p id="user_steamId">스팀ID : ${profile.steamId}</p>`)
                //     user_info.append(`<input type="button" name="steam_profile" class="steam_profile" value="스팀 프로필 이미지 가져오기">`)
                //     $("input[name='steam_profile']").click(steam_profile_action);
                // }
                const owned_games = response.data.owned_games;
                if(owned_games !== undefined){
                    const div_owned_games = $("div.owned_game")
                    for (let i = 0; i < owned_games["games"].length; i++) {
                        const game = owned_games["games"][i]
                        const date = new Date(game.rtime_last_played * 1000); 

                        // 날짜를 YYYY년 mm월 dd일 형식으로 변환
                        const formattedDate = `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;

                        div_owned_games.append(`<div>
                            <img src="https://avatars.fastly.steamstatic.com/${game.img_icon_url}.jpg">
                            <span>${game.name}</span>
                            <span>${(game.playtime_forever/60).toFixed(1)}시간</span>
                            <span>최근 플레이${formattedDate}</span>
                            </div>`)                
                    }
                }
                
                const recent_games = response.data.recent_games;
                const div_recent_games = $("div.recent_game")
                if(recent_games !== undefined){
                    for (let i = 0; i < recent_games["games"].length; i++) {
                        const game = recent_games["games"][i]

                        div_recent_games.append(`<div>
                            <img src="https://avatars.fastly.steamstatic.com/${game.img_icon_url}.jpg">
                            <span>${game.name}</span>
                            <span>총 플레이타임${(game.playtime_forever/60).toFixed(1)}시간</span>
                            <span>지난 2주간 플레이타임${(game.playtime_2weeks/60).toFixed(1)}시간</span>
                            </div>`)                
                    }
                }

                
            },
            error: function(error){
                console.log(error)
            }
        });
    }
    get_profile(access_token)
});
