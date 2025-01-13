function get_review(){
    $.ajax({
        url: "/api/reviews/",
        method: 'GET',
        success: function(data){
            console.log(data)
            const list_wrap = $("div.listWrap")
            if(data.length){
                for (let i = 0; i < data.length; i++) {
                    const el = data[i];
                    let objectDate = new Date(el.created_at);
    
                    let day = objectDate.getDate();
                    let month = objectDate.getMonth();
                    let year = objectDate.getFullYear();
    
                    var title = "Zomboid";
                    var categories = ["생존", "좀비", "멀티 플레이어"]
                    list_wrap.append(`
                        <div class="game_row">
                            <div class="game_title">
                                <div class="game_img"><img src="/static/images/games/1.jpg"></div>
                                <div class="game_info">
                                    <h4>${title}</h4>
                                    <div class="categories"></div>
                                    <span>${year}년 ${month+1}월 ${day}일</span>
                                    <span>${el.nickname}</span>
                                </div>
                            </div>
                            <div class="game_rating">
                                <span>${"⭐".repeat(el.score*1)}</span>
                                <span>좋아요 수 ${el.total_likes}</span>
                            </div>
                        </div>`);
                    const game_row = $("div.listWrap .game_row:last div.categories")
                    categories.forEach(category => {
                        game_row.append(`<span class="category">${category}</span>`);
                    });
                }
            } else {      
                list_wrap.append(`<h4>등록된 리뷰가 없습니다.</h4>`)          
            }
        },
        error: function(error){
            console.log(error)
        }
    })
}
$(document).ready(function() {
    get_review()
});