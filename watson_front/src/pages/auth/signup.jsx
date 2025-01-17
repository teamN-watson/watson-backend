import React, { useState } from 'react';
import axios from '@src/axiosInstance';
import useStore from '@store/zustore';
import '@assets/css/account/signin.css';

export default function SignupPage() {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const login = useStore((state) => state.login); // zustand의 login 함수 가져오기

  // const handleSubmit = async (e) => {
  //   e.preventDefault();

  //   try {
  //     const response = await axios.post(
  //       'http://127.0.0.1:8000/api/account/signin/',
  //       { user_id: userId, password: password },
  //     );

  //     if (response.data.access_token && response.data.refresh_token) {
  //       // zustand 스토어에 로그인 정보 저장
  //       login({ user_id: userId }, response.data.access_token, response.data.refresh_token);
  //       window.location.href = '/';
  //     }
  //   } catch (error) {
  //     console.error(error);
  //     setErrorMsg(error.response?.data?.message || '로그인에 실패했습니다.');
  //   }
  // };

  return (
    <div className="signupContainer">
      <h2>회원가입</h2>
    </div>
  );
}
