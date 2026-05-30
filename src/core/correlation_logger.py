import logging


class CorrelationLogger:
    """Logger wrapper that prepends [cid: <correlation_id>] to messages."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _fmt(self, msg: str, cid: str | None = None) -> str:
        if cid:
            return f"[cid: {cid}] {msg}"
        return msg

    def info(self, msg: str, cid: str | None = None) -> None:
        self.logger.info(self._fmt(msg, cid))

    def error(self, msg: str, cid: str | None = None) -> None:
        self.logger.error(self._fmt(msg, cid))

    def warning(self, msg: str, cid: str | None = None) -> None:
        self.logger.warning(self._fmt(msg, cid))

    def exception(self, msg: str, cid: str | None = None) -> None:
        self.logger.exception(self._fmt(msg, cid))
