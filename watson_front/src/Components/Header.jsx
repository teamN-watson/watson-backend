// src/components/Header.jsx
import React, { useEffect } from 'react';
import axios from '@src/axiosInstance';
import useStore from '@store/zustore';
import '@assets/css/navbar.css';
export default function Header() {
    const { isLoggedIn, userInfo, setUserInfo, logout, accessToken, refreshToken, setAccessToken, setRefreshToken } = useStore();

    useEffect(() => {
        const refreshToken = sessionStorage.getItem('refresh_token');

        if (refreshToken) {
            setRefreshToken(refreshToken);
        }
    }, [refreshToken]);
    useEffect(() => {
        const accessToken = sessionStorage.getItem('access_token');
        if (accessToken) {
            setAccessToken(accessToken);
            // 로그인 상태일 때 유저 정보 불러오기
            axios.get('http://127.0.0.1:8000/api/account/token/', {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            }).then((response) => {
                if (response.status === 200) {
                    console.log(response.data)
                    setUserInfo(response.data);
                }
            }).catch((error) => {
                console.error('Error fetching user info:', error);
            });
        }
    }, []);

    const handleLogout = () => {
        if (refreshToken && accessToken) {
            axios.post('http://127.0.0.1:8000/api/account/logout/', {
                refresh_token: refreshToken, // body 데이터
            }, {
                headers: { 'Authorization': `Bearer ${accessToken}` }, // 헤더 설정
            }
            ).then((response) => {
                if (response.status === 200) {
                    logout(); // zustand 상태에서 로그아웃 처리
                    sessionStorage.removeItem('access_token');
                    sessionStorage.removeItem('refresh_token');
                    // window.location.href = '/'; // 로그아웃 후 리다이렉트
                }
            }).catch((error) => {
                console.error('Error fetching user info:', error);
            });


        }
    };

    return (
        <header>
            <nav className="navbar">
                <div className="container">
                    <div>
                        <a href="/" className="logo">
                            Watson
                        </a>
                    </div>
                    <div>
                        <ul className="menu">
                            <li><a href="/reviews/">리뷰</a></li>
                            <li><a href="/search">게임</a></li>
                            <li><a href="/chatbot">챗봇</a></li>
                        </ul>
                    </div>
                    <div>
                        <div className="nav_auth">
                            {isLoggedIn ? (
                                <>
                                    {userInfo?.photo && (
                                        <div className="user_photo">
                                            <img src={userInfo.photo} alt="User Photo" />
                                        </div>
                                    )}
                                    <h3>{userInfo?.user_id}님</h3>
                                    <a href={`/profile/${userInfo?.id}`}>마이페이지</a>
                                    <button onClick={handleLogout}>로그아웃</button>
                                </>
                            ) : (
                                <>
                                    <a href="/signin">로그인</a>
                                    <a href="/signup">회원가입</a>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </nav>
        </header>
    );
}
