"""
Betfair authentication and session management module.

This module provides thread-safe session management for the Betfair API,
handling login, logout, and session keep-alive automatically.
"""

import logging
import os
from threading import Lock
from typing import Optional

import betfairlightweight
from betfairlightweight import APIClient
from betfairlightweight.exceptions import BetfairError

logger = logging.getLogger(__name__)


class BetfairSessionManager:
    """
    Thread-safe session manager for Betfair API.

    Handles authentication, session lifecycle, and automatic keep-alive.
    Supports both password-based and certificate-based authentication.
    """

    def __init__(
        self,
        username: str,
        password: str,
        app_key: str,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
    ):
        """
        Initialize the Betfair session manager.

        Args:
            username: Betfair account username
            password: Betfair account password
            app_key: Betfair application key
            cert_file: Optional path to SSL certificate file
            key_file: Optional path to SSL key file
        """
        self.username = username
        self.password = password
        self.app_key = app_key
        self.cert_file = cert_file
        self.key_file = key_file

        # Thread safety
        self.lock = Lock()
        self.session_active = False

        # Initialize API client
        self.client: Optional[APIClient] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the betfairlightweight API client."""
        certs_path = None
        if self.cert_file and self.key_file:
            if os.path.exists(self.cert_file) and os.path.exists(self.key_file):
                certs_path = (self.cert_file, self.key_file)
                logger.info("Certificate authentication enabled")
            else:
                logger.warning(
                    "Certificate files not found, falling back to password authentication"
                )

        self.client = betfairlightweight.APIClient(
            username=self.username,
            password=self.password,
            app_key=self.app_key,
            certs=certs_path,
        )
        logger.info("Betfair API client initialized")

    def ensure_logged_in(self) -> None:
        """
        Ensure the session is active, logging in if necessary.

        This method is thread-safe and can be called before any API operation.

        Raises:
            BetfairError: If login fails
        """
        with self.lock:
            if not self.session_active:
                self._login()

    def _login(self) -> None:
        """
        Internal login method (must be called with lock held).

        Raises:
            BetfairError: If login fails
        """
        try:
            logger.info(f"Logging in to Betfair as {self.username}")
            self.client.login()
            self.session_active = True
            logger.info("Successfully logged in to Betfair")
        except BetfairError as e:
            logger.error(f"Betfair login failed: {e}")
            self.session_active = False
            raise

    def keep_alive(self) -> bool:
        """
        Send a keep-alive request to maintain the session.

        Should be called periodically (e.g., every 30 minutes) to prevent
        session timeout.

        Returns:
            bool: True if keep-alive successful, False otherwise
        """
        with self.lock:
            if not self.session_active:
                logger.warning("Cannot send keep-alive: session not active")
                return False

            try:
                logger.debug("Sending session keep-alive")
                self.client.keep_alive()
                logger.debug("Keep-alive successful")
                return True
            except BetfairError as e:
                logger.error(f"Keep-alive failed: {e}")
                self.session_active = False
                return False

    def logout(self) -> None:
        """
        Logout from Betfair and end the session.

        This should be called when shutting down the server.
        """
        with self.lock:
            if self.session_active:
                try:
                    logger.info("Logging out from Betfair")
                    self.client.logout()
                    self.session_active = False
                    logger.info("Successfully logged out")
                except BetfairError as e:
                    logger.error(f"Logout failed: {e}")
                    self.session_active = False

    def get_client(self) -> APIClient:
        """
        Get the authenticated API client.

        Returns:
            APIClient: The betfairlightweight API client

        Raises:
            RuntimeError: If client is not initialized
        """
        if self.client is None:
            raise RuntimeError("API client not initialized")
        return self.client

    @property
    def is_active(self) -> bool:
        """Check if the session is currently active."""
        with self.lock:
            return self.session_active


def create_session_manager_from_env() -> BetfairSessionManager:
    """
    Create a BetfairSessionManager from environment variables.

    Required environment variables:
        - BETFAIR_USERNAME
        - BETFAIR_PASSWORD
        - BETFAIR_APP_KEY

    Optional environment variables:
        - BETFAIR_CERT_FILE
        - BETFAIR_KEY_FILE

    Returns:
        BetfairSessionManager: Configured session manager

    Raises:
        ValueError: If required environment variables are missing
    """
    username = os.getenv("BETFAIR_USERNAME")
    password = os.getenv("BETFAIR_PASSWORD")
    app_key = os.getenv("BETFAIR_APP_KEY")

    if not username or not password or not app_key:
        raise ValueError(
            "Missing required environment variables: "
            "BETFAIR_USERNAME, BETFAIR_PASSWORD, BETFAIR_APP_KEY"
        )

    cert_file = os.getenv("BETFAIR_CERT_FILE")
    key_file = os.getenv("BETFAIR_KEY_FILE")

    return BetfairSessionManager(
        username=username,
        password=password,
        app_key=app_key,
        cert_file=cert_file,
        key_file=key_file,
    )
