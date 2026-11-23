"""
Layer between frontend and backend api
"""
import requests


class ApiError(Exception):
	"""Any problem talking to the API (server down, validation error, ...)."""


class AuthError(ApiError):
	"""Wrong credentials or the login token has expired."""


class ApiClient:
	def __init__(self, base_url: str, timeout: float = 5.0):
		self.base_url = base_url.rstrip("/")
		self.timeout = timeout
		self.session = requests.Session()
		self.username: str | None = None

	# ---- auth -------------------------------------------------------------
	def login(self, username: str, password: str) -> None:
		data = self._request(
			"POST", "/auth/login", data={"username": username, "password": password}
		)
		self.session.headers["Authorization"] = f"Bearer {data['access_token']}"
		self.username = username

	def logout(self) -> None:
		self.session.headers.pop("Authorization", None)
		self.username = None

	#  items
	def list_items(self) -> list[dict]:
		return self._request("GET", "/items")

	def add_item(self, name: str, description: str) -> dict:
		return self._request("POST", "/items", json={"name": name, "description": description})

	#  internals
	def _request(self, method: str, path: str, **kwargs):
		try:
			response = self.session.request(
				method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs
			)
		except requests.ConnectionError:
			raise ApiError(f"Cannot reach the server at {self.base_url}. Is it running?")
		except requests.Timeout:
			raise ApiError("The server took too long to respond.")

		if response.status_code == 401:
			raise AuthError(self._error_message(response))
		if not response.ok:
			raise ApiError(self._error_message(response))
		return response.json()

	@staticmethod
	def _error_message(response: requests.Response) -> str:
		try:
			detail = response.json().get("detail")
		except ValueError:
			detail = None
		if isinstance(detail, list):  # FastAPI validation errors are a list
			return "; ".join(err.get("msg", "") for err in detail)
		return detail or f"Server error ({response.status_code})"
