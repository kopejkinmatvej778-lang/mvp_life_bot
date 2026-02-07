// GYM V3 - ULTIMATE WORKOUT EXPERIENCE
// Fullscreen workout mode with focused single exercise view

const GymV3 = {
    // State
    currentProgram: null,
    currentDayIndex: 0,
    currentExerciseIndex: 0,
    currentSet: 1,       // Current set number (1, 2, 3, 4...)
    totalSets: 4,        // Total sets for current exercise
    workoutActive: false,
    workoutStartTime: null,
    mainTimer: null,
    restTimer: null,
    exerciseTimer: null,
    restSeconds: 0,

    // Blue color for workout mode only
    WORKOUT_COLOR: '#007AFF',

    // Motivational messages
    motivationalMessages: [
        { icon: '💧', text: 'Пей воду' },
        { icon: '🌬️', text: 'Глубоко дыши' },
        { icon: '💪', text: 'Ты справляешься!' },
        { icon: '🔥', text: 'Жги калории!' },
        { icon: '🎯', text: 'Фокус на цели' },
        { icon: '⚡', text: 'Восстанавливай силы' }
    ],

    init() {
        if (!DB.data.activePrograms) {
            DB.data.activePrograms = [];
            DB.save();
        }
        this.createWorkoutOverlay();
        this.ensureRestOverlay();
        this.renderMyPrograms();
    },

    // Create fullscreen workout overlay
    createWorkoutOverlay() {
        if (document.getElementById('workout-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'workout-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(180deg, #0a0a0a 0%, #111 50%, #0a0a0a 100%);
            z-index: 9999;
            display: none;
            flex-direction: column;
            padding: 20px;
            padding-top: env(safe-area-inset-top, 20px);
            padding-bottom: env(safe-area-inset-bottom, 20px);
            overflow-y: auto;
        `;
        overlay.innerHTML = `
            <div id="workout-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <style>
                    @keyframes heartbeat-pulse {
                        0% { transform: scale(1); opacity: 1; }
                        15% { transform: scale(1.15); opacity: 1; }
                        30% { transform: scale(1); opacity: 1; }
                        45% { transform: scale(1.15); opacity: 1; }
                        60% { transform: scale(1); opacity: 1; }
                        100% { transform: scale(1); opacity: 1; }
                    }
                    .timer-heartbeat {
                        animation: heartbeat-pulse 0.8s ease-in-out infinite;
                        color: #FF375F !important; /* Red color for intensity */
                        text-shadow: 0 0 20px rgba(255, 55, 95, 0.5);
                    }
                </style>
                <div style="width:44px;"></div> <!-- Spacer for centering -->
                <div style="text-align:center;">
                    <div id="workout-timer-display" style="font-size:28px; font-weight:700; color:#fff; font-variant-numeric:tabular-nums;">00:00</div>
                    <div style="font-size:11px; color:#666; text-transform:uppercase; letter-spacing:1px;">время</div>
                </div>
                <!-- Finish Button (Top Right) -->
                <button onclick="GymV3.exitWorkout()" style="background:rgba(255,59,48,0.2); border:1px solid rgba(255,59,48,0.3); color:#FF3B30; font-size:14px; font-weight:600; cursor:pointer; padding:8px 14px; border-radius:12px;">
                    Конец
                </button>
            </div>
            <div id="workout-content" style="flex:1; display:flex; flex-direction:column; justify-content:center;">
                <!-- Current exercise will be rendered here -->
            </div>
        `;
        document.body.appendChild(overlay);
    },

    // Ensure rest overlay exists
    ensureRestOverlay() {
        let overlay = document.getElementById('rest-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'rest-overlay';
            document.body.appendChild(overlay);
        }

        overlay.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(180deg, rgba(0,30,60,0.98) 0%, rgba(0,0,0,0.98) 100%);
            z-index: 10000;
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        `;

        overlay.innerHTML = `
            <div id="rest-motivation" style="font-size:60px; margin-bottom:10px; animation: bounce 2s infinite;">💧</div>
            <div id="rest-motivation-text" style="font-size:18px; color:#888; margin-bottom:50px;">Пей воду</div>
            
            <div style="position:relative; width:200px; height:200px; margin-bottom:50px;">
                <div style="
                    position:absolute; top:0; left:0; right:0; bottom:0;
                    border-radius:50%; 
                    border:4px solid rgba(0,122,255,0.2);
                "></div>
                <div id="rest-progress-ring" style="
                    position:absolute; top:0; left:0; right:0; bottom:0;
                    border-radius:50%; 
                    border:4px solid #007AFF;
                    border-right-color: transparent;
                    border-bottom-color: transparent;
                    animation: spin-rest 1s linear infinite;
                "></div>
                <div style="
                    position:absolute; top:0; left:0; right:0; bottom:0;
                    display:flex; align-items:center; justify-content:center;
                ">
                    <div id="rest-timer-display" style="font-size:72px; font-weight:800; color:#fff;">60</div>
                </div>
            </div>
            
            <button onclick="GymV3.skipRest()" style="
                background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2);
                color:#fff; padding:16px 60px; border-radius:30px; font-size:16px; font-weight:600; cursor:pointer;
            ">Пропустить</button>
            
            <style>
                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-10px); }
                }
                @keyframes spin-rest {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            </style>
        `;
    },

    // Render My Programs - with ORIGINAL colors
    renderMyPrograms() {
        const container = document.getElementById('gym-programs');
        if (!container) return;

        const myProgs = DB.data.activePrograms || [];

        if (myProgs.length === 0) {
            container.innerHTML = `
                <div style="position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;">
                    <div style="font-size:70px; margin-bottom:20px;">🏋️</div>
                    <div style="font-size:22px; font-weight:700; color:#fff; margin-bottom:8px;">Начните тренироваться!</div>
                    <div style="font-size:14px; color:#888; max-width:280px; margin:0 auto 25px;">Выберите программу из каталога</div>
                    <button onclick="GymV3.showCatalog()" style="
                        background:linear-gradient(135deg, #007AFF 0%, #00D4FF 100%);
                        border:none; color:#fff; padding:16px 40px; border-radius:16px;
                        font-weight:700; font-size:16px; cursor:pointer;
                        box-shadow: 0 4px 25px rgba(0,122,255,0.4);
                    "><i class="fa-solid fa-dumbbell" style="margin-right:10px;"></i>Открыть Каталог</button>
                </div>
            `;
            return;
        }

        let html = '<div style="font-size:12px; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:15px;">Мои Программы</div>';

        for (let progId of myProgs) {
            const prog = workoutsDB[progId];
            if (!prog) continue;

            // Use ORIGINAL program color
            html += `
                <div class="gym-card" style="--card-color:${prog.color}; margin-bottom:15px;" onclick="GymV3.openProgram('${progId}')">
                    <div class="card-icon">${prog.icon}</div>
                    <h3>${prog.title}</h3>
                    <p>${prog.desc}</p>
                </div>
            `;
        }

        html += `
            <button onclick="GymV3.showCatalog()" style="
                width:100%; margin-top:15px; padding:14px;
                background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
                color:#fff; border-radius:14px; font-size:14px; cursor:pointer;
            "><i class="fa-solid fa-plus" style="margin-right:8px;"></i>Добавить программу</button>
        `;

        container.innerHTML = html;
    },

    // Show Catalog - with ORIGINAL colors
    showCatalog() {
        const container = document.getElementById('gym-programs');
        if (!container) return;

        const myProgs = DB.data.activePrograms || [];

        let html = `
            <button onclick="GymV3.renderMyPrograms()" style="
                background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.1);
                color:#fff; padding:10px 20px; border-radius:12px; font-size:14px;
                cursor:pointer; margin-bottom:20px; display:flex; align-items:center; gap:8px;
            "><i class="fa-solid fa-arrow-left"></i> Назад</button>
            <div style="font-size:12px; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:15px;">Каталог программ</div>
        `;

        for (let key of Object.keys(workoutsDB)) {
            const prog = workoutsDB[key];
            const isActive = myProgs.includes(key);

            const badge = isActive
                ? `<div style="position:absolute; top:15px; right:15px; background:rgba(46,204,113,0.2); color:#2ecc71; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:1px solid #2ecc71;"><i class="fa-solid fa-check" style="font-size:12px;"></i></div>`
                : `<div style="position:absolute; top:15px; right:15px; background:rgba(0,122,255,0.2); color:#007AFF; width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:1px solid #007AFF; z-index:10; cursor:pointer;" onclick="event.stopPropagation(); GymV3.addProgram('${key}'); return false;"><i class="fa-solid fa-plus" style="font-size:16px;"></i></div>`;

            // Use ORIGINAL program color
            // Wrapped in onclick to allow previewing from catalog, but prevent bad behaviour
            html += `
                <div class="gym-card" style="--card-color:${prog.color}; margin-bottom:15px; position:relative;" onclick="GymV3.openProgram('${key}')">
                    ${badge}
                    <div class="card-icon">${prog.icon}</div>
                    <h3>${prog.title}</h3>
                    <p>${prog.desc}</p>
                </div>
            `;
        }

        container.innerHTML = html;
    },

    addProgram(id) {
        console.log("Adding program:", id);
        if (!DB.data.activePrograms) DB.data.activePrograms = [];

        if (!DB.data.activePrograms.includes(id)) {
            DB.data.activePrograms.push(id);
            DB.save();

            // Visual feedback
            if (window.Telegram?.WebApp?.HapticFeedback) {
                Telegram.WebApp.HapticFeedback.notificationOccurred('success');
            }
            alert("Программа добавлена!");

            this.showCatalog();
        } else {
            alert("Программа уже добавлена");
        }
    },

    // Open Program - show days with ORIGINAL color
    openProgram(id) {
        this.currentProgram = workoutsDB[id];
        this.currentProgram.id = id;
        this.switchView('gym-days-view');

        document.getElementById('gym-program-title').innerText = this.currentProgram.title;

        const m1 = this.currentProgram.months[0];
        const listContainer = document.getElementById('gym-days-list');
        const color = this.currentProgram.color; // Original color

        let html = `<h4 style="color:rgba(255,255,255,0.3); margin:0 0 15px 5px; text-transform:uppercase; font-size:12px; letter-spacing:1px;">${m1.title}</h4>`;

        html += m1.days.map((day, idx) => `
            <div class="day-card" onclick="GymV3.startWorkout(${idx})" style="border-left-color:${color}">
                <div>
                    <h4>${day.title}</h4>
                    <span>${day.exercises.length} упражнений</span>
                </div>
                <button onclick="event.stopPropagation(); GymV3.startWorkout(${idx})" style="background:${color}; border:none; color:#000; padding:10px 20px; border-radius:12px; font-weight:700; cursor:pointer;">
                    <i class="fa-solid fa-play"></i> Начать
                </button>
            </div>
        `).join('');

        listContainer.innerHTML = html;
    },

    // START WORKOUT - Opens fullscreen overlay
    startWorkout(dayIdx) {
        this.currentDayIndex = dayIdx;
        this.currentExerciseIndex = 0;
        this.currentSet = 1;
        this.workoutActive = true;
        this.workoutStartTime = Date.now();

        // Parse sets for first exercise
        const day = this.currentProgram.months[0].days[dayIdx];
        const firstEx = day.exercises[0];
        this.totalSets = this.parseSetsCount(firstEx.sets);

        // Show fullscreen workout overlay
        document.getElementById('workout-overlay').style.display = 'flex';

        this.startMainTimer();
        this.renderCurrentExercise();
    },

    // Parse sets count from string like "4x8" -> 4
    parseSetsCount(setsStr) {
        const match = setsStr.match(/(\d+)\s*[xх×]/i);
        if (match) return parseInt(match[1]);
        return 4; // Default
    },

    // Parse reps from string like "4x8" -> 8
    parseReps(setsStr) {
        const match = setsStr.match(/[xх×]\s*(\d+)/i);
        if (match) return match[1];
        return setsStr;
    },

    // Exit workout (with confirmation)
    exitWorkout() {
        if (confirm('Завершить тренировку досрочно?')) {
            // Check if less than 15 mins
            const elapsedSeconds = Math.floor((Date.now() - this.workoutStartTime) / 1000);
            const minutes = Math.floor(elapsedSeconds / 60);

            if (minutes < 15) {
                if (confirm(`Прошло всего ${minutes} мин. Минимальное время - 15 мин. Если выйти сейчас, тренировка не засчитается. Выйти?`)) {
                    this.finishWorkout();
                }
            } else {
                this.finishWorkout();
            }
        }
    },

    // Main timer
    startMainTimer() {
        if (this.mainTimer) clearInterval(this.mainTimer);

        this.mainTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.workoutStartTime) / 1000);
            const m = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const s = (elapsed % 60).toString().padStart(2, '0');
            const el = document.getElementById('workout-timer-display');
            if (el) el.innerText = `${m}:${s}`;
        }, 1000);
    },

    // Render ONLY current exercise with SET info and TECHNIQUE placeholder
    renderCurrentExercise() {
        const day = this.currentProgram.months[0].days[this.currentDayIndex];

        // Check if finished
        if (this.currentExerciseIndex >= day.exercises.length) {
            this.finishWorkout();
            return;
        }

        const ex = day.exercises[this.currentExerciseIndex];
        const progress = `${this.currentExerciseIndex + 1}/${day.exercises.length}`;
        const isTimed = this.isTimedExercise(ex.sets);
        const color = this.WORKOUT_COLOR; // Blue inside workout

        // Update sets for this exercise
        this.totalSets = this.parseSetsCount(ex.sets);
        const reps = this.parseReps(ex.sets);

        // Render exercise card
        const content = document.getElementById('workout-content');

        if (isTimed) {
            const seconds = this.parseTimeToSeconds(ex.sets);
            content.innerHTML = `
                <div style="padding:20px;">
                    <!-- Timed Exercise Card - App Style -->
                    <div style="
                        background: var(--bg-card, #1c1c1e);
                        border-radius: var(--radius-l, 20px);
                        padding: 25px 20px;
                        margin-bottom: 15px;
                    ">
                        <!-- Exercise Number -->
                        <div style="
                            display:inline-block;
                            background:rgba(0,122,255,0.15);
                            color:#007AFF;
                            padding:6px 14px;
                            border-radius:20px;
                            font-size:12px;
                            font-weight:600;
                            margin-bottom:18px;
                        ">${this.currentExerciseIndex + 1} / ${day.exercises.length}</div>
                        
                        <!-- Exercise Name -->
                        <h2 style="font-size:22px; font-weight:700; color:#fff; margin:0 0 30px 0; line-height:1.3;">
                            ${ex.name}
                        </h2>
                        
                        <!-- Timer Display -->
                        <div id="exercise-timer" style="font-size:64px; font-weight:800; color:#007AFF; text-align:center; margin-bottom:30px;">
                            ${this.formatTime(seconds)}
                        </div>
                        
                        <!-- Start Button -->
                        <button id="start-timer-btn" onclick="GymV3.startExerciseTimer(${seconds})" style="
                            width:100%;
                            background: var(--primary, #007AFF);
                            border:none;
                            color:#fff;
                            padding:18px;
                            border-radius:var(--radius-m, 16px);
                            font-size:17px;
                            font-weight:600;
                            cursor:pointer;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            gap:10px;
                        "><i class="fa-solid fa-play"></i> СТАРТ</button>
                    </div>
                    
                    <!-- Action Buttons - App Style -->
                    <div style="display:flex; gap:12px;">
                        <button onclick="GymV3.showTechnique('${ex.name}')" style="
                            flex:1;
                            background: var(--bg-card, #1c1c1e);
                            border:none;
                            color:#007AFF;
                            padding:16px;
                            border-radius:var(--radius-m, 16px);
                            font-size:15px;
                            font-weight:600;
                            cursor:pointer;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            gap:8px;
                        "><i class="fa-solid fa-play-circle"></i> Техника</button>
                        
                        <button onclick="GymV3.skipExercise()" style="
                            flex:1;
                            background: var(--bg-card, #1c1c1e);
                            border:none;
                            color:var(--danger, #FF375F);
                            padding:16px;
                            border-radius:var(--radius-m, 16px);
                            font-size:15px;
                            font-weight:600;
                            cursor:pointer;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            gap:8px;
                        "><i class="fa-solid fa-forward"></i> Пропустить</button>
                    </div>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div style="padding:20px; display:flex; flex-direction:column; height:100%; justify-content:center;">
                    <!-- Premium Exercise Card -->
                    <div style="text-align:center; margin-bottom:40px;">
                        <div style="
                            display:inline-block; margin-bottom:15px;
                            padding:6px 16px; border-radius:30px;
                            background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
                            font-size:12px; letter-spacing:1px; text-transform:uppercase; color:rgba(255,255,255,0.6);
                        ">Упражнение ${this.currentExerciseIndex + 1} из ${day.exercises.length}</div>
                        
                        <h2 style="font-size:28px; font-weight:800; margin:0 0 10px 0; line-height:1.2; background: linear-gradient(180deg, #fff 0%, #ccc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            ${ex.name}
                        </h2>
                    </div>

                    <!-- Dynamic Circular Set Indicator -->
                    <div style="position:relative; width:180px; height:180px; margin:0 auto 40px; display:flex; align-items:center; justify-content:center;">
                        <!-- SVG Ring Background -->
                        <svg width="180" height="180" viewBox="0 0 180 180" style="position:absolute; transform: rotate(-90deg);">
                            <circle cx="90" cy="90" r="80" stroke="rgba(255,255,255,0.1)" stroke-width="8" fill="none"></circle>
                            <!-- Progress Arc -->
                            <circle cx="90" cy="90" r="80" stroke="#007AFF" stroke-width="8" fill="none"
                                stroke-dasharray="${2 * Math.PI * 80}"
                                stroke-dashoffset="${2 * Math.PI * 80 * (1 - this.currentSet / this.totalSets)}"
                                style="transition: stroke-dashoffset 0.5s ease; stroke-linecap: round;">
                            </circle>
                        </svg>
                        
                        <div style="text-align:center; z-index:2;">
                            <div style="font-size:13px; color:rgba(255,255,255,0.5); text-transform:uppercase; margin-bottom:5px;">Подход</div>
                            <div style="font-size:56px; font-weight:800; line-height:1;">${this.currentSet}<span style="font-size:24px; color:rgba(255,255,255,0.3); font-weight:400;">/${this.totalSets}</span></div>
                        </div>
                    </div>

                    <!-- Reps & Info -->
                    <div style="display:flex; justify-content:center; gap:30px; margin-bottom:40px;">
                        <div style="text-align:center;">
                            <i class="fa-solid fa-dumbbell" style="font-size:20px; color:#007AFF; margin-bottom:8px;"></i>
                            <div style="font-size:24px; font-weight:700;">${reps}</div>
                            <div style="font-size:11px; color:rgba(255,255,255,0.4); text-transform:uppercase;">Повторы</div>
                        </div>
                        <div style="width:1px; background:rgba(255,255,255,0.1);"></div>
                        <div style="text-align:center;" onclick="GymV3.showTechnique('${ex.name}')">
                            <i class="fa-solid fa-circle-info" style="font-size:20px; color:rgba(255,255,255,0.5); margin-bottom:8px;"></i>
                            <div style="font-size:14px; font-weight:600; color:#fff; margin-top:5px; line-height:24px;">Инфо</div>
                            <div style="font-size:11px; color:rgba(255,255,255,0.4); text-transform:uppercase;">Техника</div>
                        </div>
                    </div>

                    <!-- Main Action -->
                    <button onclick="GymV3.completeSetAndRest()" style="
                        width:100%;
                        background: linear-gradient(135deg, #007AFF 0%, #0056b3 100%);
                        box-shadow: 0 10px 30px rgba(0,122,255,0.3);
                        border:none; color:#fff;
                        padding:22px; border-radius:24px;
                        font-size:18px; font-weight:700;
                        cursor:pointer; position:relative; overflow:hidden;
                        display:flex; align-items:center; justify-content:center; gap:12px;
                        margin-bottom:20px;
                    ">
                        <i class="fa-solid fa-check"></i> ЗАВЕРШИТЬ ПОДХОД
                    </button>

                    <button onclick="GymV3.skipExercise()" style="
                        background:transparent; border:none;
                        color:rgba(255,255,255,0.3); font-size:14px;
                        padding:10px; align-self:center; cursor:pointer;
                    ">Пропустить упражнение</button>
                </div>
            `;
        }
    },

    // Specific Russian cues for exercises
    techniqueTips: {
        "squat": "• Спина прямая, взгляд вперед\n• Вес на пятках\n• Колени смотрят в стороны носков\n• Глубокий вдох перед опусканием",
        "bench_press": "• Лопатки сведены вместе\n• Ноги жестко упираются в пол\n• Локти под углом 45-75° к телу\n• Опускаем на низ груди",
        "deadlift": "• Спина идеально прямая\n• Гриф скользит по ногам\n• Движение начинается с ног\n• Шея - продолжение позвоночника",
        "pushups": "• Тело образует прямую линию\n• Пресс и ягодицы напряжены\n• Локти не расставлять широко\n• Касаемся грудью пола",
        "plank": "• Таз не провисает и не торчит\n• Локти строго под плечами\n• Максимальное напряжение пресса\n• Дыхание ровное",
        "jump_rope": "• Прыжки только на носках\n• Колени чуть согнуты\n• Работают только кисти рук\n• Локти прижаты к корпусу",
        "pullups": "• Хват чуть шире плеч\n• Тянемся грудью к перекладине\n• Без рывков ногами\n• Полное разгибание внизу",
        "lunges": "• Шаг широкий\n• Колено задней ноги почти касается пола\n• Корпус держим вертикально\n• Угол в коленях 90°",
        "overhead_press": "• Пресс и ягодицы зажаты\n• Локти выведены чуть вперед\n• Штанга движется строго вертикально\n• В верхней точке голова уходит вперед",
        "dips": "• Корпус чуть наклонен вперед\n• Локти не разводим широко\n• Опускаемся до угла 90°",
        "crunches": "• Поясница прижата к полу\n• Не тянем себя за шею руками\n• Выдох на подъеме",
        "default": "Следите за техникой выполнения. Спина прямая, дыхание ровное. Концентрируйтесь на целевой мышце."
    },

    // Show technique modal
    showTechnique(exerciseName) {
        const slug = this.normalizeExerciseName(exerciseName);
        const tips = this.techniqueTips[slug] || this.techniqueTips["default"];
        const formattedTips = tips.replace(/\n/g, '<br/>');

        // Create modal
        const modal = document.createElement('div');
        modal.id = 'technique-modal';
        modal.style.cssText = `
            position:fixed; 
            top: 20px; left: 20px; right: 20px; bottom: 20px;
            background:rgba(20,20,22,0.98); 
            border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.1);
            z-index:10001;
            display:flex; flex-direction:column; align-items:center; justify-content:center;
            padding:30px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.8);
            backdrop-filter: blur(20px);
        `;
        modal.innerHTML = `
            <button onclick="document.getElementById('technique-modal').remove()" style="
                position:absolute; top:20px; right:20px;
                background:rgba(255,255,255,0.1); border:none; color:#fff;
                width:44px; height:44px; border-radius:50%; font-size:20px; cursor:pointer;
            "><i class="fa-solid fa-xmark"></i></button>
            
            <div style="font-size:13px; color:#666; text-transform:uppercase; letter-spacing:2px; margin-bottom:15px;">
                Техника упражнения
            </div>
            <div style="font-size:22px; font-weight:700; color:#fff; margin-bottom:30px; text-align:center;">
                ${exerciseName}
            </div>
            
            <div style="
                width:300px; height:300px;
                background:white;
                border-radius:24px;
                overflow:hidden;
                margin-bottom:30px;
                display:flex; align-items:center; justify-content:center;
            ">
                <img src="assets/exercises/${slug}.png" 
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block'"
                     style="width:100%; height:100%; object-fit:contain; padding:10px;" />
                     
                <div style="text-align:center; display:none; color:#333;">
                    <i class="fa-solid fa-image" style="font-size:50px; opacity:0.3; margin-bottom:15px;"></i>
                    <div style="font-size:14px;">Схема скоро появится</div>
                </div>
            </div>
            
            <div style="
                max-width:320px; 
                text-align:left; 
                color:#ccc; 
                font-size:15px; 
                line-height:1.6;
                background:rgba(255,255,255,0.05);
                padding:15px 20px;
                border-radius:16px;
                border:1px solid rgba(255,255,255,0.1);
            ">
                ${formattedTips}
            </div>
        `;
        document.body.appendChild(modal);
    },

    // Complete set → auto start rest with progressive timing
    completeSetAndRest() {
        if (window.Telegram?.WebApp?.HapticFeedback) {
            Telegram.WebApp.HapticFeedback.impactOccurred('medium');
        }

        // Progressive rest: 30s first, then +10s each set
        const restTime = 30 + (this.currentSet - 1) * 10;

        // Check if last set
        if (this.currentSet >= this.totalSets) {
            // Move to next exercise after rest
            this.startRest(restTime, true); // true = next exercise after rest
        } else {
            // Just next set
            this.currentSet++;
            this.startRest(restTime, false);
        }
    },

    // Skip exercise
    skipExercise() {
        this.currentExerciseIndex++;
        this.currentSet = 1;

        // Update totalSets for new exercise
        const day = this.currentProgram.months[0].days[this.currentDayIndex];
        if (this.currentExerciseIndex < day.exercises.length) {
            this.totalSets = this.parseSetsCount(day.exercises[this.currentExerciseIndex].sets);
        }

        this.renderCurrentExercise();
    },

    // Start timed exercise
    startExerciseTimer(seconds) {
        let remaining = seconds;
        const display = document.getElementById('exercise-timer');
        const btn = document.getElementById('start-timer-btn');

        if (btn) btn.style.display = 'none';

        if (this.exerciseTimer) clearInterval(this.exerciseTimer);

        this.exerciseTimerTarget = Date.now() + seconds * 1000;

        this.exerciseTimer = setInterval(() => {
            const now = Date.now();
            const remaining = Math.ceil((this.exerciseTimerTarget - now) / 1000);

            if (display) display.innerText = this.formatTime(Math.max(0, remaining));

            // Heartbeat & Pulsation (Last 20s)
            if (remaining <= 20 && remaining > 0) {
                if (display && !display.classList.contains('timer-heartbeat')) {
                    display.classList.add('timer-heartbeat');
                }
                this.playHeartbeat();
            }

            // Countdown Beeps (Last 5s)
            // Ensure we don't beep multiple times for the same second by checking integer change
            // Simplified for this context: just play if close to integer bound
            if (remaining <= 5 && remaining > 0) {
                // Trigger once per second logic would be better, but simple call is okay for now if sound is short
                // To prevent spam, we could track 'lastBeepSecond'
                if (this.lastBeepSecond !== remaining) {
                    this.playCountdownBeep();
                    this.lastBeepSecond = remaining;
                }
            }

            if (remaining <= 0) {
                clearInterval(this.exerciseTimer);
                if (display) display.classList.remove('timer-heartbeat');

                this.playFinishSound();

                if (window.Telegram?.WebApp?.HapticFeedback) {
                    Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                }

                // Move to next exercise
                this.currentExerciseIndex++;
                this.currentSet = 1;

                setTimeout(() => this.renderCurrentExercise(), 1000); // 1s delay to hear the finish sound
            }
        }, 200); // Check more frequently for smoothness
    },

    // Rest timer
    startRest(seconds, goToNextExercise = false) {
        this.restSeconds = seconds;
        this.goToNextAfterRest = goToNextExercise;

        const overlay = document.getElementById('rest-overlay');
        overlay.style.display = 'flex';

        // Random motivation
        const msg = this.motivationalMessages[Math.floor(Math.random() * this.motivationalMessages.length)];
        document.getElementById('rest-motivation').innerText = msg.icon;
        document.getElementById('rest-motivation-text').innerText = msg.text;

        if (this.restTimer) clearInterval(this.restTimer);

        const display = document.getElementById('rest-timer-display');
        display.innerText = this.restSeconds;

        this.restTimerTarget = Date.now() + seconds * 1000;

        this.restTimer = setInterval(() => {
            const now = Date.now();
            this.restSeconds = Math.ceil((this.restTimerTarget - now) / 1000);

            display.innerText = Math.max(0, this.restSeconds);

            // Countdown for rest as well (Last 3s)
            if (this.restSeconds <= 3 && this.restSeconds > 0) {
                if (this.lastRestBeep !== this.restSeconds) {
                    this.playCountdownBeep();
                    this.lastRestBeep = this.restSeconds;
                }
            }

            // Change motivation every 15s (approx)
            if (this.restSeconds > 0 && this.restSeconds % 15 === 0) {
                // Optimization: only update once per second
                // skipping detailed check for brevity
                const newMsg = this.motivationalMessages[Math.floor(Math.random() * this.motivationalMessages.length)];
                document.getElementById('rest-motivation').innerText = newMsg.icon;
                document.getElementById('rest-motivation-text').innerText = newMsg.text;
            }

            if (this.restSeconds <= 0) {
                clearInterval(this.restTimer);
                this.playFinishSound(); // Enhanced finish sound
                display.innerText = "GO!";

                if (window.Telegram?.WebApp?.HapticFeedback) {
                    Telegram.WebApp.HapticFeedback.notificationOccurred('warning');
                }

                setTimeout(() => this.closeRest(), 800);
            }
        }, 200);
    },

    addRestTime(sec) {
        this.restTimerTarget += sec * 1000;
        // visual update happens in next tick
    },

    skipRest() {
        clearInterval(this.restTimer);
        this.closeRest();
    },

    closeRest() {
        document.getElementById('rest-overlay').style.display = 'none';

        // If was last set, move to next exercise
        if (this.goToNextAfterRest) {
            this.currentExerciseIndex++;
            this.currentSet = 1;

            // Update totalSets for new exercise
            const day = this.currentProgram.months[0].days[this.currentDayIndex];
            if (this.currentExerciseIndex < day.exercises.length) {
                this.totalSets = this.parseSetsCount(day.exercises[this.currentExerciseIndex].sets);
            }
        }

        this.renderCurrentExercise();
    },

    // Finish workout
    finishWorkout() {
        if (this.mainTimer) clearInterval(this.mainTimer);
        if (this.exerciseTimer) clearInterval(this.exerciseTimer);
        if (this.restTimer) clearInterval(this.restTimer);

        this.workoutActive = false;

        // Calculate time
        const elapsedSeconds = Math.floor((Date.now() - this.workoutStartTime) / 1000);
        const minutes = Math.floor(elapsedSeconds / 60);

        // Hide overlay
        document.getElementById('workout-overlay').style.display = 'none';

        // 15 Minute Validation
        if (minutes < 15) {
            alert(`⚠️ Тренировка слишком короткая (${minutes} мин).\nМинимальное время: 15 минут.\nXP не начислены.`);
            this.switchView('gym-programs');
            this.renderMyPrograms();
            return;
        }

        // Add XP
        const xpGained = 50 + Math.floor(minutes * 2);
        DB.data.xp = (DB.data.xp || 0) + xpGained;
        DB.save();

        // Show completion
        const confirmMsg = `🎉 Тренировка завершена!\n⏱ Время: ${minutes} мин\n⭐ +${xpGained} XP`;
        alert(confirmMsg);

        this.switchView('gym-programs');
        this.renderMyPrograms();
    },

    // Helpers
    normalizeExerciseName(name) {
        // Safe mapping for Russian exercise names to English filenames
        const map = {
            // Basic Matches
            "Приседания со штангой": "squat",
            "Приседания": "squat",
            "Жим лежа": "bench_press",
            "Жим штанги лежа": "bench_press",
            "Становая тяга": "deadlift",
            "Отжимания": "pushups",
            "Планка": "plank",
            "Скакалка": "jump_rope",
            "Скакалка (быстро)": "jump_rope",

            // Batch 2 (Coming soon)
            "Подтягивания": "pullups",
            "Подтягивания узкие": "pullups",
            "Выпады": "lunges",
            "Выпады (ходьба)": "lunges",
            "Болгарский сплит": "lunges", // Re-use for now
            "Армейский жим": "overhead_press",
            "Брусья": "dips",
            "Брусья с весом": "dips",
            "Скручивания": "crunches",
            "Пресс": "crunches",
            "Жим гантелей на наклонной": "db_incline_press",
            "Бицепс штанга": "barbell_curl",
            "Молотки": "dumbbell_curl",
            "Тяга блока к поясу": "seated_row",
            "Тяга верхнего блока": "lat_pulldown",
            "Верхний блок": "lat_pulldown",

            // Placeholders for others to prevent empty string errors
            // If not found, we return a safe default or hashed string
        };

        // Exact match
        if (map[name]) return map[name];

        // fuzzy match logic could go here

        // Fallback: simple hash or safe slug that ALLOWS cyrillic if needed, 
        // but since we rely on local files, let's map unknown to 'placeholder' for now 
        // or return a transliterated slug if we had a library.
        // For now:
        return "placeholder";
    },

    // --- DEMO MODE ENGINE ---
    startDemoMode() {
        if (this.demoActive) return;
        this.demoActive = true;
        console.log("🎬 Starting Demo Mode...");

        // Mock alerts and confirms
        this._originalAlert = window.alert;
        this._originalConfirm = window.confirm;
        window.alert = (msg) => {
            console.log("[Demo Alert]:", msg);
            const toast = document.createElement('div');
            toast.innerText = msg;
            toast.style.cssText = `
                position:fixed; top:20%; left:50%; transform:translate(-50%, -50%);
                background:rgba(255,255,255,0.95); color:#000; padding:15px 25px;
                border-radius:20px; box-shadow:0 10px 40px rgba(0,0,0,0.5);
                z-index:20000; font-weight:800; text-align:center; min-width:200px;
                font-size: 16px;
                animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            `;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.5s';
                setTimeout(() => toast.remove(), 500);
            }, 3000);
        };
        window.confirm = () => true;

        // Visual Badge
        const badge = document.createElement('div');
        badge.id = 'demo-badge';
        badge.innerHTML = '<i class="fa-solid fa-robot"></i> AUTO-DEMO';
        badge.style.cssText = `
            position:fixed; top:70px; right:10px;
            background:#FF375F; color:white; padding:6px 12px; border-radius:30px;
            font-size:10px; font-weight:800; z-index:20000; 
            box-shadow:0 0 15px rgba(255, 55, 95, 0.5); text-transform:uppercase; letter-spacing:1px;
        `;
        document.body.appendChild(badge);

        this.runDemoSteps();
    },

    stopDemoMode() {
        this.demoActive = false;
        if (this._originalAlert) window.alert = this._originalAlert;
        if (this._originalConfirm) window.confirm = this._originalConfirm;
        document.getElementById('demo-badge')?.remove();
        console.log("🏁 Demo Mode Stopped");
    },

    async runDemoSteps() {
        const wait = (ms) => new Promise(r => setTimeout(r, ms));

        try {
            console.log("🚀 Starting Full App Demo (35s)");

            // 0. RESET VIEW
            window.scrollTo({ top: 0, behavior: 'instant' });

            // 1. FAKE ONBOARDING (Simulated)
            const onboardingOverlay = document.createElement('div');
            onboardingOverlay.style.cssText = `
                position:fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:10000;
                display:flex; flex-direction:column; align-items:center; justify-content:center;
                animation: fadeIn 0.5s;
            `;
            onboardingOverlay.innerHTML = `
                <div style="font-size:30px; font-weight:800; margin-bottom:20px;">MVP <span style="color:#007AFF">LIFE OS</span></div>
                <div style="color:#888; margin-bottom:40px;">Initializing System...</div>
                <div style="width:200px; height:4px; background:#333; border-radius:2px;">
                    <div id="demo-loader" style="width:0%; height:100%; background:#007AFF; transition: width 2s linear;"></div>
                </div>
            `;
            document.body.appendChild(onboardingOverlay);

            await wait(100);
            document.getElementById('demo-loader').style.width = '100%';
            await wait(2000); // Show logo screen

            onboardingOverlay.style.opacity = '0';
            onboardingOverlay.style.transition = 'opacity 0.5s';
            setTimeout(() => onboardingOverlay.remove(), 500);
            await wait(500);

            // 2. PROFILE & STATS (5s)
            // Use global UI or fallback logic to switch tab
            if (window.UI) window.UI.switchTab('profile');
            else document.querySelector('[onclick*="switchTab(\'profile\')"]')?.click();

            await wait(1000);
            window.scrollTo({ top: 200, behavior: 'smooth' }); // Scroll to Logic/Stats
            await wait(1500);
            // Highlight Level
            const xpBar = document.getElementById('xp-fill');
            if (xpBar) {
                xpBar.style.width = '0%';
                setTimeout(() => xpBar.style.width = '75%', 100);
            }
            await wait(1500);

            // 3. FOOD / CALORIES (5s)
            if (window.UI) window.UI.switchTab('food');
            else document.querySelector('[onclick*="switchTab(\'food\')"]')?.click();

            await wait(800);

            // Simulate changing calories
            const calVal = document.getElementById('cal-val');
            if (calVal) {
                let start = 0;
                const end = 1850;
                const dur = 1000;
                const startTime = performance.now();
                const animateCal = (t) => {
                    const progress = Math.min((t - startTime) / dur, 1);
                    calVal.innerText = Math.floor(progress * end);
                    if (progress < 1) requestAnimationFrame(animateCal);
                };
                requestAnimationFrame(animateCal);

                const calProg = document.getElementById('cal-progress');
                if (calProg) calProg.style.width = '70%';
            }
            await wait(2500);

            // 4. WORKOUTS (Rest of time ~15-20s)
            if (window.UI) window.UI.switchTab('gym');
            else document.querySelector('[onclick*="switchTab(\'gym\')"]')?.click();

            // Force Gym View
            this.switchView('gym-programs');
            this.renderMyPrograms();

            await wait(1000);
            window.scrollTo({ top: 0, behavior: 'smooth' });

            // Open Program (first available)
            const programCard = document.querySelector('.gym-card');
            if (programCard) {
                programCard.style.transform = "scale(0.95)";
                setTimeout(() => programCard.style.transform = "scale(1)", 150);
                await wait(200);
                programCard.click();
            }
            await wait(1500);

            // Select Day (first day)
            const dayCard = document.querySelector('.day-card'); // "day-card" class from gym-v3 render
            if (dayCard) {
                dayCard.click();
            }
            await wait(1500);

            // Show Technique (The "Wow" factor)
            // find first exercise name in the now-visible list
            const exTitle = document.querySelector('.exercise-item h4')?.innerText || 'squat';
            this.showTechnique(exTitle);

            await wait(4000);
            document.getElementById('technique-modal')?.remove();

            // Heartbeat
            await wait(500);
            this.playHeartbeat();

            // Finish
            await wait(1000);
            const activeView = document.getElementById('gym-active-view');
            // If we are in active view (only if day click triggered active view)
            // But currently design might keep it in list. Let's assume list view for day.

            // End
            const finishToast = document.createElement('div');
            finishToast.innerText = "✨ DEMO COMPLETED";
            finishToast.style.cssText = `
                position:fixed; top:50%; left:50%; transform:translate(-50%,-50%);
                background:#fff; color:#000; padding:20px 40px; font-weight:800;
                font-size:20px; border-radius:20px; z-index:20000;
                box-shadow:0 0 50px rgba(255,255,255,0.5);
                animation: popIn 0.5s;
            `;
            document.body.appendChild(finishToast);
            await wait(2000);
            finishToast.remove();

            this.stopDemoMode();

        } catch (e) {
            console.error("Demo Error:", e);
            this.stopDemoMode();
        }
    },


    isTimedExercise(setsStr) {
        return setsStr.includes('мин') || setsStr.match(/\d+\s*с($|\s)/) || setsStr.includes('сек');
    },

    parseTimeToSeconds(str) {
        const minMatch = str.match(/(\d+)\s*мин/);
        if (minMatch) return parseInt(minMatch[1]) * 60;

        const secMatch = str.match(/(\d+)\s*с/);
        if (secMatch) return parseInt(secMatch[1]);

        return 60;
    },

    formatTime(sec) {
        const m = Math.floor(sec / 60).toString().padStart(2, '0');
        const s = (sec % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    },

    // Sound Effects Engine
    audioCtx: null,

    initAudio() {
        if (!this.audioCtx) {
            this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
    },

    playCountdownBeep() {
        this.initAudio();
        const t = this.audioCtx.currentTime;
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();

        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        // Short, crisp click (Woodblock style)
        osc.frequency.setValueAtTime(800, t);
        gain.gain.setValueAtTime(0.3, t);
        gain.gain.exponentialRampToValueAtTime(0.01, t + 0.05); // Very short transition

        osc.start(t);
        osc.stop(t + 0.05);
    },

    playHeartbeat() {
        // Subtle low thud, not annoying
        this.initAudio();
        const t = this.audioCtx.currentTime;

        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        osc.frequency.setValueAtTime(80, t);
        osc.frequency.exponentialRampToValueAtTime(40, t + 0.1); // Drop pitch

        gain.gain.setValueAtTime(0.4, t);
        gain.gain.exponentialRampToValueAtTime(0.01, t + 0.15);

        osc.start(t);
        osc.stop(t + 0.15);
    },

    playFinishSound() {
        this.initAudio();
        const t = this.audioCtx.currentTime;

        // Pleasant chord
        [523.25, 659.25, 783.99].forEach((freq, i) => { // C Major
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            osc.connect(gain);
            gain.connect(this.audioCtx.destination);

            osc.frequency.value = freq;
            osc.type = 'sine';

            gain.gain.setValueAtTime(0.1, t);
            gain.gain.exponentialRampToValueAtTime(0.01, t + 1.2);

            osc.start(t + i * 0.05); // slight strum
            osc.stop(t + 1.2);
        });
    },

    playSound() { this.playFinishSound(); }, // Legacy fallback

    switchView(id) {
        ['gym-programs', 'gym-days-view', 'gym-active-view'].forEach(v => {
            const el = document.getElementById(v);
            if (el) el.style.display = 'none';
        });
        const target = document.getElementById(id);
        if (target) target.style.display = 'block';
    }
};

window.Gym = GymV3;
window.GymV2 = GymV3;
