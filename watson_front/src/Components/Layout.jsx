import React from "react";
import Header from "./Header";  // 헤더 컴포넌트
import Footer from "./Footer";  // 푸터 컴포넌트
import { Outlet } from 'react-router-dom'

export default function GlobalLayout() {
    return (
        <div>
            <Header />
            <main id="main">
                <div className="container">
                    <Outlet />
                </div>
            </main>
            <Footer />
        </div>
    );
}