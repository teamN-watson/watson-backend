import React from 'react';
import './navbar.css';

export default function Header() {
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
                            <li><a href="/view/reviews/">리뷰</a></li>
                            <li><a href="/view/search">게임</a></li>
                            <li><a href="/view/chatbot">챗봇</a></li>
                        </ul>
                    </div>
                    <div>
                        <div className="nav_auth">
                        </div>
                    </div>
                </div>
            </nav>
        </header>
    );
}