let menu = $(".menu")
let settings = $(".settings")
let support = $(".support")

// Функция для закрытия всех меню
function closeAllMenus() {
    $(".navbar__menu").removeClass("navbar__menu-info-active navbar__menu-settings-active");
}

menu.on("click", function () {
    closeAllMenus();
    $(".navbar__menu-info").toggleClass("navbar__menu-info-active");
});
settings.on("click", function () {
    closeAllMenus();
    $(".navbar__menu-settings").toggleClass("navbar__menu-settings-active");
});
support.on("click", function () {
    closeAllMenus();
    $(".navbar__settings").toggleClass("navbar__menu-settings-active");
});
// Закрытие меню при клике вне его области
$(document).on("click", function (event) {
    if (!$(event.target).closest(".navbar__menu, .menu, .settings, .support").length) {
        closeAllMenus();
    }
});

$(document).keydown(function (event) {
    if (event.key === 'F2') {
        window.location.href = 'https://wazir.kg/disp/new_order.html';
    }
    // Закрытие меню при нажатии Escape
    if (event.key === 'Escape') {
        closeAllMenus();
    }
});
