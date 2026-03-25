#!/bin/bash

# Скрипт для подготовки проекта к публикации на GitHub

echo "=========================================="
echo "Подготовка проекта к публикации на GitHub"
echo "=========================================="

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo "Ошибка: git не установлен"
    exit 1
fi

# Инициализация репозитория, если не существует
if [ ! -d .git ]; then
    echo "Инициализация git репозитория..."
    git init
    echo "Репозиторий инициализирован"
else
    echo "Репозиторий уже инициализирован"
fi

# Проверка .gitignore
if [ ! -f .gitignore ]; then
    echo "Создание .gitignore..."
    # Базовый .gitignore для Python
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp

# Environment
.env

# Logs
*.log
EOF
fi

# Добавление файлов
echo "Добавление файлов в индекс..."
git add .

# Проверка статуса
echo ""
echo "Файлы в индексе:"
git status --short

echo ""
echo "=========================================="
echo "Готово! Далее выполните:"
echo ""
echo "1. Создайте репозиторий на GitHub"
echo "2. Свяжите локальный и удалённый репозиторий:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/restaurant-booking-system.git"
echo "3. Сделайте первый коммит:"
echo "   git commit -m 'Initial commit'"
echo "4. Отправьте на GitHub:"
echo "   git push -u origin main"
echo "=========================================="
