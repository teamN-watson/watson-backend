const axiosInstance = axios.create({
    baseURL: '/api',
});

// 요청 인터셉터 추가
axiosInstance.interceptors.request.use((config) => {
    const access_token = sessionStorage.getItem('access_token');
    
    // 토큰이 필요한 요청인지 체크
    if (access_token && !config.noAuthRequired) {
        config.headers['Authorization'] = `Bearer ${access_token}`;
    }

    return config;
}, (error) => {
    return Promise.reject(error);
});

// 토큰이 필요한 요청이 아닌 경우에 사용
function makeRequestWithoutToken(url, method = 'GET', data = null) {
    return axiosInstance({
        method,
        url,
        data,
        noAuthRequired: true // 토큰을 필요로 하지 않는 요청에 대한 플래그 설정
    });
}

// 토큰이 필요한 요청을 보내는 함수
function makeRequest(url, method = 'GET', data = null) {
    if (!sessionStorage.getItem('access_token')) {
        // access_token이 없으면 로그인 페이지로 리다이렉트
        window.location.href = '/view/signin';
        return;
    }

    return axiosInstance({
        method,
        url,
        data
    });
}

$(document).ready(function() {
    function add_signwrap(){
        const nav_auth = $('div.nav_auth');
        nav_auth.append(`<a href="/view/signin">로그인</a>`);
        nav_auth.append(`<a href="/view/signup">회원가입</a>`);
    }


    // 요청 인터셉터 (요청 전에 실행)
    const access_token = sessionStorage.getItem('access_token');
    const refresh_token = sessionStorage.getItem('refresh_token');
    const nav_auth = $('div.nav_auth');

    let isRefreshing = false;  // 토큰 갱신 중인지 여부
    let refreshQueue = []; // 토큰 갱신을 기다리는 요청 큐

    axiosInstance.interceptors.response.use((response) => {
        return response;
    }, async (error) => {
        const originalRequest = error.config;  // 원래 요청의 설정

        // 401 상태 코드 (토큰 만료)
        if (error.response.status === 401 && refresh_token && !isRefreshing) {
            isRefreshing = true; // 토큰 갱신 중임을 표시
            console.log("토큰이 만료되어 재발급합니다.");

            try {
                // refresh_token으로 access_token 재발급
                const refreshResponse = await fetch('/api/account/refresh/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refresh_token }),
                });

                if (refreshResponse.status === 200) {
                    const data = await refreshResponse.json();
                    const newAccessToken = data.access_token;
                    sessionStorage.setItem('access_token', newAccessToken);

                    // 새로운 access_token을 헤더에 설정
                    axiosInstance.defaults.headers['Authorization'] = `Bearer ${newAccessToken}`;

                    // 큐에 있던 요청들을 새 토큰으로 재시도
                    while (refreshQueue.length > 0) {
                        const { resolve, reject, originalRequest } = refreshQueue.shift();
                        // 새 토큰을 적용하고 요청 재시도
                        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
                        axios(originalRequest)
                            .then(resolve)  // 요청 성공 시 resolve
                            .catch(reject);  // 요청 실패 시 reject
                    }

                    // 첫 번째 요청은 이미 새 토큰으로 재시도되었기 때문에 여기서 반환하지 않음
                } else {
                    throw new Error("Refresh 토큰이 만료되었습니다.");
                }
            } catch (refreshError) {
                console.error("Refresh 토큰이 만료되었습니다.");
                sessionStorage.removeItem('access_token');
                sessionStorage.removeItem('refresh_token');
                location.href = "/";  // 로그아웃 처리
            } finally {
                isRefreshing = false;
            }

            // 첫 번째 요청에 대해서는 토큰 갱신 후 새 토큰을 사용하여 재시도
            originalRequest.headers['Authorization'] = `Bearer ${sessionStorage.getItem('access_token')}`;
            return axios(originalRequest);  // 새 토큰으로 원래 요청을 재시도
        }

        // 이미 토큰 갱신 중인 경우 요청을 큐에 추가
        if (error.response.status === 401 && refresh_token && isRefreshing) {
            // 이미 요청 중인 토큰 갱신을 기다리는 Promise를 반환
            return new Promise((resolve, reject) => {
                refreshQueue.push({
                    resolve,
                    reject,
                    originalRequest
                });
            });
        }

        return Promise.reject(error);
    });


    // 로그아웃 처리
    function logout() {
        axiosInstance.post('/account/logout/', {
            refresh_token: refresh_token
        }).then((response) => {
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('refresh_token');
            location.href = "/";
        }).catch((error) => {
            console.log(error);
        });
    }

    
    async function displayUserInfo() {
        try {
            const response = await axiosInstance.get('/account/token/');

            if (response.status === 200) {
                const data = response.data;
                console.log("유저 정보:", data);

                if (data.user_id !== undefined) {
                    // 유저 사진 처리
                    if (data.photo) {
                        let photo = data.photo.split("/").splice(2);
                        if (photo[0] === "items") {
                            nav_auth.append(`<div class="user_photo">
                                <img src="https://cdn.fastly.steamstatic.com/steamcommunity/public/images/${photo.join("/")}" />
                            </div>`);
                        } else if (photo[0] === "https%3A") {
                            nav_auth.append(`<div class="user_photo">
                                <img src="${photo.join("/").replace("%3A", ":")}" />
                            </div>`);
                        } else {
                            nav_auth.append(`<div class="user_photo">
                                <img src="${data.photo}" />
                            </div>`);
                        }
                    } else {
                        nav_auth.append(`<div class="user_photo">
                            <img src="/static/images/default_profile.png" />
                        </div>`);
                    }

                    nav_auth.append(`<h3>${data.user_id}님</h3>`);
                    nav_auth.append(`<a href="/view/profile/${data.id}">마이페이지</a>`);
                    nav_auth.append(`<input type="button" class="logout" value="로그아웃">`);

                    // 로그아웃 버튼 클릭 이벤트
                    $("div.nav_auth input.logout").click(function() {
                        logout();
                    });
                } else {
                    add_signwrap();
                }
            } else {
                console.error("유저 정보 가져오기 실패");
                add_signwrap();
            }
        } catch (error) {
            console.error("Error fetching user info:", error.message);
            add_signwrap();
        }
    } 

    // 유저 정보 표시 함수 호출
    if (access_token) {
        displayUserInfo();
    }else {
        add_signwrap();
    }
});