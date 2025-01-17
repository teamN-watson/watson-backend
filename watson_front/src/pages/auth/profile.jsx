import React, { useEffect, useState } from 'react';
import axios from '@src/axiosInstance';
import useStore from '@store/zustore';
import { useNavigate, useParams } from 'react-router-dom';
import { getProfilePhotoUrl } from '@src/utils';

function Profile() {
  const { id } = useParams(); // URL에서 id 파라미터 가져오기
  const { isLoggedIn, userInfo, setUserInfo, logout, accessToken, refreshToken, setAccessToken, setRefreshToken } = useStore();
  const [ownedGames, setOwnedGames] = useState([]);
  const [recentGames, setRecentGames] = useState([]);
  const [isMypage, setIsMypage] = useState(false);
  useEffect(() => {
    console.log(id)
    if (id) {
      axios.get(`http://127.0.0.1:8000/api/account/profile?id=${id}`).then((response) => {
        if (response.status === 200) {
          console.log(response.data)
          const data = response.data.data;

          setIsMypage(data.is_mypage)
        }
      });

    }
  }, [id]);


  return (
    <div className="profileContainer">
      <div className="user_photo">
        <img src={`https://cdn.fastly.steamstatic.com/steamcommunity/public/images/${userInfo?.photo || '/static/images/default_profile.png'}`} alt="Profile" />
      </div>

      <div className="user_info">
        {isMypage && <a href="/view/edit/"><button>편집하기</button></a>}
        <p id="user_user_id">아이디 : {userInfo?.user_id}</p>
        <p id="user_email">이메일 : {userInfo?.email}</p>
        <p id="user_nickname">닉네임 : {userInfo?.nickname}</p>
        <p id="user_age">나이 : {userInfo?.age}</p>

        {userInfo?.steamId && <p id="user_steamId">스팀ID : {userInfo.steamId}</p>}

        {isMypage ? (
          userInfo.steamId ? (
            <input type="button" name="steam_profile" className="steam_profile" value="스팀 프로필 이미지 가져오기" onClick={steamProfileAction} />
          ) : (
            <a href={`/view/steam/login/?user_id=${userInfo.user_id}`} className="btn btn-steam-login">
              Login with Steam
            </a>
          )
        ) : null}
      </div>

      <div className="owned_game">
        {ownedGames.length > 0 ? (
          ownedGames.map((game, index) => {
            const date = new Date(game.rtime_last_played * 1000);
            const formattedDate = `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;

            return (
              <div key={index}>
                <img src={`https://avatars.fastly.steamstatic.com/${game.img_icon_url}.jpg`} alt={game.name} />
                <span>{game.name}</span>
                <span>{(game.playtime_forever / 60).toFixed(1)}시간</span>
                <span>최근 플레이 {formattedDate}</span>
              </div>
            );
          })
        ) : (
          <div>보유한 게임이 없습니다.</div>
        )}
      </div>

      <div className="recent_game">
        {recentGames.length > 0 ? (
          recentGames.map((game, index) => (
            <div key={index}>
              <img src={`https://avatars.fastly.steamstatic.com/${game.img_icon_url}.jpg`} alt={game.name} />
              <span>{game.name}</span>
              <span>총 플레이타임 {(game.playtime_forever / 60).toFixed(1)}시간</span>
              <span>지난 2주간 플레이타임 {(game.playtime_2weeks / 60).toFixed(1)}시간</span>
            </div>
          ))
        ) : (
          <div>최근 플레이한 게임이 없습니다.</div>
        )}
      </div>
    </div>
  );
}

export default Profile;
