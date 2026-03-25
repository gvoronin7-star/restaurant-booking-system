"""
Скрипт запуска тестов.
"""

import subprocess
import sys
import os


def run_tests(args=None):
    """Запуск тестов."""
    cmd = [sys.executable, "-m", "pytest"]
    
    if args:
        cmd.extend(args)
    else:
        # Стандартный запуск
        cmd.extend([
            "-v",           # Подробный вывод
            "--tb=short",   # Краткий traceback
        ])
    
    # Добавляем путь к проекту
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"Запуск: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd)
    return result.returncode


def run_unit_tests():
    """Запуск только юнит-тестов."""
    return run_tests(["-m", "unit"])


def run_integration_tests():
    """Запуск только интеграционных тестов."""
    return run_tests(["-m", "integration"])


def run_with_coverage():
    """Запуск тестов с покрытием."""
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term",
        "-v"
    ]
    return subprocess.run(cmd).returncode


def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unit":
            print("Запуск юнит-тестов...")
            return run_unit_tests()
        elif command == "integration":
            print("Запуск интеграционных тестов...")
            return run_integration_tests()
        elif command == "coverage":
            print("Запуск тестов с покрытием...")
            return run_with_coverage()
        elif command == "help":
            print("""
Использование: python run_tests.py [команда]

Команды:
  (без аргументов)  Запуск всех тестов
  unit              Только юнит-тесты
  integration       Только интеграционные тесты
  coverage          Тесты с покрытием кода
  help              Показать эту справку

Примеры:
  python run_tests.py
  python run_tests.py unit
  python run_tests.py integration
  python run_tests.py coverage
""")
            return 0
        else:
            print(f"Неизвестная команда: {command}")
            return 1
    
    # Стандартный запуск
    return run_tests()


if __name__ == "__main__":
    sys.exit(main())
