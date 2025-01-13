function get_review(){
    $.ajax({
        url: "/api/review/",
        method: 'GET',
        success: function(response){
            console.log(response)
            
        },
        error: function(error){
            console.log(error)
        }
    })
}
$(document).ready(function() {
    get_review()
});