const tg = window.Telegram.WebApp;
tg.expand();

// === STATE ===
let state = {
    myPrograms: JSON.parse(localStorage.getItem('myPrograms')) || [],
    rituals: JSON.parse(localStorage.getItem('rituals')) || [
        { id: 1, title: 'Ранний подъем', done: false, type: 'body' },
        { id: 2, title: 'Чтение 10 стр', done: false, type: 'mind' }
    ],
    missions: JSON.parse(localStorage.getItem('missions')) || [],
};

// === USER PROFILE ===
let userProfile = JSON.parse(localStorage.getItem('userProfile')) || { weight: 75, height: 180, age: 25, goal: 'lose', sport: 'none' };
let userSettings = JSON.parse(localStorage.getItem('userSettings')) || { lang: 'ru', theme: 'dark' };

// MAPS
const goalMap = { 'lose': 'Похудение', 'main': 'Баланс', 'gain': 'Набор массы' };
const sportMap = { 'none': 'Нет', 'gym': 'Зал', 'basketball': 'Баскетбол', 'boxing': 'Бокс', 'football': 'Футбол' };
const langMap = { 'ru': 'Русский', 'en': 'English' };
const themeMap = { 'dark': 'Тёмная', 'light': 'Светлая' };

function init() {
    if (tg.initDataUnsafe?.user?.id) userId = tg.initDataUnsafe.user.id;

    // Reset rituals
    const lastLogin = localStorage.getItem('lastLoginDate');
    const today = new Date().toDateString();
    if (lastLogin !== today) {
        state.rituals.forEach(r => r.done = false);
        localStorage.setItem('lastLoginDate', today);
        saveState();
    }

    // Default types
    state.missions.forEach(m => { if (!m.type) m.type = 'wealth'; });

    renderRituals();
    renderMissions();
    renderMyPrograms();
    updateRings();

    // Init Avatar
    if (tg.initDataUnsafe?.user?.photo_url) {
        const img = document.getElementById('user-avatar-img');
        const ph = document.getElementById('user-avatar-placeholder');
        if (img && ph) {
            img.src = tg.initDataUnsafe.user.photo_url;
            img.style.display = 'block';
            ph.style.display = 'none';
        }
    }

    loadProfile();
    loadSettings();
}

// === UI ===
function switchTab(name) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    const target = document.getElementById(`tab-${name}`);
    if (target) target.classList.add('active');

    if (name === 'home') document.querySelectorAll('.nav-item')[0].classList.add('active');
    if (name === 'profile') document.querySelectorAll('.nav-item')[1].classList.add('active');
    if (name === 'food') document.querySelectorAll('.nav-item')[2].classList.add('active');
    if (name === 'settings') document.querySelectorAll('.nav-item')[3].classList.add('active');
}
function toggleMenu() {
    document.getElementById('side-menu').classList.toggle('active');
    document.getElementById('menu-overlay').classList.toggle('active');
}

