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
    _cookie_file_path: str = os.path.join(os.getcwd(), "app", "data", "cookies.json")
    _login_url: str
    _redirect_url: str

    def __init__(self, login_url: str, redirect_url: str):
        self._login_url = login_url
        self._redirect_url = redirect_url
        _ = self.load_cookies()

    async def _log_page_state(self, page, message):
        """Helper to log page state for debugging"""
        try:
            content = await page.content()
            url = page.url
            logger.debug(f"{message} - Current URL: {url}")
            logger.debug(f"Page content length: {len(content)}")
            # Save content to file for debugging
            with open(f"debug_page_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to log page state: {str(e)}")

    async def _debug_page_state(self, page, message):
        """Log detailed page state for debugging"""
        try:
            url = page.url
            logger.debug(f"{message} - Current URL: {url}")
            
            # Log all radio buttons on the page
            radios = await page.query_selector_all('input[type="radio"]')
            for radio in radios:
                label = await radio.evaluate('el => el.getAttribute("aria-label") || el.getAttribute("value") || el.id')
                logger.debug(f"Found radio button: {label}")
                
            # Log all clickable elements
            clickable = await page.query_selector_all('button, input[type="radio"], input[type="submit"]')
            for elem in clickable:
                text = await elem.evaluate('el => el.textContent || el.value || el.id')
                logger.debug(f"Found clickable element: {text}")
                
        except Exception as e:
            logger.error(f"Error in debug logging: {str(e)}")

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
                    headless=False,
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
                _ = await page.wait_for_function(
                    'window.location.href.startsWith("https://login.microsoftonline.com")',
                    timeout=60000,
                )

                # content = await page.content()
                # with open("login_content.html", "w") as f:
                #     f.write(content)

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

                # content = await page.content()
                # with open("login_content_2.html", "w") as f:
                #     f.write(content)

                logger.debug("Waiting for password input")
                password_element = await page.wait_for_selector(
                    "input[name='passwd']", timeout=20000
                )

                if not password_element:
                    logger.error("Failed to find password input element")
                    raise Exception("Failed to find password input element")

                # Fill in password
                await password_element.fill(_user.password)
                logger.debug("Password filled")

                # Small delay before pressing Enter
                await page.wait_for_timeout(1000)

                try:
                    # Re-get the password element to ensure it's still attached
                    password_element = await page.wait_for_selector(
                        "input[name='passwd']",
                        timeout=5000,
                        state="visible"
                    )
                    
                    if not password_element:
                        raise Exception("Password element not found before pressing Enter")
                        
                    # Try to press Enter on the element
                    await password_element.press("Enter")
                    logger.debug("Pressed Enter on password field")
                    
                except Exception as e:
                    logger.error(f"Failed to press Enter on password field: {str(e)}")
                    # Try alternative method - keyboard press
                    try:
                        await page.keyboard.press("Enter")
                        logger.debug("Pressed Enter using keyboard")
                    except Exception as e2:
                        logger.error(f"Failed to press Enter using keyboard: {str(e2)}")
                        raise

                # Wait for navigation/processing
                try:
                    # Wait for URL change or new elements
                    await page.wait_for_function(
                        """() => {
                            return document.querySelector('#idDiv_SAOTCS_Proofs') !== null || 
                                   document.querySelector('.error') !== null ||
                                   document.querySelector('#passwordError') !== null ||
                                   document.querySelector('[data-value="PhoneAppNotification"]') !== null ||
                                   document.querySelector('#idSIButton9') !== null
                        }""",
                        timeout=15000
                    )
                    
                    # Add a small delay to let any animations complete
                    await page.wait_for_timeout(2000)
                    
                    # Save the current page state for debugging
                    # content = await page.content()
                    # with open("after_password.html", "w", encoding="utf-8") as f:
                    #     f.write(content)
                    # await page.screenshot(path="after_password.png")
                    
                    logger.debug("Password page processed successfully")
                except Exception as e:
                    logger.error(f"Error after password submission: {str(e)}")
                    # Save the page state for debugging
                    # content = await page.content()
                    # with open("password_error.html", "w", encoding="utf-8") as f:
                    #     f.write(content)
                    # await page.screenshot(path="password_error.png")
                    raise

                logger.debug("Waiting for phone authentication")

                try:
                    # Add a longer delay after password entry to let the page fully load
                    await page.wait_for_timeout(5000)
                    
                    # Try to find any verification/authentication related elements
                    verification_selectors = [
                        "#idDiv_SAOTCS_Proofs",
                        "[data-bind*='phoneAppNotification']",
                        "[data-value='PhoneAppNotification']",
                        "input[aria-label*='Notification']",
                        "input[aria-label*='notification']",
                        "div[data-value*='Phone']",
                        "#idDiv_SAOTCC_Section",
                        "[role='radiogroup']"
                    ]
                    
                    # Log the current page state
                    # content = await page.content()
                    # with open("verification_page.html", "w", encoding="utf-8") as f:
                    #     f.write(content)
                    # await page.screenshot(path="verification_page.png")
                    
                    # Try each selector
                    phone_auth_element = None
                    for selector in verification_selectors:
                        try:
                            logger.debug(f"Trying to find element with selector: {selector}")
                            element = await page.wait_for_selector(selector, timeout=3000, state="visible")
                            if element:
                                # Check if this is a container or the actual element
                                if await element.evaluate('el => el.tagName === "DIV"'):
                                    # If it's a container, look for the phone option inside it
                                    possible_elements = await element.query_selector_all('input[type="radio"], div[role="button"], button')
                                    for possible in possible_elements:
                                        html = await possible.evaluate('el => el.outerHTML')
                                        logger.debug(f"Found possible element: {html}")
                                        if any(keyword in html.lower() for keyword in ['phone', 'notification', 'mobil']):
                                            phone_auth_element = possible
                                            break
                                else:
                                    phone_auth_element = element
                                
                                if phone_auth_element:
                                    logger.debug("Found phone authentication element")
                                    break
                        except Exception as e:
                            logger.debug(f"Selector {selector} failed: {str(e)}")
                            continue

                    if not phone_auth_element:
                        # Try an alternative approach - look for any clickable elements
                        logger.debug("Trying alternative approach to find authentication element")
                        elements = await page.query_selector_all('input[type="radio"], div[role="button"], button')
                        for element in elements:
                            try:
                                html = await element.evaluate('el => el.outerHTML')
                                text = await element.evaluate('el => el.textContent || el.value || el.getAttribute("aria-label") || ""')
                                logger.debug(f"Found element: {text} with HTML: {html}")
                                if any(keyword in (html + text).lower() for keyword in ['phone', 'notification', 'mobil', 'authenticator']):
                                    phone_auth_element = element
                                    logger.debug(f"Found authentication element with text: {text}")
                                    break
                            except Exception as e:
                                logger.debug(f"Error checking element: {str(e)}")
                                continue

                    if not phone_auth_element:
                        logger.error("Failed to find phone authentication element")
                        raise Exception("Failed to find phone authentication element")

                    # Add a delay before clicking
                    await page.wait_for_timeout(1000)
                    
                    # Try to click the element
                    try:
                        await phone_auth_element.click()
                        logger.debug("Successfully clicked phone authentication element")
                    except Exception as e:
                        logger.error(f"Failed to click element: {str(e)}")
                        # Try JavaScript click as fallback
                        await page.evaluate('element => element.click()', phone_auth_element)
                        logger.debug("Clicked element using JavaScript")

                except Exception as e:
                    logger.error(f"Error during phone authentication: {str(e)}")
                    # Save debug info
                    # await page.screenshot(path="auth_error.png")
                    # content = await page.content()
                    # with open("auth_error.html", "w", encoding="utf-8") as f:
                    #     f.write(content)
                    raise

                logger.debug("Waiting for authentication number")
                auth_number_element = await page.wait_for_selector(
                    ".display-sign-container", timeout=60000
                )

                if not auth_number_element:
                    logger.error("Failed to find authentication number element")
                    raise Exception("Failed to find authentication number element")

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
