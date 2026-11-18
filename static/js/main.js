document.addEventListener('DOMContentLoaded', function() {
    // Бургер-меню
    const burger = document.getElementById('burgerBtn');
    const nav = document.getElementById('mainNav');
    if (burger && nav) {
        burger.addEventListener('click', function() {
            nav.classList.toggle('mobile-open');
            burger.classList.toggle('active');
        });
    }
});