// === TASKS ===
function toggleTask(id, type) {
    let task = state.rituals.find(r => r.id === id);
    if (!task) task = state.missions.find(m => m.id === id);
    if (task) {
        task.done = !task.done;
        saveState();
        if (state.rituals.find(r => r.id === id)) renderRituals(); else renderMissions();
        updateRings();
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    }
}
let activeAddCategory = 'mission';
function openAddMissionModal(category = 'mission') {
    activeAddCategory = category;
    document.getElementById('new-mission-input').value = '';
    document.getElementById('modal-add-mission').classList.add('active');
    setTimeout(() => document.getElementById('new-mission-input').focus(), 100);
}
function closeAddMissionModal() { document.getElementById('modal-add-mission').classList.remove('active'); }
function confirmAddMission() {
    let title = document.getElementById('new-mission-input').value;
    if (!title) return;
    title = title.charAt(0).toUpperCase() + title.slice(1);
    const type = activeAddCategory === 'ritual' ? 'body' : classifyTask(title);
    const newItem = { id: Date.now(), title: title, done: false, type: type };
    if (activeAddCategory === 'ritual') state.rituals.push(newItem);
    else state.missions.push(newItem);
    saveState();
    activeAddCategory === 'ritual' ? renderRituals() : renderMissions();
    updateRings();
    closeAddMissionModal();
}
function classifyTask(text) {
    const t = text.toLowerCase();
    const bodyKeys = ['зал', 'спорт', 'трен', 'бег', 'отжим', 'турник', 'подъем', 'сон', 'вес', 'диет', 'ходьб', 'бокс', 'баскет', 'футбол', 'пресс'];
    if (bodyKeys.some(k => t.includes(k))) return 'body';
    const mindKeys = ['чте', 'книг', 'медит', 'учеб', 'англ', 'урок', 'курс', 'ум', 'развит', 'слуш', 'подкаст'];
    if (mindKeys.some(k => t.includes(k))) return 'mind';
    return 'wealth';
}
function startVoiceInput() { alert("Используйте клавиатуру"); }
function deleteMission(e, id) {
    e.stopPropagation();
    state.missions = state.missions.filter(m => m.id !== id);
    saveState(); renderMissions(); updateRings();
}
function renderRituals() {
    const list = document.getElementById('rituals-list'); list.innerHTML = '';
    state.rituals.forEach(r => {
        const div = document.createElement('div');
        div.className = `task-card ritual ${r.done ? 'done' : ''}`;
        div.onclick = () => toggleTask(r.id, 'ritual');
        div.innerHTML = `<div class="check-circle"><i class="fa-solid fa-check"></i></div><div class="task-info"><div class="task-title">${r.title}</div></div>`;
        list.appendChild(div);
    });
}
function renderMissions() {
    const list = document.getElementById('missions-list');
    if (state.missions.length === 0) { list.innerHTML = `<div class="empty-state">Нет задач на сегодня</div>`; return; }
    list.innerHTML = '';
    state.missions.forEach(m => {
        const div = document.createElement('div');
        div.className = `task-card mission ${m.done ? 'done' : ''}`;
        div.onclick = () => toggleTask(m.id, 'mission');
        div.innerHTML = `
            <div class="check-circle"><i class="fa-solid fa-check"></i></div>
            <div class="task-info"><div class="task-title">${m.title}</div><div class="task-desc">Цель</div></div>
            <button class="del-btn" onclick="deleteMission(event, ${m.id})">✕</button>
        `;
        list.appendChild(div);
    });
}
function updateRings() {
    const all = [...state.rituals, ...state.missions];
    let tBody = 0, dBody = 0, tMind = 0, dMind = 0, tWealth = 0, dWealth = 0;
    all.forEach(t => {
        const type = t.type || 'wealth';
        if (type === 'body') { tBody++; if (t.done) dBody++; }
        else if (type === 'mind') { tMind++; if (t.done) dMind++; }
        else { tWealth++; if (t.done) dWealth++; }
    });
    setProgress('ring-body', tBody === 0 ? 0 : (dBody / tBody) * 100);
    setProgress('ring-mind', tMind === 0 ? 0 : (dMind / tMind) * 100);
    setProgress('ring-wealth', tWealth === 0 ? 0 : (dWealth / tWealth) * 100);
}
function setProgress(id, pct) {
    const c = document.getElementById(id);
    const r = c.r.baseVal.value;
    const circ = 2 * Math.PI * r;
    c.style.strokeDasharray = `${circ} ${circ}`;
    c.style.strokeDashoffset = circ - (pct / 100) * circ;
}

