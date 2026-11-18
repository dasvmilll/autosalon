document.addEventListener('DOMContentLoaded', function() {
    // Валидация формы трейд-ина
    const tradeinForm = document.getElementById('tradeinForm');
    if (tradeinForm) {
        tradeinForm.addEventListener('submit', function(e) {
            let isValid = true;
            const phoneInput = document.querySelector('input[name="phone"]');
            const yearInput = document.querySelector('input[name="year"]');
            const brandInput = document.querySelector('input[name="brand"]');

            document.querySelectorAll('.js-error').forEach(el => el.remove());

            if (brandInput && !brandInput.value.trim()) {
                showError(brandInput, 'Укажите марку автомобиля');
                isValid = false;
            }

            const phoneRegex = /^\+7\s?\d{3}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}$/;
            if (phoneInput && !phoneRegex.test(phoneInput.value)) {
                showError(phoneInput, 'Формат: +7 900 000-00-00');
                isValid = false;
            }

            const year = parseInt(yearInput.value);
            if (yearInput && (isNaN(year) || year < 1900 || year > 2026)) {
                showError(yearInput, 'Введите год от 1900 до 2026');
                isValid = false;
            }

            if (!isValid) e.preventDefault();
        });
    }

    // Валидация формы тест-драйва
    const testdriveForm = document.getElementById('testdriveForm');
    if (testdriveForm) {
        testdriveForm.addEventListener('submit', function(e) {
            let isValid = true;
            const licenseInput = document.querySelector('input[name="license_number"]');
            const experienceInput = document.querySelector('input[name="experience_years"]');

            document.querySelectorAll('.js-error').forEach(el => el.remove());

            if (licenseInput && !/^\d{2}\s?\d{2}\s?\d{6}$/.test(licenseInput.value)) {
                showError(licenseInput, 'Формат: 77 12 345678');
                isValid = false;
            }

            if (experienceInput && parseInt(experienceInput.value) < 2) {
                showError(experienceInput, 'Стаж должен быть не менее 2 лет');
                isValid = false;
            }

            if (!isValid) e.preventDefault();
        });
    }

    function showError(input, message) {
        const error = document.createElement('div');
        error.className = 'errorlist js-error';
        error.innerText = message;
        input.parentNode.appendChild(error);
    }

    // Живой поиск
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value;
            if (query.length < 2) {
                document.getElementById('searchResults').style.display = 'none';
                return;
            }

            const loader = document.getElementById('searchLoader');
            loader.style.display = 'block';

            fetch(`/catalog/api/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    const resultsDiv = document.getElementById('searchResults');
                    if (data.results.length > 0) {
                        resultsDiv.innerHTML = data.results.map(car => 
                            `<div class="search-item" onclick="window.location='/catalog/car/${car.id}/'">
                                <strong>${car.name}</strong> — ${car.price.toLocaleString()} ₽
                            </div>`
                        ).join('');
                        resultsDiv.style.display = 'block';
                    } else {
                        resultsDiv.style.display = 'none';
                    }
                    loader.style.display = 'none';
                });
        });
    }

    // Живой фильтр каталога
    const filterForm = document.getElementById('filterForm');
    const brandInput = document.getElementById('filterBrand');
    const sortSelect = document.getElementById('filterSort');
    const carsGrid = document.getElementById('carsGrid');
    const catalogLoader = document.getElementById('catalogLoader');
    const paginationBlock = document.getElementById('paginationBlock');

    if (filterForm && carsGrid) {
        // Предотвращаем отправку формы (без инлайн-onsubmit)
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
        });

        function fetchCars() {
            const brand = brandInput.value;
            const sort = sortSelect.value;
            
            catalogLoader.style.display = 'block';
            carsGrid.style.opacity = '0.5';
            if (paginationBlock) paginationBlock.style.display = 'none';

            fetch(`/catalog/api/filter/?brand=${encodeURIComponent(brand)}&sort=${encodeURIComponent(sort)}`)
                .then(response => response.json())
                .then(data => {
                    carsGrid.innerHTML = '';
                    if (data.cars.length === 0) {
                        carsGrid.innerHTML = '<div class="empty-state"><p>Ничего не найдено.</p></div>';
                    } else {
                        data.cars.forEach(car => {
                            const imageUrl = car.image || '/media/cars/haval.jpg';
                            const card = document.createElement('article');
                            card.className = 'card';
                            card.innerHTML = `
                                <div class="card-img">
                                    <img src="${imageUrl}" alt="${car.brand} ${car.model}" width="400" height="200" loading="lazy">
                                    ${car.status === 'reserved' ? '<span class="status-badge reserved">Забронирован</span>' : ''}
                                </div>
                                <div class="card-body">
                                    <h3 class="card-title">${car.brand} ${car.model}</h3>
                                    <p class="card-subtitle">${car.trim} · ${car.color}</p>
                                    <p class="card-price">${car.price.toLocaleString('ru-RU')} ₽</p>
                                    <a href="/catalog/car/${car.id}/" class="btn-secondary">Подробнее</a>
                                </div>
                            `;
                            carsGrid.appendChild(card);
                        });
                    }
                    catalogLoader.style.display = 'none';
                    carsGrid.style.opacity = '1';
                })
                .catch(err => {
                    console.error('Ошибка загрузки:', err);
                    catalogLoader.style.display = 'none';
                    carsGrid.style.opacity = '1';
                });
        }

        let timeout = null;
        brandInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(fetchCars, 400);
        });

        sortSelect.addEventListener('change', fetchCars);
    }
});