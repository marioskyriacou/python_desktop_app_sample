"""PySide6 desktop UI. Run with:  python -m frontend.main"""
import os
import sys
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
	QApplication,
	QFormLayout,
	QHBoxLayout,
	QHeaderView,
	QLabel,
	QLineEdit,
	QMainWindow,
	QMessageBox,
	QPushButton,
	QStackedWidget,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)

from frontend.client_api import ApiClient, ApiError, AuthError

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


class LoginPage(QWidget):
	logged_in = Signal()

	def __init__(self, client: ApiClient):
		super().__init__()
		self.client = client

		title = QLabel("Sign in")
		title.setStyleSheet("font-size: 20px; font-weight: 600;")

		self.username = QLineEdit(placeholderText="Username")
		self.password = QLineEdit(placeholderText="Password")
		self.password.setEchoMode(QLineEdit.EchoMode.Password)
		self.password.returnPressed.connect(self.login)

		self.error = QLabel()
		self.error.setStyleSheet("color: #c0392b;")
		self.error.setWordWrap(True)
		self.error.hide()

		self.login_button = QPushButton("Log in")
		self.login_button.setDefault(True)
		self.login_button.clicked.connect(self.login)

		box = QWidget()
		box.setFixedWidth(280)
		form = QVBoxLayout(box)
		for w in (title, self.username, self.password, self.error, self.login_button):
			form.addWidget(w)

		outer = QVBoxLayout(self)
		outer.addWidget(box, alignment=Qt.AlignmentFlag.AlignCenter)

	def login(self) -> None:
		username = self.username.text().strip()
		password = self.password.text()
		if not username or not password:
			self._show_error("Enter your username and password.")
			return

		self.login_button.setEnabled(False)
		try:
			self.client.login(username, password)
		except ApiError as exc:
			self._show_error(str(exc))
			return
		finally:
			self.login_button.setEnabled(True)

		self.password.clear()
		self.error.hide()
		self.logged_in.emit()

	def _show_error(self, message: str) -> None:
		self.error.setText(message)
		self.error.show()


class ItemsPage(QWidget):
	logged_out = Signal()

	def __init__(self, client: ApiClient):
		super().__init__()
		self.client = client

		# Header: who is logged in + logout
		self.user_label = QLabel()
		logout_button = QPushButton("Log out")
		logout_button.clicked.connect(self.logged_out.emit)
		header = QHBoxLayout()
		header.addWidget(self.user_label)
		header.addStretch()
		header.addWidget(logout_button)

		# Form to add a new item
		self.name = QLineEdit(placeholderText="Required")
		self.description = QLineEdit(placeholderText="Optional")
		self.description.returnPressed.connect(self.add_item)
		add_button = QPushButton("Add")
		add_button.clicked.connect(self.add_item)
		form = QFormLayout()
		form.addRow("Name", self.name)
		form.addRow("Description", self.description)
		form.addRow("", add_button)

		# Table with the saved items
		self.table = QTableWidget(0, 3)
		self.table.setHorizontalHeaderLabels(["Name", "Description", "Created"])
		self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.table.verticalHeader().hide()
		self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

		layout = QVBoxLayout(self)
		layout.addLayout(header)
		layout.addLayout(form)
		layout.addWidget(self.table)

	def load(self) -> None:
		self.user_label.setText(f"Logged in as <b>{self.client.username}</b>")
		try:
			items = self.client.list_items()
		except ApiError as exc:
			self._handle_error(exc)
			return

		self.table.setRowCount(len(items))
		for row, item in enumerate(items):
			created = datetime.fromisoformat(item["created_at"]).astimezone()
			values = (item["name"], item["description"], created.strftime("%d/%m/%Y %H:%M"))
			for col, value in enumerate(values):
				self.table.setItem(row, col, QTableWidgetItem(value))
		self.table.resizeColumnToContents(0)
		self.table.resizeColumnToContents(2)

	def add_item(self) -> None:
		name = self.name.text().strip()
		if not name:
			QMessageBox.warning(self, "Missing name", "Please enter a name.")
			self.name.setFocus()
			return
		try:
			self.client.add_item(name, self.description.text().strip())
		except ApiError as exc:
			self._handle_error(exc)
			return

		self.name.clear()
		self.description.clear()
		self.name.setFocus()
		self.load()

	def _handle_error(self, exc: ApiError) -> None:
		QMessageBox.warning(self, "Error", str(exc))
		if isinstance(exc, AuthError):  # token expired -> back to login
			self.logged_out.emit()


class MainWindow(QMainWindow):
	def __init__(self, client: ApiClient):
		super().__init__()
		self.client = client
		self.setWindowTitle("Desktop App")
		self.resize(720, 480)

		self.login_page = LoginPage(client)
		self.items_page = ItemsPage(client)
		self.login_page.logged_in.connect(self.show_items)
		self.items_page.logged_out.connect(self.show_login)

		self.pages = QStackedWidget()
		self.pages.addWidget(self.login_page)
		self.pages.addWidget(self.items_page)
		self.setCentralWidget(self.pages)

	def show_items(self) -> None:
		self.items_page.load()
		self.pages.setCurrentWidget(self.items_page)
		self.items_page.name.setFocus()

	def show_login(self) -> None:
		self.client.logout()
		self.pages.setCurrentWidget(self.login_page)
		self.login_page.password.setFocus()


def main() -> None:
	app = QApplication(sys.argv)
	window = MainWindow(ApiClient(API_URL))
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
