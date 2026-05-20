import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QStackedWidget, QMessageBox, QTextEdit,
    QProgressBar, QHeaderView, QGroupBox, QFrame
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QColor, QFont
import db_manager

# 1. СОЗДАЕМ НАДЕЖНУЮ ТЕМНУЮ ТЕМУ ПРЯМО В КОДЕ
# Это гарантирует, что текст будет белым, даже если style.qss пустой или не загружен.
GLOBAL_DARK_STYLE = """
/* Принудительно белый текст для всего приложения */
* {
    color: #ffffff;
    font-family: "Segoe UI", sans-serif;
}

/* Специфичные стили для виджетов, чтобы они выглядели красиво на темном */
QLabel {
    color: #e2e8f0; /* Светло-серый для текста */
}
QLabel[error="true"] {
    color: #ef4444; /* Красный для ошибок */
}
QLineEdit, QComboBox, QTextEdit {
    color: #ffffff;
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 4px;
    border-radius: 4px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #6366f1;
}
QTableWidget {
    background-color: #0f172a;
    gridline-color: #334155;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #1e293b;
    color: #cbd5e1;
    padding: 5px;
    border: 1px solid #334155;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #1e293b;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #475569;
    border-radius: 5px;
}
QProgressBar {
    border: 1px solid #334155;
    border-radius: 5px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #6366f1;
}
QToolTip {
    background-color: #1e293b;
    color: #ffffff;
    border: 1px solid #334155;
}
"""

# Пытаемся загрузить внешний файл, если он есть, и добавляем к нашему глобальному стилю
style_path = "style.qss"
QSS_STYLE = GLOBAL_DARK_STYLE  # Начинаем с нашего надежного стиля
if os.path.exists(style_path):
    with open(style_path, "r", encoding="utf-8") as f:
        # Добавляем содержимое файла ПОСЛЕ нашего стиля, чтобы он мог переопределять детали
        QSS_STYLE += f.read()


def load_ui(filename):
    """Загружает .ui файл динамически"""
    loader = QUiLoader()
    file = QFile(filename)
    if not file.open(QFile.ReadOnly):
        print(f"Ошибка открытия файла: {filename}")
        sys.exit(1)
    window = loader.load(file)
    file.close()
    return window


