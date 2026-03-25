"""
GUI интерфейс для системы бронирования ресторана.
"""

import sys

# Настройка UTF-8 для Windows
if sys.platform == "win32":
    import io
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from backend import RestaurantBackend


class RestaurantGUI:
    """Графический интерфейс системы бронирования."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Система бронирования ресторана")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Подключение к БД
        self.backend = RestaurantBackend()
        if not self.backend.connect():
            messagebox.showerror("Ошибка", "Не удалось подключиться к базе данных")
            return
        
        # Инициализация БД - только если таблицы не существуют
        try:
            with self.backend.db._get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM information_schema.tables 
                    WHERE table_name IN ('clients', 'tables', 'bookings')
                """)
                result = cursor.fetchone()
                if result['cnt'] < 3:
                    # Таблицы не существуют - создаем
                    self.backend.initialize_database()
                    self.backend.seed_demo_data()
        except Exception as e:
            print(f"Проверка таблиц: {e}")
        
        # Настройка стиля
        self.setup_style()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка данных
        self.refresh_all()
        
        # Обработка закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_style(self):
        """Настройка стиля."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка цветов
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10), padding=5)
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), background='#f0f0f0')
        style.configure('Treeview', font=('Arial', 9), rowheight=25)
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
        
        # Цвета для статусов
        self.status_colors = {
            'available': '#90EE90',
            'occupied': '#FFB6C1',
            'reserved': '#FFE4B5',
            'maintenance': '#D3D3D3',
            'pending': '#FFE4B5',
            'confirmed': '#90EE90',
            'cancelled': '#FFB6C1',
            'completed': '#87CEEB',
            'no_show': '#D3D3D3'
        }
    
    def create_widgets(self):
        """Создание виджетов."""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель - кнопки действий
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопки основных действий
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Расписание на сегодня", command=self.show_today_schedule).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➕ Новое бронирование", command=self.quick_booking_dialog).pack(side=tk.LEFT, padx=2)
        
        # Кнопки управления данными
        data_btn_frame = ttk.Frame(top_frame)
        data_btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(data_btn_frame, text="👥 Клиенты", command=self.show_clients).pack(side=tk.LEFT, padx=2)
        ttk.Button(data_btn_frame, text="🪑 Столики", command=self.show_tables).pack(side=tk.LEFT, padx=2)
        ttk.Button(data_btn_frame, text="📊 Статистика", command=self.show_statistics).pack(side=tk.LEFT, padx=2)
        
        # Ноутбук (вкладки)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка "Расписание"
        self.schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.schedule_frame, text="📅 Расписание")
        self.create_schedule_tab()
        
        # Вкладка "Доступность"
        self.availability_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.availability_frame, text="📊 Доступность")
        self.create_availability_tab()
        
        # Вкладка "Бронирования"
        self.bookings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bookings_frame, text="📋 Бронирования")
        self.create_bookings_tab()
        
        # Вкладка "Клиенты"
        self.clients_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.clients_tab_frame, text="👥 Клиенты")
        self.create_clients_tab()
        
        # Вкладка "Столики"
        self.tables_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tables_tab_frame, text="🪑 Столики")
        self.create_tables_tab()
        
        # Статус бар
        self.status_bar = ttk.Label(main_frame, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def create_schedule_tab(self):
        """Вкладка расписания."""
        # Выбор даты
        date_frame = ttk.Frame(self.schedule_frame, padding=10)
        date_frame.pack(fill=tk.X)
        
        ttk.Label(date_frame, text="Дата:").pack(side=tk.LEFT, padx=5)
        
        self.schedule_date = ttk.Entry(date_frame, width=15)
        self.schedule_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.schedule_date.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(date_frame, text="Показать", command=self.refresh_schedule).pack(side=tk.LEFT, padx=5)
        
        # Таблица расписания
        columns = ('Время', 'Столик', 'Клиент', 'Гости', 'Статус', 'Телефон')
        self.schedule_tree = ttk.Treeview(self.schedule_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.schedule_tree.heading(col, text=col)
            self.schedule_tree.column(col, width=120)
        
        self.schedule_tree.column('Клиент', width=150)
        self.schedule_tree.column('Телефон', width=120)
        
        scrollbar = ttk.Scrollbar(self.schedule_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscroll=scrollbar.set)
        
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Контекстное меню для расписания
        self.schedule_menu = tk.Menu(self.schedule_tree, tearoff=0)
        self.schedule_menu.add_command(label="Подтвердить", command=self.confirm_booking_from_schedule)
        self.schedule_menu.add_command(label="Отменить", command=self.cancel_booking_from_schedule)
        self.schedule_menu.add_command(label="Завершить", command=self.complete_booking_from_schedule)
        self.schedule_tree.bind("<Button-3>", self.show_schedule_menu)
    
    def create_availability_tab(self):
        """Вкладка доступности."""
        # Выбор даты
        date_frame = ttk.Frame(self.availability_frame, padding=10)
        date_frame.pack(fill=tk.X)
        
        ttk.Label(date_frame, text="Дата:").pack(side=tk.LEFT, padx=5)
        
        self.availability_date = ttk.Entry(date_frame, width=15)
        self.availability_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.availability_date.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(date_frame, text="Показать", command=self.refresh_availability).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="Показать матрицу", command=self.show_availability_matrix).pack(side=tk.LEFT, padx=5)
        
        # Список доступных столиков
        avail_frame = ttk.LabelFrame(self.availability_frame, text="Доступные столики", padding=10)
        avail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Номер', 'Вместимость', 'Локация')
        self.availability_tree = ttk.Treeview(avail_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.availability_tree.heading(col, text=col)
            self.availability_tree.column(col, width=150)
        
        self.availability_tree.pack(fill=tk.BOTH, expand=True)
        
        # Выбор времени
        time_frame = ttk.Frame(self.availability_frame, padding=10)
        time_frame.pack(fill=tk.X)
        
        ttk.Label(time_frame, text="Время:").pack(side=tk.LEFT, padx=5)
        self.availability_time = ttk.Combobox(time_frame, width=10, values=[f"{h:02d}:00" for h in range(10, 23)])
        self.availability_time.set(datetime.now().strftime("%H:00"))
        self.availability_time.pack(side=tk.LEFT, padx=5)
        self.availability_time.bind("<<ComboboxSelected>>", lambda e: self.refresh_availability())
    
    def create_bookings_tab(self):
        """Вкладка бронирований."""
        # Фильтр по статусу
        filter_frame = ttk.Frame(self.bookings_frame, padding=10)
        filter_frame.pack(fill=tk.X)
        
        ttk.Label(filter_frame, text="Статус:").pack(side=tk.LEFT, padx=5)
        self.booking_status_filter = ttk.Combobox(filter_frame, width=15, 
                                                   values=['Все', 'pending', 'confirmed', 'cancelled', 'completed', 'no_show'])
        self.booking_status_filter.set('Все')
        self.booking_status_filter.pack(side=tk.LEFT, padx=5)
        self.booking_status_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_bookings())
        
        ttk.Button(filter_frame, text="Показать", command=self.refresh_bookings).pack(side=tk.LEFT, padx=5)
        
        # Таблица бронирований
        columns = ('ID', 'Дата', 'Время', 'Столик', 'Клиент', 'Гости', 'Статус')
        self.bookings_tree = ttk.Treeview(self.bookings_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.bookings_tree.heading(col, text=col)
            self.bookings_tree.column(col, width=100)
        
        self.bookings_tree.column('Клиент', width=150)
        
        scrollbar = ttk.Scrollbar(self.bookings_frame, orient=tk.VERTICAL, command=self.bookings_tree.yview)
        self.bookings_tree.configure(yscroll=scrollbar.set)
        
        self.bookings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Кнопки действий
        action_frame = ttk.Frame(self.bookings_frame, padding=10)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Подтвердить", command=self.confirm_booking).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Отменить", command=self.cancel_booking).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Завершить", command=self.complete_booking).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Удалить", command=self.delete_booking).pack(side=tk.LEFT, padx=2)
    
    def create_clients_tab(self):
        """Вкладка клиентов."""
        # Поиск
        search_frame = ttk.Frame(self.clients_tab_frame, padding=10)
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.client_search = ttk.Entry(search_frame, width=30)
        self.client_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_clients).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Все", command=self.refresh_clients).pack(side=tk.LEFT, padx=2)
        
        # Таблица клиентов
        columns = ('ID', 'Имя', 'Email', 'Телефон', 'Дата регистрации')
        self.clients_tree = ttk.Treeview(self.clients_tab_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.clients_tree.heading(col, text=col)
            self.clients_tree.column(col, width=120)
        
        self.clients_tree.column('Имя', width=150)
        self.clients_tree.column('Email', width=180)
        
        scrollbar = ttk.Scrollbar(self.clients_tab_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscroll=scrollbar.set)
        
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Кнопки действий
        action_frame = ttk.Frame(self.clients_tab_frame, padding=10)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Добавить клиента", command=self.add_client_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Бронирования клиента", command=self.client_bookings).pack(side=tk.LEFT, padx=2)
    
    def create_tables_tab(self):
        """Вкладка столиков."""
        # Фильтр
        filter_frame = ttk.Frame(self.tables_tab_frame, padding=10)
        filter_frame.pack(fill=tk.X)
        
        ttk.Label(filter_frame, text="Локация:").pack(side=tk.LEFT, padx=5)
        self.table_location_filter = ttk.Combobox(filter_frame, width=15,
                                                   values=['Все', 'main_hall', 'terrace', 'vip_room', 'bar'])
        self.table_location_filter.set('Все')
        self.table_location_filter.pack(side=tk.LEFT, padx=5)
        self.table_location_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_tables())
        
        ttk.Button(filter_frame, text="Показать", command=self.refresh_tables).pack(side=tk.LEFT, padx=5)
        
        # Таблица столиков
        columns = ('ID', 'Номер', 'Вместимость', 'Локация', 'Статус')
        self.tables_tree = ttk.Treeview(self.tables_tab_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.tables_tree.heading(col, text=col)
            self.tables_tree.column(col, width=120)
        
        self.tables_tree.column('Номер', width=80)
        
        scrollbar = ttk.Scrollbar(self.tables_tab_frame, orient=tk.VERTICAL, command=self.tables_tree.yview)
        self.tables_tree.configure(yscroll=scrollbar.set)
        
        self.tables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Кнопки действий
        action_frame = ttk.Frame(self.tables_tab_frame, padding=10)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Добавить столик", command=self.add_table_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Изменить статус", command=self.change_table_status).pack(side=tk.LEFT, padx=2)
    
    # === Методы обновления данных ===
    
    def refresh_all(self):
        """Обновить все вкладки."""
        self.refresh_schedule()
        self.refresh_availability()
        self.refresh_bookings()
        self.refresh_clients()
        self.refresh_tables()
        self.set_status("Данные обновлены")
    
    def refresh_schedule(self):
        """Обновить расписание."""
        date = self.schedule_date.get().strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Очистка
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        try:
            schedule = self.backend.get_daily_schedule(date)
            for s in schedule:
                start = str(s['start_time'])[:5]
                end = str(s['end_time'])[:5]
                time_str = f"{start}-{end}"
                
                self.schedule_tree.insert('', tk.END, values=(
                    time_str,
                    s['table_number'],
                    s['client_name'],
                    s['guest_count'],
                    s['status'],
                    s['client_phone']
                ), tags=(str(s['id']),))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить расписание: {e}")
    
    def refresh_availability(self):
        """Обновить доступность."""
        date = self.availability_date.get().strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        time = self.availability_time.get().strip()
        if not time:
            time = datetime.now().strftime("%H:00")
        
        # Очистка
        for item in self.availability_tree.get_children():
            self.availability_tree.delete(item)
        
        try:
            available = self.backend.tables.get_available(date, time)
            for t in available:
                self.availability_tree.insert('', tk.END, values=(
                    t['table_number'],
                    t['capacity'],
                    t['location']
                ))
            
            self.set_status(f"Доступно столиков: {len(available)} на {date} в {time}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить доступность: {e}")
    
    def refresh_bookings(self):
        """Обновить бронирования."""
        status = self.booking_status_filter.get()
        if status == 'Все':
            status = None
        
        # Очистка
        for item in self.bookings_tree.get_children():
            self.bookings_tree.delete(item)
        
        try:
            bookings = self.backend.bookings.get_all(status)
            for b in bookings:
                start = str(b['start_time'])[:5]
                end = str(b['end_time'])[:5]
                
                self.bookings_tree.insert('', tk.END, values=(
                    b['id'],
                    b['booking_date'],
                    f"{start}-{end}",
                    b['table_number'],
                    b['client_name'],
                    b['guest_count'],
                    b['status']
                ), tags=(str(b['id']),))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить бронирования: {e}")
    
    def refresh_clients(self):
        """Обновить клиентов."""
        # Очистка
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        
        try:
            clients = self.backend.clients.get_all()
            for c in clients:
                created = str(c['created_at'])[:10] if c.get('created_at') else ''
                self.clients_tree.insert('', tk.END, values=(
                    c['id'],
                    c['name'],
                    c['email'],
                    c['phone'],
                    created
                ), tags=(str(c['id']),))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить клиентов: {e}")
    
    def refresh_tables(self):
        """Обновить столики."""
        location = self.table_location_filter.get()
        
        # Очистка
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)
        
        try:
            if location == 'Все':
                tables = self.backend.tables.get_all()
            else:
                tables = self.backend.tables.get_by_location(location)
            
            for t in tables:
                self.tables_tree.insert('', tk.END, values=(
                    t['id'],
                    t['table_number'],
                    t['capacity'],
                    t['location'],
                    t['status']
                ), tags=(str(t['id']), t['status']))
                
                # Раскраска по статусу
                if t['status'] in self.status_colors:
                    self.tables_tree.tag_configure(t['status'], background=self.status_colors[t['status']])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить столики: {e}")
    
    # === Диалоговые окна ===
    
    def quick_booking_dialog(self):
        """Диалог быстрого бронирования с выбором столика."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новое бронирование")
        dialog.geometry("550x650")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрируем
        dialog.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")
        
        # Загружаем всех клиентов для автодополнения
        all_clients = self.backend.clients.get_all()
        client_names = [c['name'] for c in all_clients]
        client_data = {c['name']: c for c in all_clients}
        
        # Загружаем все столики
        all_tables = self.backend.tables.get_all()
        table_options = ["Автоматически"] + [f"{t['table_number']} ({t['capacity']} мест, {t['location']})" for t in all_tables]
        table_data = {f"{t['table_number']} ({t['capacity']} мест, {t['location']})": t for t in all_tables}
        
        # Поля ввода
        fields = {}
        
        # Заголовок секции клиента
        ttk.Label(dialog, text="=== Клиент ===", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(10, 5), sticky=tk.W, padx=10
        )
        
        row = 1
        
        # Выбор клиента - сначала показываем всех
        ttk.Label(dialog, text="Выберите или введите имя:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Фрейм для комбобокса с кнопкой обновления
        client_frame = ttk.Frame(dialog)
        client_frame.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        
        name_var = tk.StringVar()
        # Используем Combobox с редактируемым списком
        name_combo = ttk.Combobox(client_frame, textvariable=name_var, width=35, 
                                   values=client_names, state='normal')
        name_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # Кнопка обновления списка
        def refresh_client_list():
            nonlocal client_names, client_data
            all_clients = self.backend.clients.get_all()
            client_names = [c['name'] for c in all_clients]
            client_data = {c['name']: c for c in all_clients}
            name_combo['values'] = client_names
        
        ttk.Button(client_frame, text="🔄", width=3, command=refresh_client_list).pack(side=tk.LEFT)
        
        # Подсказка
        ttk.Label(dialog, text="(начните вводить имя для поиска)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row+1, column=1, sticky=tk.W, padx=10
        )
        
        # Функция автодополнения при вводе
        def on_name_keyrelease(event):
            value = name_var.get()
            
            if not value:
                name_combo['values'] = client_names
            else:
                # Фильтр по частичному совпадению (без учета регистра)
                filtered = [name for name in client_names if value.lower() in name.lower()]
                name_combo['values'] = filtered
                # Показываем выпадающий список
                if filtered:
                    name_combo.event_generate('<Button-1>')
                    name_combo.icursor(len(value))
            
            # Проверяем частичное совпадение для автозаполнения
            for name in client_names:
                if value.lower() == name.lower():
                    # Точное совпадение - заполняем данные
                    client = client_data[name]
                    email_var.set(client['email'])
                    phone_var.set(client['phone'])
                    break
                elif value.lower() in name.lower() and value:
                    # Частичное совпадение - показываем подсказку
                    pass
        
        name_combo.bind('<KeyRelease>', on_name_keyrelease)
        name_combo.bind('<<ComboboxSelected>>', lambda e: on_name_keyrelease(None))
        
        fields['name'] = name_var
        row += 2
        
        # Email
        ttk.Label(dialog, text="Email:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        email_var = tk.StringVar()
        email_entry = ttk.Entry(dialog, textvariable=email_var, width=40)
        email_entry.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        fields['email'] = email_var
        row += 1
        
        # Телефон
        ttk.Label(dialog, text="Телефон:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        phone_var = tk.StringVar()
        phone_entry = ttk.Entry(dialog, textvariable=phone_var, width=40)
        phone_entry.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        fields['phone'] = phone_var
        row += 1
        
        # Секция бронирования
        ttk.Label(dialog, text="=== Бронирование ===", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, pady=(15, 5), sticky=tk.W, padx=10
        )
        row += 1
        
        # Количество гостей
        ttk.Label(dialog, text="Количество гостей:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        guests_var = tk.StringVar(value="2")
        guests_entry = ttk.Entry(dialog, textvariable=guests_var, width=40)
        guests_entry.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        fields['guests'] = guests_var
        row += 1
        
        # Дата
        ttk.Label(dialog, text="Дата (YYYY-MM-DD):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(dialog, textvariable=date_var, width=40)
        date_entry.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        fields['date'] = date_var
        row += 1
        
        # Время
        ttk.Label(dialog, text="Время начала (HH:MM):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        time_var = tk.StringVar(value="19:00")
        time_entry = ttk.Entry(dialog, textvariable=time_var, width=40)
        time_entry.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        fields['time'] = time_var
        row += 1
        
        # Длительность
        ttk.Label(dialog, text="Длительность (часы):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        duration_var = tk.StringVar(value="2")
        duration_entry = ttk.Entry(dialog, textvariable=duration_var, width=40)
        duration_entry.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        fields['duration'] = duration_var
        row += 1
        
        # Выбор столика
        ttk.Label(dialog, text="Столик:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        
        table_frame = ttk.Frame(dialog)
        table_frame.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        
        table_var = tk.StringVar(value="Автоматически")
        table_combo = ttk.Combobox(table_frame, textvariable=table_var, width=35, 
                                    values=table_options, state='readonly')
        table_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # Кнопка обновления списка столиков
        def refresh_table_list():
            nonlocal all_tables, table_options, table_data
            all_tables = self.backend.tables.get_all()
            table_options = ["Автоматически"] + [f"{t['table_number']} ({t['capacity']} мест, {t['location']})" for t in all_tables]
            table_data = {f"{t['table_number']} ({t['capacity']} мест, {t['location']})": t for t in all_tables}
            table_combo['values'] = table_options
        
        ttk.Button(table_frame, text="🔄", width=3, command=refresh_table_list).pack(side=tk.LEFT)
        
        # Подсказка
        ttk.Label(dialog, text="(выберите столик или оставьте 'Автоматически')", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row+1, column=1, sticky=tk.W, padx=10
        )
        
        fields['table'] = table_var
        row += 2
        
        def submit():
            try:
                guest_count = int(fields['guests'].get())
                date = fields['date'].get().strip()
                start_time = fields['time'].get().strip()
                duration = int(fields['duration'].get())
                
                # Вычисляем время окончания
                start_dt = datetime.strptime(start_time, "%H:%M")
                end_dt = start_dt + timedelta(hours=duration)
                end_time = end_dt.strftime("%H:%M")
                
                # Проверяем выбран ли столик вручную
                selected_table = table_var.get()
                table = None
                
                if selected_table != "Автоматически" and selected_table in table_data:
                    # Проверяем доступность выбранного столика
                    table = table_data[selected_table]
                    if table['capacity'] < guest_count:
                        messagebox.showerror("Ошибка", 
                            f"Столик {table['table_number']} вмещает только {table['capacity']} гостей", 
                            parent=dialog)
                        return
                    
                    # Проверяем доступность
                    if not self.backend.bookings.check_availability(table['id'], date, start_time, end_time):
                        messagebox.showerror("Ошибка", 
                            f"Сталик {table['table_number']} занят на указанное время", 
                            parent=dialog)
                        return
                else:
                    # Автоматический выбор столика
                    table = self.backend.find_table_for_group(guest_count, date, start_time, end_time)
                    if not table:
                        messagebox.showerror("Ошибка", "Нет доступных столиков на указанное время", parent=dialog)
                        return
                
                # Создаём или находим клиента
                client_name = fields['name'].get().strip()
                client_email = fields['email'].get().strip()
                client_phone = fields['phone'].get().strip()
                
                # Пробуем найти существующего клиента
                client = self.backend.clients.get_by_email(client_email)
                if not client:
                    client_id = self.backend.clients.create(client_name, client_email, client_phone)
                    client = self.backend.clients.get_by_id(client_id)
                else:
                    client_id = client['id']
                
                # Создаём бронирование
                booking_id = self.backend.bookings.create(
                    client_id=client_id,
                    table_id=table['id'],
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    guest_count=guest_count,
                    status="confirmed"
                )
                
                messagebox.showinfo("Успех", f"Бронирование #{booking_id} создано!\n"
                                            f"Сталик: {table['table_number']}", parent=dialog)
                dialog.destroy()
                self.refresh_all()
    
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=dialog)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать бронирование: {e}", parent=dialog)
        
        # Кнопка создания нового клиента
        def create_new_client():
            """Создать нового клиента из диалога бронирования."""
            try:
                name = name_var.get().strip()
                email = email_var.get().strip()
                phone = phone_var.get().strip()
                
                if not name or not email or not phone:
                    messagebox.showwarning("Внимание", "Заполните имя, email и телефон", parent=dialog)
                    return
                
                client_id = self.backend.clients.create(name, email, phone)
                messagebox.showinfo("Успех", f"Клиент #{client_id} создан", parent=dialog)
                
                # Обновляем списки
                refresh_client_list()
                
                self.refresh_clients()
                
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=dialog)
        
        # Кнопки
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Создать бронь", command=submit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Новый клиент", command=create_new_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def add_client_dialog(self):
        """Диалог добавления клиента - модальное окно."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить клиента")
        dialog.geometry("400x250")
        dialog.transient(self.root)  # Делаем окно зависимым от главного
        dialog.grab_set()  # Модальное - блокирует главное окно
        dialog.resizable(False, False)
        
        # Центрируем относительно главного окна
        dialog.geometry(f"+{self.root.winfo_x() + 100}+{self.root.winfo_y() + 100}")
        
        # Поля ввода
        ttk.Label(dialog, text="Имя:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Email:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        email_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=email_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Телефон:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        phone_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=phone_var, width=30).grid(row=2, column=1, padx=10, pady=10)
        
        def save_client():
            name = name_var.get().strip()
            email = email_var.get().strip()
            phone = phone_var.get().strip()
            
            if not name or not email or not phone:
                messagebox.showwarning("Внимание", "Заполните все поля", parent=dialog)
                return
            
            try:
                client_id = self.backend.clients.create(name, email, phone)
                messagebox.showinfo("Успех", f"Клиент #{client_id} создан", parent=dialog)
                dialog.destroy()
                self.refresh_clients()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=dialog)
        
        # Кнопки
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Сохранить", command=save_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Фокус на первое поле
        name_var.set("")
        email_var.set("")
        phone_var.set("")
    
    def add_table_dialog(self):
        """Диалог добавления столика."""
        number = simpledialog.askstring("Добавить столик", "Номер столика:")
        if not number:
            return
        
        capacity = simpledialog.askinteger("Добавить столик", "Вместимость (1-20):", minvalue=1, maxvalue=20)
        if not capacity:
            return
        
        location = simpledialog.askstring("Добавить столик", "Локация (main_hall/terrace/vip_room/bar):", 
                                          initialvalue="main_hall")
        if not location:
            return
        
        try:
            table_id = self.backend.tables.create(number, capacity, location)
            messagebox.showinfo("Успех", f"Столик #{table_id} создан")
            self.refresh_tables()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
    
    # === Действия ===
    
    def show_today_schedule(self):
        """Показать расписание на сегодня."""
        self.schedule_date.delete(0, tk.END)
        self.schedule_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.notebook.select(self.schedule_frame)
        self.refresh_schedule()
    
    def show_clients(self):
        """Показать вкладку клиентов."""
        self.notebook.select(self.clients_tab_frame)
    
    def show_tables(self):
        """Показать вкладку столиков."""
        self.notebook.select(self.tables_tab_frame)
    
    def show_statistics(self):
        """Показать статистику."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            summary = self.backend.bookings.get_daily_summary(today)
            start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            stats = self.backend.bookings.get_statistics(start, today)
            
            # Обработка None значений
            avg_guests = stats['avg_guests'] if stats['avg_guests'] else 0
            total_guests_today = summary['total_guests'] if summary['total_guests'] else 0
            
            msg = f"""СТАТИСТИКА

СЕГОДНЯ ({today}):
  Всего бронирований: {summary['total_bookings']}
  Подтверждено: {summary['confirmed']}
  Ожидают: {summary['pending']}
  Отменено: {summary['cancelled']}
  Всего гостей: {total_guests_today}

ЗА НЕДЕЛЮ ({start} - {today}):
  Всего бронирований: {stats['total_bookings']}
  Завершено: {stats['completed']}
  Отменено: {stats['cancelled']}
  Неявки: {stats['no_shows']}
  Среднее число гостей: {avg_guests:.1f}"""
            
            messagebox.showinfo("Статистика", msg)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить статистику: {e}")
    
    def search_clients(self):
        """Поиск клиентов."""
        query = self.client_search.get().strip()
        if not query:
            self.refresh_clients()
            return
        
        # Очистка
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        
        try:
            clients = self.backend.clients.search(query)
            for c in clients:
                created = str(c['created_at'])[:10] if c.get('created_at') else ''
                self.clients_tree.insert('', tk.END, values=(
                    c['id'], c['name'], c['email'], c['phone'], created
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Поиск не удался: {e}")
    
    def client_bookings(self):
        """Бронирования выбранного клиента."""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите клиента")
            return
        
        item = self.clients_tree.item(selection[0])
        client_id = item['values'][0]
        
        bookings = self.backend.bookings.get_by_client(client_id)
        
        if not bookings:
            messagebox.showinfo("Бронирования", "Нет бронирований")
            return
        
        msg = "Бронирования клиента:\n\n"
        for b in bookings:
            msg += f"#{b['id']} | {b['booking_date']} | {b['table_number']} | {b['status']}\n"
        
        messagebox.showinfo("Бронирования", msg)
    
    def change_table_status(self):
        """Изменить статус столика."""
        selection = self.tables_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите столик")
            return
        
        item = self.tables_tree.item(selection[0])
        table_id = item['values'][0]
        
        status = simpledialog.askstring("Изменить статус", 
                                        "Новый статус (available/occupied/reserved/maintenance):",
                                        initialvalue=item['values'][4])
        if not status:
            return
        
        try:
            if self.backend.tables.update_status(table_id, status):
                messagebox.showinfo("Успех", "Статус обновлён")
                self.refresh_tables()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить статус")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
    
    def show_availability_matrix(self):
        """Показать матрицу доступности."""
        date = self.availability_date.get().strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            matrix = self.backend.tables.get_availability_matrix(date)
            
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Матрица доступности на {date}")
            dialog.geometry("800x400")
            
            # Заголовок
            header_frame = ttk.Frame(dialog, padding=10)
            header_frame.pack(fill=tk.X)
            
            ttk.Label(header_frame, text=f"Матрица доступности на {date}", 
                     font=('Arial', 12, 'bold')).pack()
            
            # Создаём сетку
            time_slots = [f"{h:02d}:00" for h in range(10, 23)]
            
            # Заголовки столбцов
            cols_frame = ttk.Frame(dialog)
            cols_frame.pack(fill=tk.X, padx=10)
            
            ttk.Label(cols_frame, text="Стол", width=10, font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            for slot in time_slots:
                ttk.Label(cols_frame, text=slot[0:2], width=3, font=('Arial', 8)).pack(side=tk.LEFT)
            
            # Данные
            canvas = tk.Canvas(dialog)
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            for table_num, data in matrix.items():
                row_frame = ttk.Frame(scrollable_frame)
                row_frame.pack(fill=tk.X)
                
                ttk.Label(row_frame, text=table_num, width=10).pack(side=tk.LEFT)
                
                for slot in time_slots:
                    available = data['slots'].get(slot, False)
                    color = '#90EE90' if available else '#FFB6C1'
                    lbl = tk.Label(row_frame, text='✓' if available else '✗', 
                                  width=3, bg=color, font=('Arial', 8))
                    lbl.pack(side=tk.LEFT)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить матрицу: {e}")
    
    # === Контекстное меню для расписания ===
    
    def show_schedule_menu(self, event):
        """Показать контекстное меню."""
        item = self.schedule_tree.identify_row(event.y)
        if item:
            self.schedule_tree.selection_set(item)
            self.schedule_menu.post(event.x_root, event.y_root)
    
    def get_selected_schedule_booking(self):
        """Получить ID выбранного бронирования из расписания."""
        selection = self.schedule_tree.selection()
        if not selection:
            return None
        item = self.schedule_tree.item(selection[0])
        tags = item['tags']
        if tags:
            return int(tags[0])
        return None
    
    def confirm_booking_from_schedule(self):
        """Подтвердить бронь из расписания."""
        booking_id = self.get_selected_schedule_booking()
        if booking_id:
            if self.backend.bookings.confirm(booking_id):
                messagebox.showinfo("Успех", "Бронирование подтверждено")
                self.refresh_all()
    
    def cancel_booking_from_schedule(self):
        """Отменить бронь из расписания."""
        booking_id = self.get_selected_schedule_booking()
        if booking_id:
            if messagebox.askyesno("Подтверждение", "Отменить бронирование?"):
                self.backend.cancel_booking_with_notification(booking_id)
                self.refresh_all()
    
    def complete_booking_from_schedule(self):
        """Завершить бронь из расписания."""
        booking_id = self.get_selected_schedule_booking()
        if booking_id:
            if self.backend.bookings.complete(booking_id):
                messagebox.showinfo("Успех", "Бронирование завершено")
                self.refresh_all()
    
    # === Действия с бронированиями ===
    
    def get_selected_booking(self):
        """Получить ID выбранного бронирования."""
        selection = self.bookings_tree.selection()
        if not selection:
            return None
        item = self.bookings_tree.item(selection[0])
        return item['values'][0]
    
    def confirm_booking(self):
        """Подтвердить бронирование."""
        booking_id = self.get_selected_booking()
        if booking_id:
            if self.backend.bookings.confirm(booking_id):
                messagebox.showinfo("Успех", "Бронирование подтверждено")
                self.refresh_all()
    
    def cancel_booking(self):
        """Отменить бронирование."""
        booking_id = self.get_selected_booking()
        if booking_id and messagebox.askyesno("Подтверждение", "Отменить бронирование?"):
            self.backend.cancel_booking_with_notification(booking_id)
            self.refresh_all()
    
    def complete_booking(self):
        """Завершить бронирование."""
        booking_id = self.get_selected_booking()
        if booking_id:
            if self.backend.bookings.complete(booking_id):
                messagebox.showinfo("Успех", "Бронирование завершено")
                self.refresh_all()
    
    def delete_booking(self):
        """Удалить бронирование."""
        booking_id = self.get_selected_booking()
        if booking_id and messagebox.askyesno("Подтверждение", "Удалить бронирование?"):
            if self.backend.bookings.delete(booking_id):
                messagebox.showinfo("Успех", "Бронирование удалено")
                self.refresh_all()
    
    # === Утилиты ===
    
    def set_status(self, message: str):
        """Установить сообщение в статус баре."""
        self.status_bar.config(text=message)
    
    def on_closing(self):
        """Обработка закрытия окна."""
        if self.backend:
            self.backend.disconnect()
        self.root.destroy()


def main():
    """Точка входа."""
    root = tk.Tk()
    app = RestaurantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