// === GYM LOGIC ===
function openCatalog() {
    const ac = document.getElementById('catalog-academies');
    const ge = document.getElementById('catalog-general');

    // Clear existing
    if (ac) ac.innerHTML = '';
    if (ge) ge.innerHTML = '';

    Object.keys(workoutsDB).forEach(key => {
        const p = workoutsDB[key];
        const div = document.createElement('div');

        // Distinguish Academies vs Programs based on ID or custom logic
        // Academies usually have "academy" in id or are main sports
        const isAcademy = key.includes('academy') || key === 'football' || key === 'boxing' || key === 'wrestling';

        if (isAcademy) {
            div.className = 'academy-card';
            div.innerHTML = `<div class="card-icon">${p.icon}</div><div class="card-title">${p.title}</div>`;
            if (ac) ac.appendChild(div);
        } else {
            div.className = 'program-card';
            div.innerHTML = `<div class="prog-icon">${p.icon}</div><div><div class="card-title">${p.title}</div><div class="card-desc" style="font-size:12px; color:#666">${p.desc}</div></div>`;
            if (ge) ge.appendChild(div);
        }

        div.onclick = () => openProgram(p.id);
    });

    document.getElementById('modal-catalog').classList.add('active');
}
function closeCatalog() {
    document.getElementById('modal-catalog').classList.remove('active');
}

let activeProgramId = null;

function openProgram(progId) {
    activeProgramId = progId;
    const prog = workoutsDB[progId];
    if (!prog) return;

    // 1. Setup Header
    const modal = document.getElementById('modal-program');
    modal.querySelector('.modal-title').innerText = prog.title;

    // 2. Render Content
    const container = document.getElementById('prog-details');
    container.innerHTML = '';

    prog.months.forEach(month => {
        const mDiv = document.createElement('div');
        mDiv.className = 'month-card';
        mDiv.innerHTML = `<h3 class="month-title" style="color:${prog.color}; border-color:${prog.color}">${month.title}</h3>`;

        month.days.forEach(day => {
            const uid = `d-${Math.random().toString(36).substr(2, 9)}`;

            // Build Exercise List
            const exHTML = day.exercises.map(ex => `
                <div class="ex-item">
                    <span>${ex.name}</span>
                    <span>${ex.sets}</span>
                </div>
            `).join('');

            // Build Day Card
            const dCard = document.createElement('div');
            dCard.className = 'day-card';
            dCard.innerHTML = `
                <div class="day-header" onclick="toggleDay('${uid}')">
                    <span>${day.title}</span>
                    <i id="icon-${uid}" class="fa-solid fa-chevron-down" style="color:#666; transition:0.3s"></i>
                </div>
                <div id="${uid}" class="ex-list">
                    ${exHTML}
                </div>
            `;
            mDiv.appendChild(dCard);
        });
        container.appendChild(mDiv);
    });

    // 3. Setup FAB Button (Add/Remove)
    const btn = document.getElementById('toggle-prog-btn');
    const isAdded = state.myPrograms.some(p => p.id === progId);

    // Reset classes
    btn.className = 'fab-btn';
    btn.style.display = 'flex'; // Ensure visible

    if (isAdded) {
        btn.classList.add('remove');
        btn.innerHTML = '<i class="fa-solid fa-trash"></i> УДАЛИТЬ';
        btn.onclick = () => removeProgram(progId);
    } else {
        btn.innerHTML = '<i class="fa-solid fa-plus"></i> ДОБАВИТЬ';
        btn.onclick = () => addProgram(progId);
        // Apply program color to button
        if (prog.color) btn.style.backgroundColor = prog.color;
    }

    modal.classList.add('active');
}

function closeProgram() {
    document.getElementById('modal-program').classList.remove('active');
}

function toggleDay(uid) {
    const content = document.getElementById(uid);
    const icon = document.getElementById(`icon-${uid}`);

    if (content.style.display === 'block') {
        content.style.display = 'none';
        if (icon) icon.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'block';
        if (icon) icon.style.transform = 'rotate(180deg)';
    }
}

function addProgram(id) {
    if (!state.myPrograms.some(p => p.id === id)) {
        state.myPrograms.push({ id });
        saveState();
        renderMyPrograms();
        openProgram(id); // Re-render to show delete button
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
    }
}

function removeProgram(id) {
    state.myPrograms = state.myPrograms.filter(p => p.id !== id);
    saveState();
    renderMyPrograms();
    closeProgram();
    if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('warning');
}

