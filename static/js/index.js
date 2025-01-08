$(document).ready(function() {
    const access_token = sessionStorage.getItem('access_token')
    const refresh_token  = sessionStorage.getItem('refresh_token')

    if(access_token){
        fetchWithToken('/api/account/token/', {
            method: 'POST',
        }).then((data) => {
            console.log(data)
            const nav_auth = $('div.nav_auth');
            if(data.user_id !== undefined){
                if(data.photo !== ""){
                    nav_auth.append(`<div class="user_photo">
                        <img src="${data.photo}" />
                    </div>`);
                } else {
                    nav_auth.append(`<div class="user_photo">
                        <img src="/static/images/default_profile.png" />
                    </div>`);
                }
                nav_auth.append(`<h3>${data.user_id }님</h3>`);
                nav_auth.append(`<input type="button" class="logout" value="로그아웃">`);
                $("div.nav_auth input.logout").click(function(e){
                    logout();
                })
            }
        }).catch((error) => {
            console.error("Error creating account:", error.message); // 오류 처리
        });

    } else {
        const nav_auth = $('div.nav_auth');
        nav_auth.append(`<a href="/view/signin">로그인</a>`);
        nav_auth.append(`<a href="/view/signup">회원가입</a>`);       
    }

    function logout(){
        $.ajax({
            url: "/api/account/logout/",
            headers:{
                "Authorization": `Bearer ${access_token}`
            },
            data:{
                refresh_token: refresh_token
            },
            method: 'POST',
            success: function(data){     
                sessionStorage.removeItem('access_token')
                sessionStorage.removeItem('refresh_token')
                location.href = "/"                
            },
            error: function(data){
                console.log(data)
            }
        });
    }

    async function fetchWithToken(url, options = {}) {
    
        options.headers = {
            ...options.headers,
            Authorization: `Bearer ${access_token}`,
        };

        let response = await fetch(url, options);

        // 2. Access Token 만료로 인해 401 응답이 온 경우
        if (response.status === 401 && refresh_token) {

            console.log("토큰이 만료되어 재발급합니다.");
            const refreshResponse = await fetch('/api/token/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refresh_token }),
            });
    
            if (refreshResponse.ok) {
                const data = await refreshResponse.json();
                const newAccessToken = data.access_token;
    
                // 3. 새 Access Token 저장
                localStorage.setItem("access_token", newAccessToken);
    
                // 4. 원래 요청 다시 시도
                options.headers.Authorization = `Bearer ${newAccessToken}`;
                response = await fetch(url, options);
            } else {
                console.error("Refresh 토큰이 만료되었습니다.");
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                // 로그아웃 처리 필요
            }
        }
    
        return response.json();
    }

});
