import logging
import colorama
from logging.handlers import RotatingFileHandler


class _ColoredFormatter(logging.Formatter):
	MAX_LENGTH = 115
	COLORS = {
		logging.DEBUG: colorama.Fore.CYAN,
		logging.INFO: colorama.Fore.GREEN,
		logging.WARNING: colorama.Fore.YELLOW,
		logging.ERROR: colorama.Fore.RED,
		logging.CRITICAL: colorama.Fore.RED + colorama.Style.BRIGHT,
	}

	def format(self, record: logging.LogRecord) -> str:
		message = super().format(record)
		if len(message) > self.MAX_LENGTH:
			message = message[: self.MAX_LENGTH - 3] + "..."
		color = self.COLORS.get(record.levelno, "")
		return f"{color}{message}{colorama.Style.RESET_ALL}"


class UtilscordStreamLogger(logging.Logger):
	def __init__(self, name: str, level: int = logging.INFO) -> None:
		super().__init__(name, level)
		configure_logging(self)

class UtilscordRotatingFileLogger(logging.Logger):
	def __init__(self, name: str, level: int = logging.INFO, filename: str = "utilscord.log", max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> None:
		super().__init__(name, level)
		self.addHandler(_RotatingFileHandler(filename, max_bytes, backup_count))


def configure_logging(
	logger: logging.Logger | None = None,
	filename: str = "utilscord.log",
	max_bytes: int = 10 * 1024 * 1024,
	backup_count: int = 5,
) -> logging.Logger:
	"""Configure the application logger and return it."""
	logger = logger or logging.getLogger()
	logger.setLevel(logging.INFO)

	if not any(isinstance(handler, _UtilscordHandler) for handler in logger.handlers):
		logger.addHandler(_UtilscordHandler())
	if not any(isinstance(handler, _RotatingFileHandler) for handler in logger.handlers):
		logger.addHandler(_RotatingFileHandler(filename, max_bytes, backup_count))

	return logger


class _UtilscordHandler(logging.StreamHandler):
	def __init__(self) -> None:
		super().__init__()
		self.setFormatter(_ColoredFormatter("%(asctime)s | %(levelname)s | %(name)s (%(processName)s) | %(message)s"))


class _RotatingFileHandler(RotatingFileHandler):
	def __init__(self, filename: str, max_bytes: int, backup_count: int) -> None:
		super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count)
		self.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s (%(processName)s) | %(message)s"))