function renderMyPrograms() {
    const grid = document.getElementById('my-programs-grid');
    // Keep 'Add' card, remove others
    const addCard = grid.querySelector('.add-prog-card');
    grid.innerHTML = '';
    grid.appendChild(addCard); // Put it back at the end or begin? Usually begin is better for UX if list is long, but design shows add last.
    // Actually, let's prepend programs.

    state.myPrograms.forEach(pObj => {
        const prog = workoutsDB[pObj.id];
        if (!prog) return;

        const div = document.createElement('div');
        div.className = 'academy-card';
        div.onclick = () => openProgram(pObj.id);
        div.innerHTML = `
            <div class="card-icon">${prog.icon}</div>
            <div class="card-title">${prog.title}</div>
        `;
        grid.prepend(div);
    });
}


// === PROFILE ===
function loadProfile() {
    if (tg.initDataUnsafe?.user?.first_name) document.getElementById('user-name-display').innerText = tg.initDataUnsafe.user.first_name;
    document.getElementById('disp-weight').innerText = userProfile.weight || '-';
    document.getElementById('disp-height').innerText = userProfile.height || '-';
    document.getElementById('disp-age').innerText = userProfile.age || 25;

    document.getElementById('disp-goal').innerText = goalMap[userProfile.goal] || 'Похудение';
    document.getElementById('disp-sport').innerText = sportMap[userProfile.sport] || 'Нет';

    calcCalories();
}
function editStat(type) {
    if (type === 'weight') {
        const val = prompt('Ваш вес (кг):', userProfile.weight);
        if (val) userProfile.weight = parseInt(val);
    } else if (type === 'height') {
        const val = prompt('Ваш рост (см):', userProfile.height);
        if (val) userProfile.height = parseInt(val);
    } else if (type === 'age') {
        const val = prompt('Ваш возраст:', userProfile.age || 25);
        if (val) userProfile.age = parseInt(val);
    }
    localStorage.setItem('userProfile', JSON.stringify(userProfile));
    loadProfile();
}

// === TRANSLATIONS ===
const TRANSLATIONS = {
    ru: {
        side_menu: "М Е Н Ю",
        side_gym: "Спортивный Зал",
        side_meditation: "Медитации",
        side_finance: "Финансы",
        side_settings: "Настройки",
        home_balance: "БАЛАНС",
        ring_body: "ТЕЛО",
        ring_mind: "ДУХ",
        ring_wealth: "ДЕНЬГИ",
        home_rituals: "РИТУАЛЫ",
        home_missions: "ЦЕЛИ НА ДЕНЬ",
        home_no_tasks: "Нет задач",
        modal_new_mission: "НОВАЯ ЦЕЛЬ",
        placeholder_mission: "Введите цель...",
        cancel: "ОТМЕНА",
        food_kcal_norm: "ККАЛ / ДЕНЬ (НОРМА)",
        food_calc_basis: "Расчет на основе вашего профиля",
        profile_physics: "Тело",
        profile_weight: "Вес",
        profile_height: "Рост",
        profile_age: "Возраст",
        profile_strategy: "Стратегия",
        profile_goal: "Цель",
        profile_activity: "Активность",
        settings_title: "НАСТРОЙКИ",
        settings_app_section: "Приложение",
        settings_lang: "Язык",
        settings_theme: "Тема",
        settings_lang_ru: "Русский",
        settings_lang_en: "English",
        settings_theme_dark: "Тёмная",
        settings_theme_light: "Светлая",
        settings_support: "Поддержка"
    },
    en: {
        side_menu: "M E N U",
        side_gym: "Gym & Workout",
        side_meditation: "Meditations",
        side_finance: "Finance",
        side_settings: "Settings",
        home_balance: "BALANCE",
        ring_body: "BODY",
        ring_mind: "MIND",
        ring_wealth: "WEALTH",
        home_rituals: "RITUALS",
        home_missions: "DAILY GOALS",
        home_no_tasks: "No tasks for today",
        modal_new_mission: "NEW GOAL",
        placeholder_mission: "Enter goal...",
        cancel: "CANCEL",
        food_kcal_norm: "KCAL / DAY (TARGET)",
        food_calc_basis: "Calculated based on your profile",
        profile_physics: "Body Stats",
        profile_weight: "Weight",
        profile_height: "Height",
        profile_age: "Age",
        profile_strategy: "Strategy",
        profile_goal: "Goal",
        profile_activity: "Activity",
        settings_title: "SETTINGS",
        settings_app_section: "Application",
        settings_lang: "Language",
        settings_theme: "Theme",
        settings_lang_ru: "Russian",
        settings_lang_en: "English",
        settings_theme_dark: "Dark",
        settings_theme_light: "Light",
        settings_support: "Support"
    }
};

