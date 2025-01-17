import React from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import GlobalLayout from "./Components/Layout"; // 레이아웃 컴포넌트
import Index from "./pages/index"; // 홈 페이지 컴포넌트
import Signin from "./pages/auth/signin"; // 로그인 페이지 컴포넌트
import Signup from "./pages/auth/signup"; // 로그인 페이지 컴포넌트
import Talk from "./pages/chatbot/talk"; // 챗봇 페이지 컴포넌트
import Profile from "./pages/auth/profile"; // 프로필 페이지 컴포넌트
import "./App.css";

export default function App() {
  return (
    <Routes>
      <Route element={<GlobalLayout />}>
        <Route path="/" element={<Index />} />
        <Route path="/signin" element={<Signin />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/chatbot" element={<Talk />} />
        <Route exact path="/profile/:id" element={<Profile />} />
        <Route path="/profile" element={<Navigate to="/" />} />
      </Route>
    </Routes>
  );
}
