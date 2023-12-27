function login_required($likeButton) {
    //console.log('2nd check', $likeButton.data('post-id'));
    $.ajax({
       url: '/login_required/',
       success: function (data) {
           console.log(data);
           if (!data || !data.logged_in) {  
               $('#loginModal').modal('show');
           } else {
               // the rest of the like functionality
               var postId = $likeButton.data('post-id');
               var liked = $likeButton.data('liked');
               //console.log(postId);
               $.ajax({
                   url: '/like-post/' + postId + '/',
                   success: function (data) {
                       var likesCount = data.likes_count;
                       liked = data.liked;
                       $likeButton.data('liked', liked);
                       $likeButton.toggleClass('liked', liked);
                       $likeButton.html('<i class="fa fa-heart" aria-hidden="true"></i> ' + likesCount + '');
                   }
               });
           }
       }
    });
}