function applyLanguage(lang) {
    const texts = TRANSLATIONS[lang];
    if (!texts) return;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (texts[key]) {
            if (el.getAttribute('data-i18n-attr')) el.setAttribute(el.getAttribute('data-i18n-attr'), texts[key]);
            else el.innerText = texts[key];
        }
    });
}
// === FOOD AI & VISION ===
function triggerCamera() {
    document.getElementById('camera-input').click();
}

function handleFoodPhoto(input) {
    const file = input.files[0];
    if (!file) return;

    // Show Loading
    const btnBox = document.querySelector('.cal-sub').parentElement;
    const originalText = btnBox.innerHTML;
    // Simple spinner overlay or just modify button text
    // ...

    const reader = new FileReader();
    reader.onloadend = function () {
        const base64 = reader.result.split(',')[1]; // Remove header for safety if API handles raw b64
        // BUT our API handles full base64 string
        const fullBase64 = reader.result;

        const uid = tg.initDataUnsafe?.user?.id || 'test';
        // Relative path works if served from same origin
        // If testing locally, need distinct URL

        fetch(`/api/user/${uid}/add_food`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_base64: fullBase64 })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    updateFoodUI(data);
                    alert(`Добавлено: ${data.history[0].name} (+${data.history[0].cal} ккал)`);
                } else {
                    alert('Ошибка анализа: ' + JSON.stringify(data));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ошибка сети или сервера');
            });
    }
    reader.readAsDataURL(file);
}

function openManualFoodInput() {
    document.getElementById('food-text-input').value = '';
    document.getElementById('modal-add-food-text').classList.add('active');
}

function confirmFoodText() {
    const text = document.getElementById('food-text-input').value.trim();
    if (!text) {
        alert('Введите название еды');
        return;
    }

    document.getElementById('modal-add-food-text').classList.remove('active');

    // Show Loading
    const btn = document.querySelector('[onclick="openManualFoodInput()"]');
    const originalText = btn.innerHTML;
    // Just a basic visual feedback
    // ...

    const uid = tg.initDataUnsafe?.user?.id || 'test';

    fetch(`/api/user/${uid}/add_food`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                updateFoodUI(data);
                if (confirm(`Добавлено: ${data.history[0].name} (+${data.history[0].cal} ккал).\nДобавить ещё?`)) {
                    openManualFoodInput(); // Loop for convenience
                }
            }
        })
        .catch(error => {
            alert('Ошибка: ' + error);
            // Maybe open modal again if failed?
        });
}

