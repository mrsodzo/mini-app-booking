(function() {
    'use strict';

    function debugLog(...args) {
        console.log(...args);
    }

    const WebApp = window.Telegram?.WebApp;
    if (WebApp) {
        WebApp.ready();
        WebApp.expand();
        WebApp.MainButton.hide();
    }

    debugLog('WebApp initialized', { WebApp: !!WebApp, userAgent: navigator.userAgent });

    const API_BASE_URL = document.querySelector('meta[name="api-base-url"]')?.content || 'http://localhost:8080';

    const CONFIG = {
        TIME_SLOTS: ['10:00', '12:00', '14:00', '16:00', '18:00'],
        RIDDLES: [
            'Что можно держать в левой руке, но нельзя взять в правую?',
            'Что имеет ключи, но не может открыть замки?',
            'Что становится больше, когда его переворачиваешь?',
            'Что принадлежит вам, но другие пользуются этим чаще?',
            'Что можно поймать, но не бросить?',
        ],
        RIDDLE_ANSWERS: {
            'Что можно держать в левой руке, но нельзя взять в правую?': ['правая рука', 'правую руку'],
            'Что имеет ключи, но не может открыть замки?': ['пианино', 'фортепиано', 'клавиатура'],
            'Что становится больше, когда его переворачиваешь?': ['число 6', '6', 'шесть'],
            'Что принадлежит вам, но другие пользуются этим чаще?': ['имя', 'ваше имя'],
            'Что можно поймать, но не бросить?': ['простуду', 'простуду', 'холод'],
        }
    };

    const state = {
        currentScreen: 'screen-services',
        selectedService: null,
        selectedDate: null,
        selectedTime: null,
        services: [],
        riddle: null,
    };

    const screens = {};
    const elements = {};

    function initElements() {
        document.querySelectorAll('.screen').forEach(screen => {
            screens[screen.id] = screen;
        });

        elements.servicesList = document.getElementById('services-list');
        elements.datesList = document.getElementById('dates-list');
        elements.timeSlots = document.getElementById('time-slots');
        elements.bookingForm = document.getElementById('booking-form');
        elements.clientName = document.getElementById('client-name');
        elements.clientPhone = document.getElementById('client-phone');
        elements.clientNotes = document.getElementById('client-notes');
        elements.btnSubmit = document.getElementById('btn-submit');
        elements.btnCloseSuccess = document.getElementById('btn-close-success');
        elements.bookingDetails = document.getElementById('booking-details');
        elements.errorMessage = document.getElementById('error-message');
        elements.btnErrorBack = document.getElementById('btn-error-back');
        elements.btnErrorRetry = document.getElementById('btn-error-retry');
        elements.formService = document.getElementById('form-service');
        elements.formDatetime = document.getElementById('form-datetime');
        elements.formPrice = document.getElementById('form-price');
        elements.nameError = document.getElementById('name-error');
        elements.phoneError = document.getElementById('phone-error');
        elements.dateServiceName = document.getElementById('date-service-name');
        elements.dateServicePrice = document.getElementById('date-service-price');
        elements.timeServiceName = document.getElementById('time-service-name');
        elements.timeServiceDate = document.getElementById('time-service-date');
        elements.selectedServiceDate = document.getElementById('selected-service-date');
        elements.selectedServiceTime = document.getElementById('selected-service-time');

        elements.riddleText = document.getElementById('riddle-text');
        elements.contestForm = document.getElementById('contest-form');
        elements.contestAnswer = document.getElementById('contest-answer');
        elements.contestName = document.getElementById('contest-name');
        elements.contestPhone = document.getElementById('contest-phone');
        elements.btnContestSubmit = document.getElementById('btn-contest-submit');
        elements.btnCloseContest = document.getElementById('btn-close-contest');
        elements.contestErrorMessage = document.getElementById('contest-error-message');
        elements.btnContestRetry = document.getElementById('btn-contest-retry');
    }

    function showScreen(screenId) {
        const currentScreen = screens[state.currentScreen];
        const nextScreen = screens[screenId];

        if (!nextScreen || currentScreen === nextScreen) return;

        if (currentScreen) {
            currentScreen.classList.add('exiting');
            setTimeout(() => {
                currentScreen.classList.remove('active', 'exiting');
            }, 250);
        }

        setTimeout(() => {
            nextScreen.classList.add('active');
            state.currentScreen = screenId;
            window.scrollTo(0, 0);
        }, 50);

        if (WebApp) {
            WebApp.MainButton.hide();
        }
    }

    function goBack() {
        switch (state.currentScreen) {
            case 'screen-date':
                showScreen('screen-services');
                break;
            case 'screen-time':
                showScreen('screen-date');
                break;
            case 'screen-form':
                showScreen('screen-time');
                break;
            case 'screen-success':
                closeWebApp();
                break;
            case 'screen-error':
                if (state.selectedTime) showScreen('screen-time');
                else if (state.selectedDate) showScreen('screen-date');
                else if (state.selectedService) showScreen('screen-services');
                else showScreen('screen-services');
                break;
            case 'screen-contest-success':
                closeWebApp();
                break;
            case 'screen-contest-error':
                showScreen('screen-contest');
                break;
            default:
                showScreen('screen-services');
        }
    }

    function closeWebApp() {
        if (WebApp) {
            WebApp.close();
        }
    }

    async function fetchServices() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/services`);
            if (!response.ok) throw new Error('Failed to fetch services');
            const data = await response.json();
            state.services = data.services || [];
            debugLog('Services loaded:', state.services);
            return state.services;
        } catch (err) {
            debugLog('Error fetching services:', err);
            showErrorScreen('Не удалось загрузить услуги. Проверьте соединение.');
            return [];
        }
    }

    async function fetchAvailableDates(serviceId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/services/${serviceId}/dates`);
            if (!response.ok) throw new Error('Failed to fetch dates');
            const data = await response.json();
            debugLog('Dates loaded:', data.dates);
            return data.dates || [];
        } catch (err) {
            debugLog('Error fetching dates:', err);
            showErrorScreen('Не удалось загрузить даты. Проверьте соединение.');
            return [];
        }
    }

    async function fetchAvailableSlots(serviceId, date) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/services/${serviceId}/dates/${date}/slots`);
            if (!response.ok) throw new Error('Failed to fetch slots');
            const data = await response.json();
            debugLog('Slots loaded:', data.slots);
            return data.slots || [];
        } catch (err) {
            debugLog('Error fetching slots:', err);
            showErrorScreen('Не удалось загрузить время. Проверьте соединение.');
            return [];
        }
    }

    function formatDate(date) {
        return date.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' });
    }

    function formatShortDate(date) {
        return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
    }

    function getDayName(date) {
        return date.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric' });
    }

    function getServiceIcon(serviceType) {
        const icons = {
            'haircut': '✂️',
            'beard': '🧔',
            'coloring': '🎨',
            'styling': '✨',
        };
        return icons[serviceType] || '💇‍♀️';
    }

    function renderServices() {
        const html = state.services.map(service => `
            <li class="service-card" data-service-id="${service.id}" role="button" tabindex="0" aria-label="${service.name}, ${service.price}₽, ${service.duration_minutes} мин">
                <span class="service-icon">${getServiceIcon(service.service_type)}</span>
                <div class="service-info">
                    <span class="service-name">${service.name}</span>
                    <div class="service-meta">
                        <span>${service.duration_minutes} мин</span>
                        <span>${service.description}</span>
                    </div>
                </div>
                <span class="service-price">${service.price}₽</span>
                <svg class="service-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </li>
        `).join('');
        elements.servicesList.innerHTML = html;

        elements.servicesList.querySelectorAll('.service-card').forEach(card => {
            card.addEventListener('click', () => selectService(parseInt(card.dataset.serviceId)));
            card.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectService(parseInt(card.dataset.serviceId));
                }
            });
        });
    }

    async function selectService(serviceId) {
        const service = state.services.find(s => s.id === serviceId);
        if (!service) return;

        state.selectedService = service;

        if (elements.dateServiceName) {
            elements.dateServiceName.textContent = service.name;
            elements.dateServicePrice.textContent = `${service.price}₽`;
        }
        if (elements.timeServiceName) {
            elements.timeServiceName.textContent = service.name;
        }
        if (elements.formService) {
            elements.formService.textContent = service.name;
        }
        if (elements.formPrice) {
            elements.formPrice.textContent = `${service.price}₽`;
        }
        if (elements.selectedServiceDate) {
            elements.selectedServiceDate.querySelector('.service-icon').textContent = getServiceIcon(service.service_type);
            elements.selectedServiceDate.querySelector('.service-name').textContent = service.name;
            elements.selectedServiceDate.querySelector('.service-price').textContent = `${service.price}₽`;
        }
        if (elements.selectedServiceTime) {
            elements.selectedServiceTime.querySelector('.service-icon').textContent = getServiceIcon(service.service_type);
            elements.selectedServiceTime.querySelector('.service-name').textContent = service.name;
        }

        const dates = await fetchAvailableDates(serviceId);
        renderDates(dates);
        showScreen('screen-date');
    }

    function renderDates(dates) {
        const html = dates.map(dateObj => {
            const date = new Date(dateObj.date + 'T00:00:00');
            const isSelected = state.selectedDate?.toISOString().split('T')[0] === dateObj.date;

            return `
                <div class="date-card${isSelected ? ' selected' : ''}${!dateObj.has_slots ? ' unavailable' : ''}" 
                     data-date="${dateObj.date}" 
                     role="button" tabindex="0"
                     aria-label="${formatDate(date)}, ${dateObj.has_slots ? 'есть свободное время' : 'нет мест'}">
                    <div class="date-info">
                        <span class="date-day">${getDayName(date)}</span>
                        <span class="date-full">${formatDate(date)}</span>
                        ${dateObj.has_slots ? '<span class="date-available">Есть свободное время</span>' : '<span class="date-available" style="color:var(--error)">Мест нет</span>'}
                    </div>
                    <svg class="date-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </div>
            `;
        }).join('');
        elements.datesList.innerHTML = html;

        elements.datesList.querySelectorAll('.date-card:not(.unavailable)').forEach(card => {
            card.addEventListener('click', () => selectDate(card.dataset.date));
            card.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectDate(card.dataset.date);
                }
            });
        });
    }

    async function selectDate(dateKey) {
        const date = new Date(dateKey + 'T00:00:00');
        state.selectedDate = date;

        if (elements.timeServiceDate) {
            elements.timeServiceDate.textContent = formatDate(date);
        }
        if (elements.formDatetime) {
            elements.formDatetime.textContent = `${formatDate(date)}, время будет выбрано`;
        }

        const slots = await fetchAvailableSlots(state.selectedService.id, dateKey);
        renderTimeSlots(slots);
        showScreen('screen-time');
    }

    function renderTimeSlots(slots) {
        const html = slots.map(slot => {
            const isSelected = state.selectedTime === slot.start_time;

            return `
                <button class="time-slot${isSelected ? ' selected' : ''}" 
                        data-time="${slot.start_time}"
                        data-slot-id="${slot.id}"
                        aria-label="${slot.start_time}, свободно">
                    ${slot.start_time}
                </button>
            `;
        }).join('');
        elements.timeSlots.innerHTML = html;

        elements.timeSlots.querySelectorAll('.time-slot').forEach(btn => {
            btn.addEventListener('click', () => selectTime(btn.dataset.time, btn.dataset.slotId));
        });
    }

    function selectTime(time, slotId) {
        state.selectedTime = time;
        state.selectedSlotId = parseInt(slotId);

        if (elements.formDatetime) {
            elements.formDatetime.textContent = `${formatDate(state.selectedDate)}, ${time}`;
        }

        showScreen('screen-form');
        setTimeout(() => elements.clientName?.focus(), 100);
    }

    function validatePhone(phone) {
        const cleaned = phone.replace(/\D/g, '');
        return cleaned.length >= 10 && cleaned.length <= 11;
    }

    function formatPhoneDisplay(phone) {
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 11) {
            return `+7 (${cleaned.slice(1,4)}) ${cleaned.slice(4,7)}-${cleaned.slice(7,9)}-${cleaned.slice(9)}`;
        }
        if (cleaned.length === 10) {
            return `+7 (${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6,8)}-${cleaned.slice(8)}`;
        }
        return phone;
    }

    function setupFormValidation() {
        if (!elements.bookingForm) return;

        elements.clientPhone?.addEventListener('input', e => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.slice(0, 11);
            if (value.startsWith('8')) value = '7' + value.slice(1);

            let formatted = '+7';
            if (value.length >= 2) formatted += ' (' + value.slice(1, 4);
            if (value.length >= 4) formatted += ') ' + value.slice(4, 7);
            if (value.length >= 7) formatted += '-' + value.slice(7, 9);
            if (value.length >= 9) formatted += '-' + value.slice(9, 11);

            e.target.value = formatted;
        });

        elements.bookingForm.addEventListener('submit', handleBookingSubmit);

        [elements.clientName, elements.clientPhone].forEach(input => {
            input?.addEventListener('input', () => clearError(input));
            input?.addEventListener('blur', () => validateField(input));
        });
    }

    function clearError(input) {
        input.classList.remove('error');
        const errorEl = document.getElementById(`${input.id}-error`);
        if (errorEl) errorEl.classList.remove('visible');
    }

    function validateField(input) {
        if (input.required && !input.value.trim()) {
            showError(input, 'Это поле обязательно');
            return false;
        }
        if (input.type === 'tel' && input.value.trim() && !validatePhone(input.value)) {
            showError(input, 'Введите корректный номер телефона');
            return false;
        }
        return true;
    }

    function showError(input, message) {
        input.classList.add('error');
        const errorEl = document.getElementById(`${input.id}-error`);
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.add('visible');
        }
    }

    function setLoading(button, loading) {
        if (!button) return;
        const text = button.querySelector('.btn-text');
        const loader = button.querySelector('.btn-loader');
        if (loading) {
            button.disabled = true;
            if (text) text.style.opacity = '0';
            if (loader) loader.hidden = false;
        } else {
            button.disabled = false;
            if (text) text.style.opacity = '1';
            if (loader) loader.hidden = true;
        }
    }

    async function handleBookingSubmit(e) {
        e.preventDefault();
        debugLog('handleBookingSubmit called');

        const nameValid = validateField(elements.clientName);
        const phoneValid = validateField(elements.clientPhone);

        if (!nameValid || !phoneValid) return;

        const data = {
            action: 'booking',
            service_id: state.selectedService.id,
            time_slot_id: state.selectedSlotId,
            client_name: elements.clientName.value.trim(),
            client_phone: elements.clientPhone.value.trim(),
            notes: elements.clientNotes?.value.trim() || '',
        };
        debugLog('Sending data to bot:', data);

        setLoading(elements.btnSubmit, true);

        try {
            await sendToBot(data);
            debugLog('Data sent successfully');
        } catch (err) {
            debugLog('Booking error:', err);
            showErrorScreen(err.message || 'Не удалось создать запись. Попробуйте позже.');
        } finally {
            setLoading(elements.btnSubmit, false);
        }
    }

    function sendToBot(data) {
        return new Promise((resolve, reject) => {
            if (!WebApp) {
                debugLog('No WebApp object, resolving mock');
                setTimeout(() => resolve({ ok: true }), 500);
                return;
            }

            debugLog('Calling WebApp.sendData with:', JSON.stringify(data));
            WebApp.sendData(JSON.stringify(data));
            setTimeout(() => {
                debugLog('Closing WebApp');
                WebApp.close();
                resolve({ ok: true });
            }, 100);
        });
    }

    function showSuccess(response) {
        const service = state.selectedService;
        const dateStr = formatDate(state.selectedDate);

        elements.bookingDetails.innerHTML = `
            <div class="detail-row">
                <span class="detail-label">Услуга</span>
                <span class="detail-value">${service.name}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Дата</span>
                <span class="detail-value">${dateStr}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Время</span>
                <span class="detail-value">${state.selectedTime}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Имя</span>
                <span class="detail-value">${response.client_name}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Телефон</span>
                <span class="detail-value">${formatPhoneDisplay(response.client_phone)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Цена</span>
                <span class="detail-value">${response.price}₽</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Номер заказа</span>
                <span class="detail-value">#${response.booking_id}</span>
            </div>
        `;

        state.selectedService = null;
        state.selectedDate = null;
        state.selectedTime = null;
        state.selectedSlotId = null;

        showScreen('screen-success');
    }

    function showErrorScreen(message) {
        elements.errorMessage.textContent = message;
        showScreen('screen-error');
    }

    function setupContest() {
        state.riddle = CONFIG.RIDDLES[Math.floor(Math.random() * CONFIG.RIDDLES.length)];
        if (elements.riddleText) {
            elements.riddleText.textContent = state.riddle;
        }
        elements.contestForm?.addEventListener('submit', handleContestSubmit);
    }

    async function handleContestSubmit(e) {
        e.preventDefault();

        const answer = elements.contestAnswer?.value.trim().toLowerCase();
        const name = elements.contestName?.value.trim();
        const phone = elements.contestPhone?.value.trim();

        if (!answer || !name || !phone) {
            showContestError('Заполните все поля');
            return;
        }

        if (!validatePhone(phone)) {
            showContestError('Введите корректный номер телефона');
            return;
        }

        const correctAnswers = CONFIG.RIDDLE_ANSWERS[state.riddle] || [];
        const isCorrect = correctAnswers.some(a => answer.includes(a.toLowerCase()));

        setLoading(elements.btnContestSubmit, true);

        try {
            await sendToBot({
                action: 'contest',
                answer: elements.contestAnswer.value.trim(),
                client_name: name,
                client_phone: phone,
            });
        } catch (err) {
            debugLog('Contest error:', err);
            showContestError(err.message || 'Не удалось отправить ответ. Попробуйте позже.');
        } finally {
            setLoading(elements.btnContestSubmit, false);
        }
    }

    function showContestError(message) {
        elements.contestErrorMessage.textContent = message;
        showScreen('screen-contest-error');
    }

    function bindGlobalEvents() {
        document.querySelectorAll('.btn-back').forEach(btn => {
            btn.addEventListener('click', goBack);
        });

        elements.btnCloseSuccess?.addEventListener('click', closeWebApp);
        elements.btnCloseContest?.addEventListener('click', closeWebApp);

        elements.btnErrorBack?.addEventListener('click', goBack);
        elements.btnErrorRetry?.addEventListener('click', () => {
            if (state.selectedTime) showScreen('screen-time');
            else if (state.selectedDate) showScreen('screen-date');
            else if (state.selectedService) showScreen('screen-services');
            else showScreen('screen-services');
        });

        elements.btnContestRetry?.addEventListener('click', () => showScreen('screen-contest'));

        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') {
                goBack();
            }
        });

        if (WebApp) {
            WebApp.onEvent('backButtonClicked', goBack);
            WebApp.BackButton.show();
        }
    }

    async function init() {
        initElements();
        await fetchServices();
        renderServices();
        setupFormValidation();
        setupContest();
        bindGlobalEvents();

        if (WebApp) {
            WebApp.onEvent('themeChanged', () => {
                document.documentElement.style.setProperty('--bg-primary', WebApp.backgroundColor || '#f8f9fa');
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();