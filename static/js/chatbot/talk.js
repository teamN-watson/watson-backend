function get_record(access_token){
    $.ajax({
        url: "/api/chatbot/record/",
        headers:{
            "Authorization": `Bearer ${access_token}`
        },
        method: 'POST',
        success: function(data){
            console.log(data)
            const record = $("div.chatbot_record")
            for (let i = 0; i < data.length; i++) {
                const response = data[i];
                let htmlContent = `<div class="${response.is_user ? "user" : "ai"}">`;
                htmlContent += `<p>${response.content.message}</p>`;
                if (response.content.game_data) {
                    const game_datas = response.content.game_data
                    for (let j = 0; j < game_datas.length; j++) {
                        const game_data = game_datas[j]
                        htmlContent += `<p>${j+1}번 게임 : ${game_data.title}</p>`;
                        htmlContent += `<p>${game_data.description}</p>`;
                    }

                }
                htmlContent += `</div>`;
                record.append(htmlContent);
            }
        },
        error: function(error){
            console.log(error)
        }
    })
}
$(document).ready(function() {
    const access_token = sessionStorage.getItem('access_token')
    get_record(access_token);
    $("div.chatbotContainer form").submit(function(e) {
        e.preventDefault();

        $.ajax({
            url: "/api/chatbot/",
            headers: {
                "Authorization": `Bearer ${access_token}`
            },
            method: 'POST',
            data: {
                "message": $("input[name='message']").val()
            },
            beforeSend: function() {
                $("div.loading").addClass("active");
                $("input[name='message']").val("")
            },
            success: function(data){
                console.log(data)
                const record = $("div.chatbot_record")

                let htmlContent = ``;
                const user_message = data.user_message;
                htmlContent += `<div class="user">`;
                htmlContent += `<p>${user_message.message}</p>`;
                htmlContent += `</div>`;
                
                const bot_message = data.bot_message;
                htmlContent += `<div class="ai">`;
                htmlContent += `<p>${bot_message.message}</p>`;
                if (bot_message.game_data) {
                    const game_datas = bot_message.game_data
                    for (let j = 0; j < game_datas.length; j++) {
                        const game_data = game_datas[j]
                        htmlContent += `<p>${j+1}번 게임 : ${game_data.title}</p>`;
                        htmlContent += `<p>${game_data.description}</p>`;
                    }
                }
                htmlContent += `</div>`;
                record.append(htmlContent);
            },
            error: function(error){
                console.log(error)
                const record = $("div.chatbot_record")

                let htmlContent = ``;
                const user_message = error.user_message;
                htmlContent += `<div class="user">`;
                htmlContent += `<p>${user_message.message}</p>`;
                htmlContent += `</div>`;
                const bot_message = error.bot_message;
                htmlContent += `<div class="ai">`;
                htmlContent += `<p>${bot_message.message}</p>`;
                htmlContent += `</div>`;
                record.append(htmlContent);
            },
            complete: function() {
                setTimeout(() => {
                    $("div.loading").removeClass("active");                    
                }, 500);
            }
        });
    })
    
});