function updateFoodUI(data) {
    if (!data.nutrition) return;

    // Update Calories
    const el = document.getElementById('disp-calories');
    if (el) {
        // Simple count-up animation
        let start = parseInt(el.innerText) || 0;
        let end = data.nutrition.consumed;
        el.innerText = end;
    }

    // Update Rings
    const p = data.nutrition.protein || 0;
    const f = data.nutrition.fat || 0;
    const c = data.nutrition.carbs || 0;

    // Goals (Static defaults for now, can come from profile)
    const pGoal = 150;
    const fGoal = 100;
    const cGoal = 300;

    setProgressNew('ring-protein', (p / pGoal) * 100);
    setProgressNew('ring-fat', (f / fGoal) * 100);
    setProgressNew('ring-carbs', (c / cGoal) * 100);

    // Show Rating
    if (data.history && data.history.length > 0) {
        const item = data.history[0]; // Newest
        const card = document.getElementById('food-rating-card');

        if (item.rating || item.rating === 0) {
            card.style.display = 'block';
            const rVal = document.getElementById('rating-val');
            rVal.innerText = item.rating;
            document.getElementById('rating-text').innerText = item.rating_desc || '';

            // Color Logic
            const val = parseFloat(item.rating);
            if (val >= 8) rVal.style.color = '#30D158'; // Green
            else if (val >= 5) rVal.style.color = '#FFD60A'; // Yellow
            else rVal.style.color = '#FF375F'; // Red
        }
    }
}

function setProgressNew(id, pct) {
    const ring = document.getElementById(id);
    if (!ring) return;

    pct = parseFloat(pct) || 0;
    if (pct > 100) pct = 100;
    if (pct < 0) pct = 0;

    const r = parseFloat(ring.getAttribute('r')) || 20;
    const circumference = 2 * Math.PI * r;

    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    const offset = circumference - (pct / 100) * circumference;

    if (!isNaN(offset)) {
        ring.style.strokeDashoffset = offset;
    }
}



function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'light') {
        tg.setBackgroundColor('#F2F2F7');
        tg.setHeaderColor('#F2F2F7');
    } else {
        tg.setBackgroundColor('#000000');
        tg.setHeaderColor('#000000');
    }
}

// === SETTINGS ===
function loadSettings() {
    // Reset visuals
    document.querySelectorAll('.segment-opt').forEach(el => {
        el.classList.remove('active');
        el.classList.remove('blue');
    });

    // Set Active
    const l = userSettings.lang || 'ru';
    const t = userSettings.theme || 'dark';

    const langEl = document.getElementById(`seg-lang-${l}`);
    const themeEl = document.getElementById(`seg-theme-${t}`);

    if (langEl) { langEl.classList.add('active'); langEl.classList.add('blue'); }
    if (themeEl) { themeEl.classList.add('active'); themeEl.classList.add('blue'); }

    // APPLY LOGIC
    applyLanguage(l);
    applyTheme(t);
}

function setSetting(key, val) {
    userSettings[key] = val;
    localStorage.setItem('userSettings', JSON.stringify(userSettings));
    loadSettings();
    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

// ACTION SELECTOR
function openSelector(type) { document.getElementById(`sheet-${type}`).classList.add('active'); }
function closeSelector(type) { document.getElementById(`sheet-${type}`).classList.remove('active'); }
function setProfileVal(key, val) {
    userProfile[key] = val;
    localStorage.setItem('userProfile', JSON.stringify(userProfile));
    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    loadProfile();
    closeSelector(key);
}

function calcCalories() {
    const w = userProfile.weight || 75; const h = userProfile.height || 180; const a = userProfile.age || 25;
    let bmr = (10 * w) + (6.25 * h) - (5 * a) + 5;
    let tdee = bmr * 1.2;
    const bonuses = { 'none': 0, 'gym': 400, 'basketball': 500, 'boxing': 600, 'football': 500 };
    tdee += (bonuses[userProfile.sport] || 0);
    if (userProfile.goal === 'lose') tdee *= 0.85;
    if (userProfile.goal === 'gain') tdee *= 1.15;
    const el = document.getElementById('disp-calories');
    if (el) el.innerText = Math.round(tdee);
}
function saveState() {
    localStorage.setItem('myPrograms', JSON.stringify(state.myPrograms));
    localStorage.setItem('rituals', JSON.stringify(state.rituals));
    localStorage.setItem('missions', JSON.stringify(state.missions));
    localStorage.setItem('userProfile', JSON.stringify(userProfile));
    localStorage.setItem('userSettings', JSON.stringify(userSettings));
}

init();
