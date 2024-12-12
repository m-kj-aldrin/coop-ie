from playwright.async_api import async_playwright, TimeoutError
import json
import os
import time
import logging
from packages.crm.protocols import User, Cookie

# Configure logging
logger = logging.getLogger(__name__)

# from playwright.sync_api import sync_playwright, TimeoutError


class Authenticate:
    _cookies: dict[str, Cookie] = {}
    _user: User | None = None
    _cookie_file_path: str = os.path.join(os.getcwd(), "app", "data", "cookies.json")
    _login_url: str
    _redirect_url: str

    def __init__(self, login_url: str, redirect_url: str):
        self._login_url = login_url
        self._redirect_url = redirect_url
        self.load_cookies()

    async def login(self, user: User | None = None):
        logger.debug("Starting login process")
        
        if self.is_authenticated:
            logger.info("User already authenticated")
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
            context = await browser.new_context()
            page = await context.new_page()
            
            # Debug user agent
            actual_user_agent = await page.evaluate("() => navigator.userAgent")
            logger.info(f"Current User Agent: {actual_user_agent}")

            try:
                logger.debug(f"Navigating to login URL: {self._login_url}")
                _ = await page.goto(
                    self._login_url, timeout=60000
                )

                logger.debug("Waiting for username input")
                _ = await page.wait_for_selector(
                    "input[name='loginfmt']", timeout=20000
                )
                _ = await page.fill("input[name='loginfmt']", _user.username)
                _ = await page.press("input[name='loginfmt']", "Enter")
                logger.debug("Username entered successfully")

                logger.debug("Waiting for password input")
                _ = await page.wait_for_selector("input[name='passwd']", timeout=20000)
                _ = await page.fill("input[name='passwd']", _user.password)
                _ = await page.click("input[type='submit']")
                logger.debug("Password entered successfully")

                logger.debug("Waiting for phone authentication")
                phone_auth_selector = "[data-value='PhoneAppNotification']"
                _ = await page.wait_for_selector(phone_auth_selector, timeout=60000)
                _ = await page.click(phone_auth_selector)

                logger.debug("Waiting for authentication number")
                auth_number_selector = ".display-sign-container"
                _ = await page.wait_for_selector(auth_number_selector, timeout=60000)
                auth_number_element = await page.text_content(
                    auth_number_selector, timeout=60000
                )

                if not auth_number_element:
                    logger.error("Failed to get authentication number")
                    return self

                auth_number = auth_number_element.replace(" ", "").replace("\n", "")
                logger.info(f"Authentication number received: {auth_number}")

                print("\n" + "=" * 50)
                print(f"AUTHENTICATION NUMBER: {auth_number}")
                print("Please enter this number in your phone app")
                print("=" * 50 + "\n")

                logger.debug("Waiting for stay signed in option")
                stay_signed_in_selector = "input[type='submit']"
                _ = await page.wait_for_selector(stay_signed_in_selector, timeout=60000)
                await page.click(stay_signed_in_selector)

                logger.debug("Waiting for redirect to main page")
                await page.wait_for_url(
                    "https://coopcrmprod.crm4.dynamics.com/main.aspx?forceUCI=1&pagetype=apps",
                    timeout=60000,
                )

                logger.debug("Getting cookies")
                cookies_to_grab = [
                    "orgId",
                    "ReqClientId",
                    "CrmOwinAuth",
                    "ARRAffinity",
                ]
                cookies_list = [
                    c
                    for c in await context.cookies(self._login_url)
                    if c.get("name") and c.get("value")
                ] or []

                self._cookies = {
                    c.get("name"): Cookie(
                        name=c.get("name"),
                        value=c.get("value"),
                        expires=c.get("expires"),
                        domain=c.get("domain"),
                        path=c.get("path"),
                    )
                    for c in cookies_list
                    if c.get("name") in cookies_to_grab
                }

                if not self.cookies:
                    logger.error("No cookies were captured after authentication")
                    return self
                    
                logger.info("Authentication completed successfully")
                logger.debug(f"Captured {len(self._cookies)} cookies")

            except TimeoutError as e:
                logger.error(f"Timeout during authentication process: {str(e)}")
                return self
            except Exception as e:
                logger.error(f"Unexpected error during authentication: {str(e)}")
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
                data = json.load(f)
                self._cookies = {c: Cookie.from_json(data[c]) for c in data}
        return self

    @property
    def cookies(self):
        return self._cookies

    @property
    def is_authenticated(self):
        if not self.cookies:
            print("There is no cookies, try to load cookies")
            _ = self.load_cookies()

        auth_cookie = self.cookies.get("CrmOwinAuth")

        # print(f"Cookies: {self.cookies}")

        # print(f"Auth cookie: {auth_cookie}")

        if not auth_cookie:
            return False

        expires = auth_cookie.expires

        if not expires:
            return False

        current_time = time.time()

        if expires < current_time:
            print("Auth cookie is expired")
            return False

        # print("Auth cookie is valid")

        return True
