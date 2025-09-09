// Функция для установки активной ссылки в sidebar
function setActiveSidebarLink() {
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.nav-link');
    
    // Убираем активное состояние со всех ссылок
    sidebarLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Устанавливаем активное состояние для текущей страницы
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Вызываем функцию при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    setActiveSidebarLink();
});
