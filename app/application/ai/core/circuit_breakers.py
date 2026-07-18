import time
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Small provider health gate used by AI adapters.

    CLOSED allows calls. After enough failures it moves to OPEN and blocks
    requests until recovery_timeout elapses. The next allowed call becomes a
    HALF_OPEN probe; success closes the circuit, failure opens it again.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failures = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED

    def allow_request(self) -> bool:

        if self.state == CircuitState.OPEN:
            elapsed = time.time() - self.last_failure_time

            if elapsed > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True

            return False

        return True

    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
