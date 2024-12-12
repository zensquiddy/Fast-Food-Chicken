$(document).ready(function() {
    $(".reply-button").click(function() {
        var postId = $(this).data("post-id");
        $("#replybox-" + postId).toggle();
    });
});