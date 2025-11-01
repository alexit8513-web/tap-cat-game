// Игровые переменные
let score = 0;
let money = 100;
let level = 1;
let clickPower = 1;

// Основная функция тапа
function tapCat() {
    // Добавляем очки и деньги
    score += clickPower;
    money += clickPower;
    
    // Обновляем интерфейс
    updateUI();
    
    // Создаем эффект частиц
    createParticle(`+${clickPower}`, '#ffd700');
    
    // Анимация кота
    animateCat();
    
    // Проверяем уровень
    checkLevelUp();
}

// Обновление интерфейса
function updateUI() {
    document.getElementById('score').textContent = score;
    document.getElementById('money').textContent = money;
    document.getElementById('level').textContent = level;
    document.getElementById('power').textContent = clickPower;
}

// Создание эффекта частиц
function createParticle(text, color) {
    const effects = document.getElementById('effects');
    const particle = document.createElement('div');
    
    particle.className = 'particle';
    particle.textContent = text;
    particle.style.color = color;
    particle.style.left = Math.random() * window.innerWidth + 'px';
    particle.style.top = '50%';
    
    effects.appendChild(particle);
    
    // Удаляем частицу после анимации
    setTimeout(() => {
        particle.remove();
    }, 1000);
}

// Анимация кота
function animateCat() {
    const cat = document.getElementById('cat');
    cat.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        cat.style.transform = 'scale(1)';
    }, 100);
}

// Проверка повышения уровня
function checkLevelUp() {
    const nextLevelScore = level * 100;
    if (score >= nextLevelScore) {
        level++;
        showLevelUp();
    }
}

// Показ анимации уровня
function showLevelUp() {
    const levelUp = document.createElement('div');
    levelUp.style.position = 'fixed';
    levelUp.style.top = '50%';
    levelUp.style.left = '50%';
    levelUp.style.transform = 'translate(-50%, -50%)';
    levelUp.style.fontSize = '48px';
    levelUp.style.fontWeight = 'bold';
    levelUp.style.color = '#ffd700';
    levelUp.style.zIndex = '1000';
    levelUp.textContent = `Уровень ${level}! 🎉`;
    
    document.body.appendChild(levelUp);
    
    setTimeout(() => {
        levelUp.remove();
    }, 2000);
}

// Инициализация игры
document.addEventListener('DOMContentLoaded', () => {
    // Вешаем обработчик на кота
    document.getElementById('cat').addEventListener('click', tapCat);
    
    console.log('🐱 Игра Tap Cat загружена!');
}); 
