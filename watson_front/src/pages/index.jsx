import React from 'react';
import banner from '../assets/images/loading.gif';
import '@assets/css/index.css';  // '@assets' 별칭을 사용하여 CSS 파일 import

export default function IndexPage() {
    return (<main>
        <div className="container">
            <section className="banner">
                <div>
                    <img src={banner} />
                </div>
            </section>
            <section className="product-list">
                <div className="container">

                </div>
            </section>
        </div>
    </main>)
}