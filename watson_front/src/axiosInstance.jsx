// api.js (또는 axiosInstance.js)

import axios from 'axios';

// axios 인스턴스 생성
const axiosInstance = axios.create({
    baseURL: '/api',
});

// 요청 인터셉터 추가
axiosInstance.interceptors.request.use((config) => {
    const access_token = sessionStorage.getItem('access_token');

    // 토큰이 있으면 헤더에 추가
    if (access_token && !config.noAuthRequired) {
        config.headers['Authorization'] = `Bearer ${access_token}`;
    }

    return config;
}, (error) => {
    return Promise.reject(error);
});

// 응답 인터셉터 추가 (토큰 만료 처리 및 재발급)
let isRefreshing = false;  // 토큰 갱신 중 여부
let refreshQueue = [];  // 토큰 갱신을 기다리는 요청 큐

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;  // 원래 요청의 설정
        const refresh_token = sessionStorage.getItem('refresh_token');
        console.log(error.response.status)

        if (error.response.status === 401 && refresh_token && !isRefreshing) {
            isRefreshing = true;  // 토큰 갱신 중임을 표시
            console.log("토큰 만료, 재발급 시도");

            try {
                // refresh_token을 사용해 새 access_token 발급 요청
                const refreshResponse = await fetch('http://127.0.0.1:8000/api/account/refresh/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refresh_token }),
                });

                if (refreshResponse.status === 200) {
                    const data = await refreshResponse.json();
                    const newAccessToken = data.access_token;
                    sessionStorage.setItem('access_token', newAccessToken);

                    // 새로 받은 access_token을 헤더에 설정
                    axiosInstance.defaults.headers['Authorization'] = `Bearer ${newAccessToken}`;

                    // 대기 중인 요청들에 대해 새 토큰으로 재시도
                    while (refreshQueue.length > 0) {
                        const { resolve, reject, originalRequest } = refreshQueue.shift();
                        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
                        axios(originalRequest)
                            .then(resolve)
                            .catch(reject);
                    }
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

            // 첫 번째 요청은 새 토큰으로 재시도
            originalRequest.headers['Authorization'] = `Bearer ${sessionStorage.getItem('access_token')}`;
            return axios(originalRequest);  // 새 토큰으로 재시도
        }

        // 이미 토큰 갱신 중인 경우 요청을 큐에 추가
        if (error.response.status === 401 && refresh_token && isRefreshing) {
            return new Promise((resolve, reject) => {
                refreshQueue.push({
                    resolve,
                    reject,
                    originalRequest,
                });
            });
        }

        return Promise.reject(error);
    }
);

// axiosInstance를 export하여 다른 파일에서 사용하도록 함
export default axiosInstance;
