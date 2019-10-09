$(window).click(function (e) {
    $(".popup").css({
        left: e.pageX
    });
    $(".popup").css({
        top: e.pageY
    });
    $(".popup").show();
});

$('.popupCloseButton').click(function () {
    $('.popup').hide();
});


// $(window).load(function () {
//     $(".trigger_popup_fricc").click(function () {
//         $('.hover_bkgr_fricc').show();
//     });
//     $('.hover_bkgr_fricc').click(function () {
//         $('.hover_bkgr_fricc').hide();
//     });
//     $('.popupCloseButton').click(function () {
//         $('.hover_bkgr_fricc').hide();
//     });
// });