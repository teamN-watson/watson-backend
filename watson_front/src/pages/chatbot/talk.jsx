import React, { useEffect, useState } from 'react';
import '@assets/css/chatbot/talk.css';  // '@assets' 별칭을 사용하여 CSS 파일 import
import axios from '@src/axiosInstance';

export default function IndexPage() {
    const [message, setMessage] = useState('');
    const [chatHistory, setChatHistory] = useState([]);  // 채팅 기록 상태

    useEffect(() => {
        axios.post('http://127.0.0.1:8000/api/chatbot/record/').then((response) => {
            if (response.status === 200) {
                console.log(response.data)
                const data = response.data;
                let newChatHistory = []

                data.forEach((chat, index) => {
                    console.log(chat)
                    newChatHistory.push({
                        content: { message: chat.content.message },
                        is_user: chat.is_user,
                    })

                    if (chat.content.game_data) {
                        chat.content.game_data.forEach((game, index) => {
                            newChatHistory.push(
                                {
                                    content: { message: `${index + 1}번 게임: ${game.title}` },
                                    is_user: false,
                                },
                                {
                                    content: { message: game.description },
                                    is_user: false,
                                }
                            );
                        });
                    }

                });

                // 채팅 기록 상태 업데이트
                setChatHistory(newChatHistory);
            }
        }).catch((error) => {
            console.error('Error fetching user info:', error);
        });
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            await axios.post(
                'http://127.0.0.1:8000/api/chatbot/',
                { message: message },
            ).then((response) => {
                const data = response.data;
                if (response.status === 200 || response.status === 201) {
                    console.log(response.data)

                    let newChatHistory = [
                        ...chatHistory,
                        {
                            content: { message: data.user_message.message },
                            is_user: true,
                        },
                        {
                            content: { message: data.bot_message.message },
                            is_user: false,
                        },
                    ];

                    // 게임 데이터가 있을 경우, 게임별 메시지 추가
                    if (data.bot_message.game_data) {
                        data.bot_message.game_data.forEach((game, index) => {
                            newChatHistory = [
                                ...newChatHistory,
                                {
                                    content: { message: `${index + 1}번 게임: ${game.title}` },
                                    is_user: false,
                                },
                                {
                                    content: { message: game.description },
                                    is_user: false,
                                },
                            ];
                        });
                    }

                    setChatHistory(newChatHistory);  // 상태 업데이트
                    setMessage("");  // 입력 필드 초기화
                }
            }).catch((error) => {
                console.error('Error chatbot record:', error);
            });
        } catch (error) {
            console.error('채팅 시작하는데 실패했습니다:', error);
        }

    };

    return (
        <div className="chatbotContainer">
            <div className="chatbot_wrap" id="wrap1">
                <div className="chatbot_record">
                    {chatHistory.length && chatHistory.map((chat, index) => (
                        <div key={index}>
                            {/* 사용자 또는 봇 메시지 */}
                            <div className={chat.is_user ? "user" : "ai"}>
                                <p>{chat.content.message}</p>
                            </div>

                        </div>
                    ))}
                </div>
                <form onSubmit={handleSubmit}>
                    <div className="chatbot_input">
                        <input onChange={(e) => setMessage(e.target.value)} type="text" name="message" placeholder="메시지를 입력해주세요." value={message} />
                    </div>
                </form>
            </div>
        </div>)
}