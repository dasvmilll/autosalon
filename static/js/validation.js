// =========================================
// 1. БУРГЕР-МЕНЮ
// =========================================
document.addEventListener('DOMContentLoaded', () => {
    const burgerBtn = document.getElementById('burgerBtn');
    const mainNav = document.getElementById('mainNav');

    if (burgerBtn && mainNav) {
        burgerBtn.addEventListener('click', () => {
            burgerBtn.classList.toggle('active');
            mainNav.classList.toggle('mobile-open');
        });
    }

    // =========================================
    // 2. ЖИВОЙ ПОИСК В ШАПКЕ
    // =========================================
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const searchLoader = document.getElementById('searchLoader');

    if (searchInput && searchResults) {
        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            clearTimeout(searchTimeout);

            if (query.length < 2) {
                searchResults.style.display = 'none';
                searchResults.innerHTML = '';
                return;
            }

            if (searchLoader) searchLoader.style.display = 'block';

            searchTimeout = setTimeout(() => {
                // ИСПРАВЛЕНИЕ ДЕФЕКТА 5: добавлена проверка response.ok и блок .catch()
                fetch('/catalog/api/search/?q=' + encodeURIComponent(query))
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Ошибка сети: ' + response.status);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (searchLoader) searchLoader.style.display = 'none';

                        if (data.length === 0) {
                            searchResults.innerHTML = '<div class="search-item">Ничего не найдено</div>';
                        } else {
                            searchResults.innerHTML = data.map(item =>
                                `<a href="/catalog/${item.id}/" class="search-item">${item.brand} ${item.model}</a>`
                            ).join('');
                        }
                        searchResults.style.display = 'block';
                    })
                    .catch(error => {
                        // ИСПРАВЛЕНИЕ ДЕФЕКТА 5: обработка ошибок сети
                        if (searchLoader) searchLoader.style.display = 'none';
                        console.error('Ошибка поиска:', error);
                        searchResults.innerHTML = '<div class="search-item" style="color: #EF4444;">Ошибка загрузки. Попробуйте позже.</div>';
                        searchResults.style.display = 'block';
                    });
            }, 300);
        });

        // Закрытие результатов при клике вне
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }

    // =========================================
    // 3. ЖИВОЙ ФИЛЬТР КАТАЛОГА
    // =========================================
    const filtersForm = document.querySelector('.filters-form');
    const carsGrid = document.getElementById('carsGrid');
    const catalogLoader = document.querySelector('.catalog-loader');

    if (filtersForm && carsGrid) {
        const filters = filtersForm.querySelectorAll('input, select');

        filters.forEach(filter => {
            filter.addEventListener('change', applyFilters);
            if (filter.tagName === 'INPUT') {
                filter.addEventListener('input', applyFilters);
            }
        });

        function applyFilters() {
            const formData = new FormData(filtersForm);
            const params = new URLSearchParams(formData).toString();

            if (catalogLoader) catalogLoader.style.display = 'block';
            carsGrid.style.opacity = '0.5';

            // ИСПРАВЛЕНИЕ ДЕФЕКТА 5: добавлена проверка response.ok и блок .catch()
            fetch('/catalog/api/filter/?' + params)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Ошибка сети: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    if (catalogLoader) catalogLoader.style.display = 'none';
                    carsGrid.style.opacity = '1';

                    if (data.cars.length === 0) {
                        carsGrid.innerHTML = '<div class="empty-state">Автомобили не найдены</div>';
                    } else {
                        carsGrid.innerHTML = data.cars.map(car => `
                            <article class="card">
                                <div class="card-img">
                                    <img src="${car.image}" alt="${car.brand} ${car.model}" width="400" height="200" loading="lazy">
                                    ${car.status !== 'available' ? `<span class="status-badge ${car.status}">${car.status_display}</span>` : ''}
                                </div>
                                <div class="card-body">
                                    <h3 class="card-title">${car.brand} ${car.model}</h3>
                                    <p class="card-subtitle">${car.trim} • ${car.year}</p>
                                    <p class="card-price">${car.price_formatted} ₽</p>
                                    <a href="/catalog/${car.id}/" class="btn-secondary">Подробнее</a>
                                </div>
                            </article>
                        `).join('');
                    }
                })
                .catch(error => {
                    // ИСПРАВЛЕНИЕ ДЕФЕКТА 5: обработка ошибок сети
                    if (catalogLoader) catalogLoader.style.display = 'none';
                    carsGrid.style.opacity = '1';
                    console.error('Ошибка фильтра:', error);
                    carsGrid.innerHTML = '<div class="empty-state" style="color: #EF4444;">Ошибка загрузки. Попробуйте позже.</div>';
                });
        }
    }

    // =========================================
    // 4. ВАЛИДАЦИЯ ФОРМЫ РЕГИСТРАЦИИ
    // =========================================
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            const password = document.getElementById('id_password1');
            const password2 = document.getElementById('id_password2');

            if (password && password2 && password.value !== password2.value) {
                e.preventDefault();
                alert('Пароли не совпадают!');
                password2.focus();
            }
        });
    }
});