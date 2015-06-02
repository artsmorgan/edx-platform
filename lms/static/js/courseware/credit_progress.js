$(document).ready(function() {
    $('.detail-collapse').click(function(){
        var that = $(this);
        $('.requirement-container').toggleClass('is-hidden');
        that.find('.fa').toggleClass('fa-caret-down fa-caret-up');
        that.find('span').text(function(i, text){
          return text === gettext("Expand for details") ? gettext("Collapse") : gettext("Expand for details");
        });
    });

});
