import React from "react";
import { Route, Routes } from "react-router-dom";
import GlobalLayout from "./Components/Layout"; // 레이아웃 컴포넌트
import Index from "./pages/index"; // 홈 페이지 컴포넌트
import Signin from "./pages/auth/signin"; // 로그인 페이지 컴포넌트
import "./App.css";

export default function App() {
  return (
    <Routes>
      <Route element={<GlobalLayout />}>
        <Route path="/" element={<Index />} />
        <Route path="/auth" element={<Signin />} />
      </Route>
    </Routes>
  );
}
