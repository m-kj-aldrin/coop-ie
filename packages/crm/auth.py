from typing import Any
from playwright.async_api import async_playwright, TimeoutError
import json
import os
import time
from app.constants import USER_AGENT
from packages.crm.models import User, Cookie
from app.logger import logger


class Authenticate:
    _cookies: dict[str, Cookie] = {}
    _user: User | None = None
    _cookie_file_path: str = os.path.join(
        os.getcwd(), "app", "data", "cookies.json")
    _login_url: str
    _redirect_url: str

    def __init__(self, login_url: str, redirect_url: str):
        self._login_url = login_url
        self._redirect_url = redirect_url
        _ = self.load_cookies()

    async def login(self, user: User | None = None):
        """
        Authenticates the user using Playwright to automate browser actions.

        Args:
            user (User | None): The user credentials. If None, uses the existing user.

        Raises:
            ValueError: If no user is provided for authentication.
            Exception: For various authentication failures.
        """
        logger.debug("Starting login process")

        if self.is_authenticated:
            logger.debug("User already authenticated")
            return self

        _user = user or self._user
        if _user is None:
            logger.error("No user provided for authentication")
            raise ValueError("User must be provided")

        self._user = _user
        logger.debug(f"Attempting login for user: {_user.username}")

        async with async_playwright() as playwright:
            try:
                logger.debug("Launching browser")

                browser = await playwright.chromium.launch(
                    headless=True,
                    channel="chrome",
                    args=[
                        "--start-maximized",
                        "--disable-infobars",
                        "--disable-extensions",
                    ],
                )
            except TimeoutError:
                logger.error("Browser launch timed out")
                return self
            except Exception as e:
                logger.error(f"Failed to launch browser: {str(e)}")
                return self

            logger.debug("Creating new browser context")
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                logger.debug(f"Navigating to login URL: {self._login_url}")
                _ = await page.goto(self._login_url, timeout=60000)

                logger.debug("Waiting for username input")
                user_name_element = await page.wait_for_selector(
                    "input[name='loginfmt']"
                )

                if not user_name_element:
                    logger.error("Failed to find username input element")
                    raise Exception("Failed to find username input element")

                _ = await user_name_element.fill(_user.username)
                _ = await user_name_element.press("Enter")
                logger.debug("Username entered successfully")

                logger.debug("Waiting for password input")
                password_element = await page.wait_for_selector(
                    "input[name='passwd']", timeout=20000
                )

                if not password_element:
                    logger.error("Failed to find password input element")
                    raise Exception("Failed to find password input element")

                _ = await password_element.fill(_user.password)
                _ = await password_element.press("Enter")
                logger.debug("Password entered successfully")

                logger.debug("Waiting for phone authentication")
                phone_auth_element = await page.wait_for_selector(
                    "[data-value='PhoneAppNotification']", timeout=60000
                )

                if not phone_auth_element:
                    logger.error("Failed to find phone authentication element")
                    raise Exception(
                        "Failed to find phone authentication element")

                _ = await phone_auth_element.click()

                logger.debug("Waiting for authentication number")
                auth_number_element = await page.wait_for_selector(
                    ".display-sign-container", timeout=60000
                )

                if not auth_number_element:
                    logger.error(
                        "Failed to find authentication number element")
                    raise Exception(
                        "Failed to find authentication number element")

                auth_number = await auth_number_element.text_content()

                if not auth_number:
                    logger.error("Failed to get authentication number")
                    raise Exception("Failed to get authentication number")

                auth_number = auth_number.replace(" ", "").replace("\n", "")

                logger.debug(f"Authentication number received: {auth_number}")

                print(
                    (
                        f"\n{"=" * 50}"
                        f"\nAUTHENTICATION NUMBER: {auth_number}"
                        f"\nPlease enter this number in your phone app"
                        f"\n{"=" * 50}"
                    )
                )

                logger.debug("Waiting for stay signed in option")
                stay_signed_in_element = await page.wait_for_selector(
                    "input[type='submit']"
                )

                if not stay_signed_in_element:
                    logger.error("Failed to find stay signed in element")
                    raise Exception("Failed to find stay signed in element")

                await stay_signed_in_element.click()

                logger.debug("Waiting for redirect to main page")
                await page.wait_for_url(
                    "https://coopcrmprod.crm4.dynamics.com/main.aspx?forceUCI=1&pagetype=apps",
                    timeout=60000,
                )

                cookies_to_grab = [
                    "orgId",
                    "ReqClientId",
                    "CrmOwinAuth",
                    "ARRAffinity",
                ]

                logger.debug(f"Getting cookies: {', '.join(cookies_to_grab)}")

                grabbed_cookies = {
                    c.get("name", ""): Cookie(
                        name=c.get("name", ""),
                        value=c.get("value", ""),
                        expires=c.get("expires"),
                        domain=c.get("domain"),
                        path=c.get("path"),
                    )
                    for c in await context.cookies(self._login_url)
                    if c.get("name") in cookies_to_grab
                }

                self._cookies = grabbed_cookies

                if not self.cookies:
                    logger.error(
                        "No cookies were captured after authentication")
                    return self

                logger.info("Authentication completed successfully")
                logger.debug(f"Captured {len(self._cookies)} cookies")

            except TimeoutError as e:
                logger.error(
                    f"Timeout during authentication process: {str(e)}")
                return self
            except Exception as e:
                logger.error(
                    f"Unexpected error during authentication: {str(e)}")
                return self
            finally:
                logger.debug("Closing browser")
                await browser.close()
                self.save_cookies()
                return self

    def logout(self):
        self._user = None
        self._cookies = {}
        return self

    def cookies_as_tuples(self):
        return [(c.name, c.value) for c in self._cookies.values()]

    def save_cookies(self):
        """
        Save current cookies to the cookies file.
        """
        with open(self._cookie_file_path, "w") as f:
            json.dump(
                {c.name: c.to_json() for c in self._cookies.values()},
                f,
                indent=4,
            )

    def load_cookies(self):
        """
        Load cookies from the cookies file.
        """
        if os.path.exists(self._cookie_file_path):
            with open(self._cookie_file_path, "r") as f:
                data: dict[str, Any] = json.load(f)
                self._cookies = {c: Cookie.from_json(data[c]) for c in data}
        return self

    @property
    def cookies(self):
        return self._cookies

    @property
    def is_authenticated(self) -> bool:
        """
        Check if we have valid authentication.
        Includes a 5-minute buffer before expiration to prevent edge cases.
        """
        if not self.cookies:
            logger.debug("No cookies found, attempting to load from file")
            _ = self.load_cookies()

        auth_cookie = self.cookies.get("CrmOwinAuth")
        if not auth_cookie or not auth_cookie.expires:
            logger.debug("No valid auth cookie found")
            return False

        buffer_time = 300
        current_time = time.time()

        if auth_cookie.expires - current_time <= buffer_time:
            logger.debug("Auth cookie is expired or will expire soon")
            return False

        return True