class WMSApp:
    def __init__(self):
        # 1. Запуск БД и инициализация таблиц
        db_manager.init_db()

        # 2. Загрузка UI файлов
        self.login_win = load_ui("login.ui")
        self.main_win = load_ui("mainwindow.ui")

        # Загрузка отдельных страниц для операций
        self.dashboard_page = load_ui("dashboard.ui")
        self.receiving_page = load_ui("receiving.ui")
        self.inventory_page = load_ui("inventory.ui")
        self.quality_page = load_ui("quality.ui")
        self.shipping_page = load_ui("shipping.ui")
        self.tasks_page = load_ui("tasks.ui")
        self.reports_page = load_ui("reports.ui")

        # 3. ПРИМЕНЕНИЕ СТИЛЕЙ КО ВСЕМУ ПРИЛОЖЕНИЮ
        # Это критически важно, чтобы стиль применялся и к диалогам, и к всплывающим окнам
        QApplication.instance().setStyleSheet(QSS_STYLE)

        # Также применяем к окнам для надежности
        self.login_win.setStyleSheet(QSS_STYLE)
        self.main_win.setStyleSheet(QSS_STYLE)

        self.main_win.hide()

        # Привязка логики входа
        self.login_btn = self.login_win.findChild(QPushButton, "btnLogin")
        if self.login_btn:
            self.login_btn.clicked.connect(self.check_login)

        # 3. Перестроение кнопок главного меню
        self.setup_menu_buttons()

        # 4. Создание QStackedWidget
        self.setup_stacked_widget()

        # 5. Инициализация всех подразделов
        self.init_dashboard_page()
        self.init_receiving_page()
        self.init_inventory_page()
        self.init_quality_page()
        self.init_shipping_page()
        self.init_tasks_page()
        self.init_reports_page()

        # 6. Первоначальный запуск на главной панели
        self.switch_page(0)

        # 7. Запуск стартового окна авторизации
        self.login_win.show()

    # ... (Остальной код класса WMSApp остается без изменений) ...
    # Вставьте сюда весь ваш код методов класса WMSApp (check_login, setup_menu_buttons и т.д.)
    # Ниже я привожу только те методы, которые могут требовать внимания, но в целом они должны работать
    # если вы скопируете их из вашего исходника.

    def check_login(self):
        login_input = self.login_win.findChild(QLineEdit, "lineEditLogin")
        pass_input = self.login_win.findChild(QLineEdit, "lineEditPassword")
        err_lbl = self.login_win.findChild(QLabel, "lblError")

        username = login_input.text()
        password = pass_input.text()

        if username == "admin" and password == "1234":
            err_lbl.setText("")
            self.login_win.accept()
            self.main_win.show()
            self.log_event("Пользователь admin успешно авторизовался в системе.")
            self.refresh_dashboard_data()
        else:
            err_lbl.setText("Неверный логин или пароль!")
            self.log_event(f"Попытка входа с неверными учетными данными: '{username}'")

    def setup_menu_buttons(self):
        self.btn_rec = self.main_win.findChild(QPushButton, "btnReceiving")
        self.btn_inv = self.main_win.findChild(QPushButton, "btnInventory")
        self.btn_qual = self.main_win.findChild(QPushButton, "btnQuality")
        self.btn_ship = self.main_win.findChild(QPushButton, "btnShipping")
        self.btn_rep = self.main_win.findChild(QPushButton, "btnReports")
        self.btn_exit = self.main_win.findChild(QPushButton, "btnExit")

        self.btn_rec.hide()
        self.btn_inv.hide()
        self.btn_qual.hide()
        self.btn_ship.hide()
        self.btn_rep.hide()
        self.btn_exit.hide()

        menu_frame = QFrame(self.main_win.findChild(QWidget, "centralwidget"))
        menu_frame.setGeometry(20, 110, 760, 45)
        menu_layout = QHBoxLayout(menu_frame)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(8)

        self.btn_menu_dashboard = QPushButton("Главная панель")
        self.btn_menu_rec = QPushButton("Приемка товара")
        self.btn_menu_inv = QPushButton("Инвентаризация")
        self.btn_menu_qual = QPushButton("Контроль качества")
        self.btn_menu_ship = QPushButton("Отгрузка товара")
        self.btn_menu_tsd = QPushButton("Задачи ТСД (Мобильный)")
        self.btn_menu_rep = QPushButton("Отчетность")
        self.btn_menu_exit = QPushButton("Выход")

        for btn in [self.btn_menu_dashboard, self.btn_menu_rec, self.btn_menu_inv, self.btn_menu_qual,
                    self.btn_menu_ship, self.btn_menu_tsd, self.btn_menu_rep]:
            btn.setCheckable(True)

        # Исправляем стиль кнопки выхода, чтобы текст был виден
        self.btn_menu_exit.setStyleSheet("background-color: #ef4444; color: #ffffff; font-weight: bold;")

        menu_layout.addWidget(self.btn_menu_dashboard)
        menu_layout.addWidget(self.btn_menu_rec)
        menu_layout.addWidget(self.btn_menu_inv)
        menu_layout.addWidget(self.btn_menu_qual)
        menu_layout.addWidget(self.btn_menu_ship)
        menu_layout.addWidget(self.btn_menu_tsd)
        menu_layout.addWidget(self.btn_menu_rep)
        menu_layout.addWidget(self.btn_menu_exit)

        self.btn_menu_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.btn_menu_rec.clicked.connect(lambda: self.switch_page(1))
        self.btn_menu_inv.clicked.connect(lambda: self.switch_page(2))
        self.btn_menu_qual.clicked.connect(lambda: self.switch_page(3))
        self.btn_menu_ship.clicked.connect(lambda: self.switch_page(4))
        self.btn_menu_tsd.clicked.connect(lambda: self.switch_page(5))
        self.btn_menu_rep.clicked.connect(lambda: self.switch_page(6))
        self.btn_menu_exit.clicked.connect(self.main_win.close)

    def setup_stacked_widget(self):
        centralwidget = self.main_win.findChild(QWidget, "centralwidget")
        self.stacked_widget = QStackedWidget(centralwidget)
        self.stacked_widget.setGeometry(20, 175, 760, 380)
        # Убираем жесткий фон виджета, так как у нас теперь глобальный темный стиль,
        # чтобы избежать конфликтов.
        self.stacked_widget.setStyleSheet("border: 1px solid #2d2d3d; border-radius: 8px;")

        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.receiving_page)
        self.stacked_widget.addWidget(self.inventory_page)
        self.stacked_widget.addWidget(self.quality_page)
        self.stacked_widget.addWidget(self.shipping_page)
        self.stacked_widget.addWidget(self.tasks_page)
        self.stacked_widget.addWidget(self.reports_page)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

        buttons = [
            self.btn_menu_dashboard, self.btn_menu_rec, self.btn_menu_inv,
            self.btn_menu_qual, self.btn_menu_ship, self.btn_menu_tsd,
            self.btn_menu_rep
        ]
        for i, btn in enumerate(buttons):
            btn.setChecked(i == index)

        self.refresh_all_data()

    def refresh_all_data(self):
        if hasattr(self, "refresh_dashboard_data"): self.refresh_dashboard_data()
        if hasattr(self, "refresh_receiving_data"): self.refresh_receiving_data()
        if hasattr(self, "refresh_inventory_data"): self.refresh_inventory_data()
        if hasattr(self, "refresh_quality_data"): self.refresh_quality_data()
        if hasattr(self, "refresh_shipping_data"): self.refresh_shipping_data()
        if hasattr(self, "refresh_tasks_table"): self.refresh_tasks_table()
        if hasattr(self, "on_report_type_changed"): self.on_report_type_changed()

    def log_event(self, message):
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO documents (doc_type, timestamp, content) VALUES (?, ?, ?)", ('LOG', now, message))
        conn.commit()
        conn.close()
        if hasattr(self, 'refresh_dashboard_logs'): self.refresh_dashboard_logs()

    # ================= 0. ГЛАВНАЯ ПАНЕЛЬ =================
    def init_dashboard_page(self):
        self.lbl_stat_total = self.dashboard_page.findChild(QLabel, "lblStatTotal")
        self.lbl_stat_sku = self.dashboard_page.findChild(QLabel, "lblStatSku")
        self.lbl_stat_blocked = self.dashboard_page.findChild(QLabel, "lblStatBlocked")
        self.lbl_stat_tasks = self.dashboard_page.findChild(QLabel, "lblStatTasks")
        self.log_view = self.dashboard_page.findChild(QTextEdit, "logView")
        self.btn_refresh = self.dashboard_page.findChild(QPushButton, "btnRefresh")

        self.btn_refresh.clicked.connect(self.refresh_dashboard_data)

    def refresh_dashboard_data(self):
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(qty) FROM products")
        total_qty = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(DISTINCT sku) FROM products")
        total_sku = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(qty) FROM products WHERE quality_status = ?", ('BLOCKED',))
        blocked_qty = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status != ?", ('COMPLETED',))
        active_tasks = cursor.fetchone()[0] or 0
        conn.close()

        self.lbl_stat_total.setText(f"Всего товаров на складе: <b>{total_qty} шт.</b>")
        self.lbl_stat_sku.setText(f"Уникальных артикулов (SKU): <b>{total_sku}</b>")
        self.lbl_stat_blocked.setText(f"Заблокировано (брак): <b>{blocked_qty} шт.</b>")
        self.lbl_stat_tasks.setText(f"Активных задач ТСД: <b>{active_tasks}</b>")

        self.refresh_dashboard_logs()

    def refresh_dashboard_logs(self):
        if not hasattr(self, "log_view") or not self.log_view: return
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, content FROM documents WHERE doc_type = ? ORDER BY id DESC LIMIT 15",
                       ('LOG',))
        logs = cursor.fetchall()
        conn.close()

        log_text = ""
        for ts, msg in logs:
            # Используем цвет, который хорошо виден на темном
            log_text += f"<span style='color: #818cf8;'>[{ts}]</span> {msg}<br>"
        self.log_view.setHtml(log_text)

    # ================= 1. ПРИЕМКА ТОВАРА =================
    def init_receiving_page(self):
        self.btn_create_rec_doc = self.receiving_page.findChild(QPushButton, "btnCreateDoc")
        self.lbl_rec_doc = self.receiving_page.findChild(QLabel, "lblDocNumber")
        self.rec_form_box = self.receiving_page.findChild(QGroupBox, "grpBoxForm")

        self.txt_rec_sku = self.receiving_page.findChild(QLineEdit, "txtSku")
        self.txt_rec_qty = self.receiving_page.findChild(QLineEdit, "txtQty")
        self.txt_rec_lot = self.receiving_page.findChild(QLineEdit, "txtLot")
        self.txt_rec_loc = self.receiving_page.findChild(QLineEdit, "txtLoc")

        self.lbl_rec_assoc = self.receiving_page.findChild(QLabel, "lblAssocStatus")
        self.lbl_rec_new_name = self.receiving_page.findChild(QLabel, "lblNewName")
        self.txt_rec_new_name = self.receiving_page.findChild(QLineEdit, "txtNewName")

        self.btn_confirm_rec = self.receiving_page.findChild(QPushButton, "btnConfirm")

        self.lbl_rec_new_name.hide()
        self.txt_rec_new_name.hide()
        self.rec_form_box.setEnabled(False)
        self.btn_confirm_rec.setEnabled(False)

        self.btn_create_rec_doc.clicked.connect(self.create_receiving_document)
        self.txt_rec_sku.textChanged.connect(self.on_receiving_sku_changed)
        self.btn_confirm_rec.clicked.connect(self.confirm_receiving)

    def refresh_receiving_data(self):
        pass

    def create_receiving_document(self):
        self.rec_doc_number = f"REC-ACT-{datetime.now().strftime('%M%S')}"
        self.lbl_rec_doc.setText(f"Акт приемки: <b>{self.rec_doc_number}</b> (ОТКРЫТ)")
        self.rec_form_box.setEnabled(True)
        self.btn_confirm_rec.setEnabled(True)
        self.txt_rec_lot.setText(f"LOT-{datetime.now().strftime('%d%H%M')}")
        self.log_event(f"Приемка: Открыт новый Акт приемки № {self.rec_doc_number}")

    def on_receiving_sku_changed(self):
        sku = self.txt_rec_sku.text().strip()
        if not sku:
            self.lbl_rec_assoc.setText("Ассоциация: Ожидание ввода штрихкода...")
            self.lbl_rec_new_name.hide()
            self.txt_rec_new_name.hide()
            return

        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, lot_number FROM products WHERE sku = ?", (sku,))
        res = cursor.fetchone()
        conn.close()

        if res:
            name, lot = res
            self.lbl_rec_assoc.setText(f"✅ Товар найден в базе: <b>'{name}'</b> (Партия: {lot})")
            self.lbl_rec_new_name.hide()
            self.txt_rec_new_name.hide()
        else:
            self.lbl_rec_assoc.setText("⚠️ <b>Новый штрихкод!</b> Заполните название товара для ассоциации:")
            self.lbl_rec_new_name.show()
            self.txt_rec_new_name.show()

    def confirm_receiving(self):
        sku = self.txt_rec_sku.text().strip()
        qty_str = self.txt_rec_qty.text().strip()
        lot = self.txt_rec_lot.text().strip()
        loc = self.txt_rec_loc.text().strip()

        if not sku or not qty_str or not lot or not loc:
            QMessageBox.warning(self.main_win, "Ошибка", "Все поля должны быть заполнены!")
            return

        try:
            qty = int(qty_str)
            if qty <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self.main_win, "Ошибка", "Количество должно быть целым положительным числом!")
            return

        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE sku = ?", (sku,))
        res = cursor.fetchone()

        is_new_product = False
        if res:
            name = res[0]
            cursor.execute("UPDATE products SET qty = qty + ? WHERE sku = ?", (qty, sku))
        else:
            name = self.txt_rec_new_name.text().strip()
            if not name:
                QMessageBox.warning(self.main_win, "Ошибка", "Заполните название нового товара!")
                conn.close()
                return
            is_new_product = True
            cursor.execute("""
                INSERT INTO products (sku, name, qty, lot_number, quality_status, location)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sku, name, qty, lot, 'PENDING', loc))

        cursor.execute("""
            INSERT INTO documents (doc_type, timestamp, content)
            VALUES (?, ?, ?)
        """, ('RECEIVING', datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              f"Акт приемки {self.rec_doc_number}. Продукция: {name} (SKU: {sku}), Кол-во: {qty} шт., Размещено в ячейке: {loc}"))

        conn.commit()
        conn.close()

        if is_new_product:
            self.log_event(
                f"Приемка: Создан новый товар '{name}' ({sku}), партия {lot}, кол-во {qty} шт. Статус: На проверку качества.")
        else:
            self.log_event(f"Приемка: Товар '{name}' ({sku}) в количестве {qty} шт. добавлен к существующей партии.")

        QMessageBox.information(self.main_win, "Успех", f"Товар успешно размещен в зоне приемки (Ячейка: {loc})!")

        self.txt_rec_sku.clear()
        self.txt_rec_qty.clear()
        self.txt_rec_loc.clear()
        self.txt_rec_new_name.clear()
        self.rec_form_box.setEnabled(False)
        self.btn_confirm_rec.setEnabled(False)
        self.lbl_rec_doc.setText("Акт приемки: не создан")
        self.refresh_all_data()

    # ================= 2. ИНВЕНТАРИЗАЦИЯ =================
    def init_inventory_page(self):
        self.btn_start_inv = self.inventory_page.findChild(QPushButton, "btnStartCount")
        self.lbl_inv_status = self.inventory_page.findChild(QLabel, "lblInvStatus")
        self.inv_proc_box = self.inventory_page.findChild(QGroupBox, "grpBoxProc")
        self.cmb_inv_prod = self.inventory_page.findChild(QComboBox, "cmbProducts")
        self.lbl_inv_expected = self.inventory_page.findChild(QLabel, "lblExpectedQty")
        self.txt_inv_actual = self.inventory_page.findChild(QLineEdit, "txtActualQty")
        self.btn_save_inv_item = self.inventory_page.findChild(QPushButton, "btnSaveCount")
        self.tbl_inventory = self.inventory_page.findChild(QTableWidget, "tblInventory")
        self.lbl_inv_result_msg = self.inventory_page.findChild(QLabel, "lblResultMsg")
        self.btn_create_discrepancy_act = self.inventory_page.findChild(QPushButton, "btnDiscrepancy")
        self.btn_finish_inventory = self.inventory_page.findChild(QPushButton, "btnFinishCount")

        self.tbl_inventory.setColumnCount(5)
        self.tbl_inventory.setHorizontalHeaderLabels(["Артикул", "Наименование", "Учет", "Факт", "Разница"])
        self.tbl_inventory.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.inv_proc_box.setEnabled(False)
        self.btn_create_discrepancy_act.setEnabled(False)
        self.btn_finish_inventory.setEnabled(False)

        self.btn_start_inv.clicked.connect(self.start_inventory_session)
        self.cmb_inv_prod.currentIndexChanged.connect(self.on_inventory_product_selected)
        self.btn_save_inv_item.clicked.connect(self.save_inventory_item)
        self.btn_create_discrepancy_act.clicked.connect(self.create_discrepancy_act)
        self.btn_finish_inventory.clicked.connect(self.finish_inventory)

    def refresh_inventory_data(self):
        if self.inv_proc_box.isEnabled(): return
        self.cmb_inv_prod.blockSignals(True)
        self.cmb_inv_prod.clear()

        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sku, name, qty FROM products")
        self.inventory_products = cursor.fetchall()
        conn.close()

        for sku, name, qty in self.inventory_products:
            self.cmb_inv_prod.addItem(f"{name} (SKU: {sku})", sku)
        self.cmb_inv_prod.blockSignals(False)
        self.on_inventory_product_selected()

    def start_inventory_session(self):
        self.inventory_session_data = {}
        self.tbl_inventory.setRowCount(0)
        self.inv_proc_box.setEnabled(True)
        self.lbl_inv_status.setText("Инвентаризация: В ПРОЦЕССЕ")
        self.log_event("Инвентаризация: Запланирован и запущен пересчет товаров на складе.")
        self.refresh_inventory_data()

    def on_inventory_product_selected(self):
        sku = self.cmb_inv_prod.currentData()
        if not sku: return
        for db_sku, name, qty in self.inventory_products:
            if db_sku == sku:
                self.lbl_inv_expected.setText(str(qty))
                break

    def save_inventory_item(self):
        sku = self.cmb_inv_prod.currentData()
        actual_qty_str = self.txt_inv_actual.text().strip()
        if not sku or not actual_qty_str:
            QMessageBox.warning(self.main_win, "Ошибка", "Заполните фактическое количество!")
            return
        try:
            actual_qty = int(actual_qty_str)
            if actual_qty < 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self.main_win, "Ошибка", "Количество должно быть целым неотрицательным числом!")
            return

        name = ""
        expected_qty = 0
        for db_sku, db_name, db_qty in self.inventory_products:
            if db_sku == sku:
                name = db_name
                expected_qty = db_qty
                break

        self.inventory_session_data[sku] = {"name": name, "expected": expected_qty, "actual": actual_qty}
        self.tbl_inventory.setRowCount(0)
        has_discrepancies = False

        for item_sku, data in self.inventory_session_data.items():
            row_idx = self.tbl_inventory.rowCount()
            self.tbl_inventory.insertRow(row_idx)
            diff = data["actual"] - data["expected"]
            diff_str = f"+{diff}" if diff > 0 else str(diff)

            self.tbl_inventory.setItem(row_idx, 0, QTableWidgetItem(item_sku))
            self.tbl_inventory.setItem(row_idx, 1, QTableWidgetItem(data["name"]))
            self.tbl_inventory.setItem(row_idx, 2, QTableWidgetItem(str(data["expected"])))
            self.tbl_inventory.setItem(row_idx, 3, QTableWidgetItem(str(data["actual"])))

            diff_item = QTableWidgetItem(diff_str)
            if diff != 0:
                has_discrepancies = True
                diff_item.setForeground(QColor("#ef4444"))
                font = diff_item.font()
                font.setBold(True)
                diff_item.setFont(font)
            else:
                diff_item.setForeground(QColor("#10b981"))
                font = diff_item.font()
                font.setBold(True)
                diff_item.setFont(font)
            self.tbl_inventory.setItem(row_idx, 4, diff_item)

        self.txt_inv_actual.clear()
        self.btn_finish_inventory.setEnabled(True)
        if has_discrepancies:
            self.lbl_inv_result_msg.setText(
                "⚠️ <b>Есть расхождения с учетными данными!</b> Требуется составить Акт расхождений.")
            self.lbl_inv_result_msg.setStyleSheet("color: #f59e0b;")
            self.btn_create_discrepancy_act.setEnabled(True)
        else:
            self.lbl_inv_result_msg.setText("✅ <b>Расхождений не обнаружено!</b> Данные соответствуют учетным.")
            self.lbl_inv_result_msg.setStyleSheet("color: #10b981;")
            self.btn_create_discrepancy_act.setEnabled(False)

    def create_discrepancy_act(self):
        self.discrepancy_doc_number = f"DISC-ACT-{datetime.now().strftime('%M%S')}"
        QMessageBox.information(self.main_win, "Акт сформирован",
                                f"Акт о расхождениях {self.discrepancy_doc_number} успешно сформирован в системе!")
        self.log_event(f"Инвентаризация: Сформирован Акт о расхождениях {self.discrepancy_doc_number}")
        self.btn_create_discrepancy_act.setEnabled(False)

    def finish_inventory(self):
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        corrections_made = 0
        for sku, data in self.inventory_session_data.items():
            if data["actual"] != data["expected"]:
                cursor.execute("UPDATE products SET qty = ? WHERE sku = ?", (data["actual"], sku))
                corrections_made += 1

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO documents (doc_type, timestamp, content) VALUES (?, ?, ?)",
                       ('INVENTORY', now, f"Инвентаризация проведена. Скорректировано позиций: {corrections_made}."))
        conn.commit()
        conn.close()

        QMessageBox.information(self.main_win, "Инвентаризация завершена",
                                f"Остатки успешно скорректированы в системе!\nСкорректировано позиций: {corrections_made}.")
        self.log_event(f"Инвентаризация завершена. Проведена автокорректировка {corrections_made} остатков.")

        self.inv_proc_box.setEnabled(False)
        self.btn_create_discrepancy_act.setEnabled(False)
        self.btn_finish_inventory.setEnabled(False)
        self.lbl_inv_status.setText("Инвентаризация: Ожидание запуска")
        self.lbl_inv_result_msg.setText("Ожидание завершения пересчета позиций...")
        self.lbl_inv_result_msg.setStyleSheet("color: #cbd5e1;")
        self.refresh_all_data()

    # ================= 3. КОНТРОЛЬ КАЧЕСТВА =================
    def init_quality_page(self):
        self.cmb_quality_prod = self.quality_page.findChild(QComboBox, "cmbLots")
        self.lbl_quality_details = self.quality_page.findChild(QLabel, "lblLotDetails")
        self.pbar_quality = self.quality_page.findChild(QProgressBar, "pbarQuality")
        self.btn_run_quality_test = self.quality_page.findChild(QPushButton, "btnRunTest")
        self.decision_box = self.quality_page.findChild(QGroupBox, "grpBoxDecision")
        self.btn_quality_accept = self.quality_page.findChild(QPushButton, "btnAcceptLot")
        self.btn_quality_reject = self.quality_page.findChild(QPushButton, "btnRejectLot")

        self.decision_box.setEnabled(False)

        self.cmb_quality_prod.currentIndexChanged.connect(self.on_quality_product_selected)
        self.btn_run_quality_test.clicked.connect(self.run_quality_test)
        self.btn_quality_accept.clicked.connect(self.confirm_quality_accept)
        self.btn_quality_reject.clicked.connect(self.confirm_quality_reject)

    def refresh_quality_data(self):
        if hasattr(self, "quality_timer") and self.quality_timer.isActive(): return
        self.cmb_quality_prod.blockSignals(True)
        self.cmb_quality_prod.clear()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sku, name, lot_number, qty, quality_status FROM products")
        self.quality_products = cursor.fetchall()
        conn.close()

        for sku, name, lot, qty, status in self.quality_products:
            status_text = "ОЖИДАЕТ" if status == "PENDING" else ("ЗАБЛОК" if status == "BLOCKED" else "ОДОБРЕН")
            self.cmb_quality_prod.addItem(f"Партия: {lot} | {name} ({qty} шт.) [{status_text}]", sku)
        self.cmb_quality_prod.blockSignals(False)
        self.on_quality_product_selected()

    def on_quality_product_selected(self):
        sku = self.cmb_quality_prod.currentData()
        if not sku: return
        self.pbar_quality.setValue(0)
        self.decision_box.setEnabled(False)

        for db_sku, name, lot, qty, status in self.quality_products:
            if db_sku == sku:
                status_color = "#ef4444" if status == "BLOCKED" else ("#f59e0b" if status == "PENDING" else "#10b981")
                self.lbl_quality_details.setText(
                    f"<b>Номенклатура:</b> {name}<br>"
                    f"<b>Штрихкод (SKU):</b> {sku} | <b>Партия:</b> {lot}<br>"
                    f"<b>Объем:</b> {qty} шт.<br>"
                    f"<b>Текущий статус качества:</b> <font color='{status_color}'><b>{status}</b></font>"
                )
                break

    def run_quality_test(self):
        sku = self.cmb_quality_prod.currentData()
        if not sku: return
        self.btn_run_quality_test.setEnabled(False)
        self.cmb_quality_prod.setEnabled(False)
        self.pbar_quality.setValue(0)
        self.quality_progress = 0
        self.quality_timer = QTimer()
        self.quality_timer.timeout.connect(self.advance_quality_progress)
        self.quality_timer.start(50)

    def advance_quality_progress(self):
        self.quality_progress += 2.5
        self.pbar_quality.setValue(int(self.quality_progress))
        if self.quality_progress >= 100:
            self.quality_timer.stop()
            self.btn_run_quality_test.setEnabled(True)
            self.cmb_quality_prod.setEnabled(True)
            self.decision_box.setEnabled(True)
            QMessageBox.information(self.main_win, "Тест завершен",
                                    "Лабораторный анализ партии успешно проведен! Пожалуйста, вынесите решение.")

    def confirm_quality_accept(self):
        sku = self.cmb_quality_prod.currentData()
        if not sku: return
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, lot_number FROM products WHERE sku = ?", (sku,))
        name, lot = cursor.fetchone()
        cursor.execute("UPDATE products SET quality_status = ? WHERE sku = ?", ('APPROVED', sku))
        conn.commit()
        conn.close()

        QMessageBox.information(self.main_win, "Утверждено",
                                f"Партия {lot} успешно РАЗБЛОКИРОВАНА и готова к отгрузке!")
        self.log_event(f"Качество: Партия {lot} ('{name}') успешно прошла проверку и РАЗБЛОКИРОВАНА.")
        self.pbar_quality.setValue(0)
        self.decision_box.setEnabled(False)
        self.refresh_all_data()

    def confirm_quality_reject(self):
        sku = self.cmb_quality_prod.currentData()
        if not sku: return
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, lot_number FROM products WHERE sku = ?", (sku,))
        name, lot = cursor.fetchone()
        cursor.execute("UPDATE products SET quality_status = ? WHERE sku = ?", ('BLOCKED', sku))
        conn.commit()
        conn.close()

        QMessageBox.warning(self.main_win, "Заблокировано", f"Партия {lot} признана браком и полностью ЗАБЛОКИРОВАНА!")
        self.log_event(f"Качество: ВНИМАНИЕ! Партия {lot} ('{name}') забракована и переведена в статус БЛОКИРОВКИ.")
        self.pbar_quality.setValue(0)
        self.decision_box.setEnabled(False)
        self.refresh_all_data()

    # ================= 4. ОТГРУЗКА ТОВАРА =================
    def init_shipping_page(self):
        self.cmb_ship_prod = self.shipping_page.findChild(QComboBox, "cmbShipProducts")
        self.lbl_ship_stock_info = self.shipping_page.findChild(QLabel, "lblStockInfo")
        self.txt_ship_qty = self.shipping_page.findChild(QLineEdit, "txtShipQty")
        self.btn_verify_ship = self.shipping_page.findChild(QPushButton, "btnVerify")
        self.ship_ops_box = self.shipping_page.findChild(QGroupBox, "grpBoxOps")
        self.lbl_ship_status = self.shipping_page.findChild(QLabel, "lblShipStatus")
        self.btn_create_pick_task = self.shipping_page.findChild(QPushButton, "btnCreatePickTask")
        self.btn_ship_instant = self.shipping_page.findChild(QPushButton, "btnShipInstant")

        self.ship_ops_box.setEnabled(False)

        self.cmb_ship_prod.currentIndexChanged.connect(self.on_shipping_product_selected)
        self.btn_verify_ship.clicked.connect(self.verify_shipping)
        self.btn_create_pick_task.clicked.connect(self.create_shipping_pick_task)
        self.btn_ship_instant.clicked.connect(self.ship_product_instant)

    def refresh_shipping_data(self):
        if self.ship_ops_box.isEnabled(): return
        self.cmb_ship_prod.blockSignals(True)
        self.cmb_ship_prod.clear()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sku, name, qty, quality_status FROM products")
        self.ship_products = cursor.fetchall()
        conn.close()

        for sku, name, qty, status in self.ship_products:
            self.cmb_ship_prod.addItem(f"{name} (SKU: {sku}) [{status}]", sku)
        self.cmb_ship_prod.blockSignals(False)
        self.on_shipping_product_selected()

    def on_shipping_product_selected(self):
        sku = self.cmb_ship_prod.currentData()
        if not sku: return
        for db_sku, name, qty, status in self.ship_products:
            if db_sku == sku:
                self.lbl_ship_stock_info.setText(f"Текущие запасы: <b>{qty} шт.</b> | Статус качества: <b>{status}</b>")
                break

    def verify_shipping(self):
        sku = self.cmb_ship_prod.currentData()
        qty_str = self.txt_ship_qty.text().strip()
        if not sku or not qty_str:
            QMessageBox.warning(self.main_win, "Ошибка", "Заполните количество для отгрузки!")
            return
        try:
            qty = int(qty_str)
            if qty <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self.main_win, "Ошибка", "Количество должно быть целым положительным числом!")
            return

        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, qty, quality_status FROM products WHERE sku = ?", (sku,))
        res = cursor.fetchone()
        conn.close()

        if not res:
            QMessageBox.warning(self.main_win, "Ошибка", "Выбранный товар не найден в базе!")
            return

        name, db_qty, status = res

        if qty > db_qty:
            self.lbl_ship_status.setText(f"❌ Недостаточно товара! Доступно: {db_qty} шт., Требуется: {qty} шт.")
            self.lbl_ship_status.setStyleSheet("color: #ef4444; font-weight: bold;")
            self.ship_ops_box.setEnabled(False)
            self.log_event(f"Отгрузка: Ошибка проверки доступности '{name}' ({sku}). Недостаточно запасов.")
        elif status == "BLOCKED":
            self.lbl_ship_status.setText("❌ Партия ЗАБЛОКИРОВАНА (БРАК)! Отгрузка невозможна.")
            self.lbl_ship_status.setStyleSheet("color: #ef4444; font-weight: bold;")
            self.ship_ops_box.setEnabled(False)
            self.log_event(f"Отгрузка: Отклонено! Попытка отгрузки заблокированного товара '{name}' ({sku}).")
        elif status == "PENDING":
            self.lbl_ship_status.setText("❌ Товар ожидает контроля качества (PENDING)! Сначала подтвердите качество.")
            self.lbl_ship_status.setStyleSheet("color: #f59e0b; font-weight: bold;")
            self.ship_ops_box.setEnabled(False)
            self.log_event(f"Отгрузка: Отклонено! Товар '{name}' ({sku}) еще не прошел проверку ОТК.")
        else:
            self.lbl_ship_status.setText("✅ Проверка пройдена! Товар доступен, партия утверждена.")
            self.lbl_ship_status.setStyleSheet("color: #10b981; font-weight: bold;")
            self.ship_ops_box.setEnabled(True)
            self.log_event(f"Отгрузка: Успешная проверка доступности '{name}' ({sku}) в объеме {qty} шт.")

    def create_shipping_pick_task(self):
        sku = self.cmb_ship_prod.currentData()
        qty = int(self.txt_ship_qty.text())
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE sku = ?", (sku,))
        name = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO tasks (description, status, target_sku, target_qty, worker_name)
            VALUES (?, ?, ?, ?, ?)
        """, (f"Отбор товара '{name}' для отгрузки", 'PENDING', sku, qty, 'Кладовщик ТСД'))
        conn.commit()
        conn.close()

        QMessageBox.information(self.main_win, "Задача создана",
                                f"Складская задача на отбор для SKU {sku} ({qty} шт.) успешно передана на мобильные ТСД!")
        self.log_event(f"Отгрузка: Создано задание на отбор товара '{name}' ({qty} шт.) кладовщику на ТСД.")
        self.txt_ship_qty.clear()
        self.ship_ops_box.setEnabled(False)
        self.lbl_ship_status.setText("Статус проверки: Ожидание ввода данных...")
        self.lbl_ship_status.setStyleSheet("color: #cbd5e1; font-style: italic;")
        self.refresh_all_data()

    def ship_product_instant(self):
        sku = self.cmb_ship_prod.currentData()
        qty = int(self.txt_ship_qty.text())
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE sku = ?", (sku,))
        name = cursor.fetchone()[0]
        cursor.execute("UPDATE products SET qty = qty - ? WHERE sku = ?", (qty, sku))
        ship_doc = f"SHIP-ACT-{datetime.now().strftime('%M%S')}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO documents (doc_type, timestamp, content) VALUES (?, ?, ?)", ('SHIPPING', now,
                                                                                                 f"Оформлена расходная накладная {ship_doc}. Списано: {name} (SKU: {sku}), Кол-во: {qty} шт."))
        conn.commit()
        conn.close()

        QMessageBox.information(self.main_win, "Отгрузка проведена",
                                f"Расходный ордер {ship_doc} проведен. Товар физически отгружен со склада!")
        self.log_event(
            f"Отгрузка: Прямое списание со склада. Списан товар '{name}' ({qty} шт.) по накладной {ship_doc}.")
        self.txt_ship_qty.clear()
        self.ship_ops_box.setEnabled(False)
        self.lbl_ship_status.setText("Статус проверки: Ожидание ввода данных...")
        self.lbl_ship_status.setStyleSheet("color: #cbd5e1; font-style: italic;")
        self.refresh_all_data()

    # ================= 5. ЗАДАЧИ ТСД =================
    def init_tasks_page(self):
        self.tbl_tasks = self.tasks_page.findChild(QTableWidget, "tblTasks")
        self.tsd_console_box = self.tasks_page.findChild(QGroupBox, "grpBoxTSD")
        self.lbl_tsd_task_desc = self.tasks_page.findChild(QLabel, "lblTsdTaskDesc")
        self.btn_take_task = self.tasks_page.findChild(QPushButton, "btnTakeTask")
        self.btn_scan_task = self.tasks_page.findChild(QPushButton, "btnScanTask")
        self.btn_exec_task = self.tasks_page.findChild(QPushButton, "btnExecTask")

        self.tbl_tasks.setColumnCount(5)
        self.tbl_tasks.setHorizontalHeaderLabels(
            ["ID Задачи", "Описание складской задачи", "Товар SKU", "Количество", "Текущий статус"])
        self.tbl_tasks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tbl_tasks.itemSelectionChanged.connect(self.on_task_selected)
        self.btn_take_task.clicked.connect(self.take_task_in_hand)
        self.btn_scan_task.clicked.connect(self.scan_pick_barcode)
        self.btn_exec_task.clicked.connect(self.execute_task_completed)

    def refresh_tasks_table(self):
        self.tbl_tasks.setRowCount(0)
        self.btn_take_task.setEnabled(False)
        self.btn_scan_task.setEnabled(False)
        self.btn_exec_task.setEnabled(False)
        self.lbl_tsd_task_desc.setText("Выберите задачу в таблице для работы")

        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, description, target_sku, target_qty, status FROM tasks ORDER BY id DESC")
        tasks = cursor.fetchall()
        conn.close()

        for t_id, desc, sku, qty, status in tasks:
            row_idx = self.tbl_tasks.rowCount()
            self.tbl_tasks.insertRow(row_idx)
            self.tbl_tasks.setItem(row_idx, 0, QTableWidgetItem(str(t_id)))
            self.tbl_tasks.setItem(row_idx, 1, QTableWidgetItem(desc))
            self.tbl_tasks.setItem(row_idx, 2, QTableWidgetItem(sku))
            self.tbl_tasks.setItem(row_idx, 3, QTableWidgetItem(str(qty)))

            status_item = QTableWidgetItem(status)
            if status == "COMPLETED":
                status_item.setForeground(QColor("#10b981"))
                font = status_item.font()
                font.setBold(True)
                status_item.setFont(font)
            elif status == "IN_PROGRESS":
                status_item.setForeground(QColor("#f59e0b"))
                font = status_item.font()
                font.setBold(True)
                status_item.setFont(font)
            else:
                status_item.setForeground(QColor("#cbd5e1"))
            self.tbl_tasks.setItem(row_idx, 4, status_item)

    def on_task_selected(self):
        selected_rows = self.tbl_tasks.selectedItems()
        if not selected_rows: return
        row = selected_rows[0].row()
        self.selected_task_id = int(self.tbl_tasks.item(row, 0).text())
        desc = self.tbl_tasks.item(row, 1).text()
        sku = self.tbl_tasks.item(row, 2).text()
        qty = self.tbl_tasks.item(row, 3).text()
        status = self.tbl_tasks.item(row, 4).text()

        self.lbl_tsd_task_desc.setText(
            f"<b>Задача #{self.selected_task_id}:</b> {desc} (SKU: {sku}, Кол-во: {qty} шт.) [Статус: {status}]")
        self.task_scanned = False

        if status == "PENDING":
            self.btn_take_task.setEnabled(True)
            self.btn_scan_task.setEnabled(False)
            self.btn_exec_task.setEnabled(False)
        elif status == "IN_PROGRESS":
            self.btn_take_task.setEnabled(False)
            self.btn_scan_task.setEnabled(True)
            self.btn_exec_task.setEnabled(False)
        else:
            self.btn_take_task.setEnabled(False)
            self.btn_scan_task.setEnabled(False)
            self.btn_exec_task.setEnabled(False)

    def take_task_in_hand(self):
        if not self.selected_task_id: return
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", ('IN_PROGRESS', self.selected_task_id))
        conn.commit()
        conn.close()
        self.log_event(f"ТСД: Кладовщик принял в работу задачу #{self.selected_task_id}.")
        self.refresh_tasks_table()

    def scan_pick_barcode(self):
        if not self.selected_task_id: return
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT target_sku, target_qty FROM tasks WHERE id = ?", (self.selected_task_id,))
        sku, qty = cursor.fetchone()
        conn.close()

        self.task_scanned = True
        self.btn_exec_task.setEnabled(True)
        self.btn_scan_task.setEnabled(False)
        QMessageBox.information(self.main_win, "Успешное сканирование",
                                f"Штрихкод товара SKU {sku} отсканирован ТСД! Найдена ячейка. Товар укомплектован.")
        self.log_event(f"ТСД: Сканирование SKU {sku} выполнено. Сборщик подтвердил физическое наличие товара.")

    def execute_task_completed(self):
        if not self.selected_task_id or not self.task_scanned: return
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT target_sku, target_qty FROM tasks WHERE id = ?", (self.selected_task_id,))
        sku, qty = cursor.fetchone()
        cursor.execute("SELECT name FROM products WHERE sku = ?", (sku,))
        name = cursor.fetchone()[0]

        cursor.execute("UPDATE products SET qty = qty - ? WHERE sku = ?", (qty, sku))
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", ('COMPLETED', self.selected_task_id))

        ship_doc = f"TSD-SHIP-{datetime.now().strftime('%M%S')}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO documents (doc_type, timestamp, content) VALUES (?, ?, ?)", ('SHIPPING', now,
                                                                                                 f"Отгрузка через ТСД. Оформлена накладная {ship_doc}. Товар SKU: {sku}, списано: {qty} шт."))

        conn.commit()
        conn.close()

        QMessageBox.information(self.main_win, "Успех",
                                f"Задание #{self.selected_task_id} выполнено! Товар упакован, отгружен, остатки скорректированы.")
        self.log_event(
            f"ТСД: Задача #{self.selected_task_id} успешно ЗАКРЫТА сборщиком. Оформлена накладная {ship_doc}.")

        self.selected_task_id = None
        self.task_scanned = False
        self.refresh_all_data()

    # ================= 6. ОТЧЕТНОСТЬ =================
    def init_reports_page(self):
        self.cmb_report_type = self.reports_page.findChild(QComboBox, "cmbReportType")
        self.btn_export_report = self.reports_page.findChild(QPushButton, "btnExport")
        self.tbl_report = self.reports_page.findChild(QTableWidget, "tblReport")
        self.lbl_report_summary = self.reports_page.findChild(QLabel, "lblReportSummary")

        self.cmb_report_type.addItem("Остатки на складе (Текущий запас)", "STOCK")
        self.cmb_report_type.addItem("Журнал складских документов (Логи WMS)", "DOCS")
        self.cmb_report_type.addItem("Анализ заблокированной продукции (Брак)", "BLOCKED")

        self.cmb_report_type.currentIndexChanged.connect(self.on_report_type_changed)
        self.btn_export_report.clicked.connect(self.export_report_to_file)

    def on_report_type_changed(self):
        report_type = self.cmb_report_type.currentData()
        if not report_type: return
        self.tbl_report.setRowCount(0)

        conn = db_manager.get_connection()
        cursor = conn.cursor()

        if report_type == "STOCK":
            self.tbl_report.setColumnCount(5)
            self.tbl_report.setHorizontalHeaderLabels(
                ["Артикул (SKU)", "Название номенклатуры", "Количество", "Партия", "Статус качества"])
            self.tbl_report.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            cursor.execute("SELECT sku, name, qty, lot_number, quality_status FROM products")
            rows = cursor.fetchall()
            total_qty = 0
            for sku, name, qty, lot, status in rows:
                row_idx = self.tbl_report.rowCount()
                self.tbl_report.insertRow(row_idx)
                self.tbl_report.setItem(row_idx, 0, QTableWidgetItem(sku))
                self.tbl_report.setItem(row_idx, 1, QTableWidgetItem(name))
                self.tbl_report.setItem(row_idx, 2, QTableWidgetItem(str(qty)))
                self.tbl_report.setItem(row_idx, 3, QTableWidgetItem(lot))

                status_item = QTableWidgetItem(status)
                if status == "APPROVED":
                    status_item.setForeground(QColor("#10b981"))
                    font = status_item.font()
                    font.setBold(True)
                    status_item.setFont(font)
                elif status == "BLOCKED":
                    status_item.setForeground(QColor("#ef4444"))
                    font = status_item.font()
                    font.setBold(True)
                    status_item.setFont(font)
                else:
                    status_item.setForeground(QColor("#f59e0b"))
                    font = status_item.font()
                    font.setBold(True)
                    status_item.setFont(font)
                self.tbl_report.setItem(row_idx, 4, status_item)
                total_qty += qty
            self.lbl_report_summary.setText(
                f"Общее количество товаров на складе: <b>{total_qty} шт.</b> в {len(rows)} партиях.")

        elif report_type == "DOCS":
            self.tbl_report.setColumnCount(3)
            self.tbl_report.setHorizontalHeaderLabels(["Время создания", "Тип документа", "Содержание документа"])
            self.tbl_report.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.tbl_report.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.tbl_report.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            cursor.execute("SELECT timestamp, doc_type, content FROM documents WHERE doc_type != ? ORDER BY id DESC",
                           ('LOG',))
            rows = cursor.fetchall()
            for ts, dtype, content in rows:
                row_idx = self.tbl_report.rowCount()
                self.tbl_report.insertRow(row_idx)
                self.tbl_report.setItem(row_idx, 0, QTableWidgetItem(ts))
                self.tbl_report.setItem(row_idx, 1, QTableWidgetItem(dtype))
                self.tbl_report.setItem(row_idx, 2, QTableWidgetItem(content))
            self.lbl_report_summary.setText(f"Всего создано складских документов: <b>{len(rows)} шт.</b>")

        elif report_type == "BLOCKED":
            self.tbl_report.setColumnCount(4)
            self.tbl_report.setHorizontalHeaderLabels(["Артикул (SKU)", "Название брака", "Количество", "Партия брака"])
            self.tbl_report.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            cursor.execute("SELECT sku, name, qty, lot_number FROM products WHERE quality_status = ?", ('BLOCKED',))
            rows = cursor.fetchall()
            total_blocked = 0
            for sku, name, qty, lot in rows:
                row_idx = self.tbl_report.rowCount()
                self.tbl_report.insertRow(row_idx)
                self.tbl_report.setItem(row_idx, 0, QTableWidgetItem(sku))
                self.tbl_report.setItem(row_idx, 1, QTableWidgetItem(name))
                self.tbl_report.setItem(row_idx, 2, QTableWidgetItem(str(qty)))
                self.tbl_report.setItem(row_idx, 3, QTableWidgetItem(lot))
                total_blocked += qty
            self.lbl_report_summary.setText(
                f"Общий объем бракованной/блокированной продукции: <font color='#ef4444'><b>{total_blocked} шт.</b></font>")

        conn.close()

    def export_report_to_file(self):
        report_type = self.cmb_report_type.currentData()
        if not report_type: return
        filename = f"report_{report_type.lower()}_{datetime.now().strftime('%d%H%M')}.txt"
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("===================================================\n")
                f.write(f"ОТЧЕТ СИСТЕМЫ WMS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("===================================================\n\n")

                if report_type == "STOCK":
                    cursor.execute("SELECT sku, name, qty, lot_number, quality_status, location FROM products")
                    rows = cursor.fetchall()
                    f.write(
                        f"{'SKU':<8} | {'Наименование':<32} | {'Кол-во':<6} | {'Партия':<14} | {'Статус':<10} | {'Ячейка':<6}\n")
                    f.write("-" * 85 + "\n")
                    for sku, name, qty, lot, status, loc in rows:
                        f.write(f"{sku:<8} | {name[:30]:<32} | {qty:<6} | {lot:<14} | {status:<10} | {loc:<6}\n")
                elif report_type == "DOCS":
                    cursor.execute(
                        "SELECT timestamp, doc_type, content FROM documents WHERE doc_type != ? ORDER BY id DESC",
                        ('LOG',))
                    rows = cursor.fetchall()
                    for ts, dtype, content in rows:
                        f.write(f"[{ts}] {dtype:<10} | {content}\n")
                elif report_type == "BLOCKED":
                    cursor.execute("SELECT sku, name, qty, lot_number, location FROM products WHERE quality_status = ?",
                                   ('BLOCKED',))
                    rows = cursor.fetchall()
                    f.write(f"{'SKU':<8} | {'Название брака':<32} | {'Кол-во':<6} | {'Партия':<14} | {'Ячейка':<6}\n")
                    f.write("-" * 75 + "\n")
                    for sku, name, qty, lot, loc in rows:
                        f.write(f"{sku:<8} | {name[:30]:<32} | {qty:<6} | {lot:<14} | {loc:<6}\n")

            QMessageBox.information(self.main_win, "Успех", f"Отчет успешно сохранен в файл: {filename}")
            self.log_event(f"Отчетность: Выгружен текстовый отчет в файл {filename}")
        except Exception as e:
            QMessageBox.critical(self.main_win, "Ошибка экспорта", f"Не удалось экспортировать отчет:\n{str(e)}")
        conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    wms = WMSApp()
    sys.exit(app.exec())