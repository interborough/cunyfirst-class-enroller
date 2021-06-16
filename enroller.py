import sys
import time
import keyboard

from playsound import playsound

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

bell_path = "audio\\bell.mp3"


def main():
    # Get user input.
    driver_path, username, password, class_num, class_term, time_delay = get_user_input()

    try:
        driver = webdriver.Chrome(driver_path)
    except WebDriverException:
        print("Invalid Chromedriver.exe path! Please double check the location of your Chromedriver.exe, "
              "and try again.")
        exit_routine()

    # Go to CUNYFirst.
    driver.get("https://home.cunyfirst.cuny.edu/")

    # Enter username and password.
    driver.find_element_by_id("CUNYfirstUsernameH").send_keys(username)
    driver.find_element_by_id("CUNYfirstPassword").send_keys(password)
    driver.find_element_by_id("submit").click()

    # Go to the Student Center.
    try:
        driver.find_element_by_link_text("Student Center").click()
    except NoSuchElementException:
        print("Invalid username or password! Please double check your login information, and try again.")
        driver.quit()
        exit_routine()

    # Click on the Enrollment Shopping Cart Button.
    driver.switch_to.frame("TargetContent")
    shopping_cart_button = WebDriverWait(driver, 10) \
        .until(ec.presence_of_element_located((By.ID, "DERIVED_SSS_SCL_SSS_ENRL_CART$276$")))

    shopping_cart_button.click()

    # There are 2 cases: There either is a term selection table or there is not. Try to select a term, otherwise
    # assume there is no term selection.
    try:
        select_term(class_term, driver)
        term_selection = True
        class_row, class_status_img_src = get_class_status(class_num, driver)
    except TimeoutError:
        term_selection = False
        class_row, class_status_img_src = get_class_status(class_num, driver)

    while class_status_img_src == "https://cssa.cunyfirst.cuny.edu/cs/cnycsprd/cache850/PS_CS_STATUS_CLOSED_ICN_1.gif":
        print(f"Class is closed! Checking again in {time_delay} seconds.")
        time.sleep(float(time_delay))

        # Refresh page and check status again.
        shopping_cart_tab = driver.find_element_by_link_text("shopping cart")
        shopping_cart_tab.click()

        if term_selection:
            select_term(class_term, driver)

        get_class_status(class_num, driver)

    if class_status_img_src == "https://cssa.cunyfirst.cuny.edu/cs/cnycsprd/cache850/PS_CS_STATUS_WAITLIST_ICN_1.gif":
        print("Class has a wait list. Attempting to join the wait list.")

    if class_status_img_src == "https://cssa.cunyfirst.cuny.edu/cs/cnycsprd/cache850/PS_CS_STATUS_OPEN_ICN_1.gif":
        print("Class is open! Attempting to enroll.")

    enroll_in_class(class_row, driver)
    driver.quit()
    exit_routine()


def get_user_input():
    driver_path = input(
        "Enter the location of your chromedriver.exe. (ex: C:\\Users\\Bob\\Desktop\\chromedriver.exe)\n").strip()

    username = input(
        "Enter your CUNYFirst username (without the @login.cuny.edu, just the FirstName.LastNameNumber)\n").strip()

    password = input("Enter your CUNYFirst password\n").strip()
    class_num = input("Enter the class number of the class you wish to enroll in (ex: 45378)\n").strip()
    class_term = input("Enter the term of the class you wish to enroll in (ex: 2021 Spring Term or 2021 Summer Term)"
                       "\n").strip()

    time_delay = input("Enter the time in seconds that you wish to wait in between class status checks (Check if "
                       "class is open. If not, wait this many seconds and check again.)\n").strip()

    print()

    return driver_path, username, password, class_num, class_term, time_delay


def select_term(class_term, driver):
    # Gets term table and continues to the shopping cart for a specific term.
    term_table = WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.ID, "SSR_DUMMY_RECV1$scroll$0")))
    all_term_rows = term_table.find_elements_by_css_selector('tr')
    term_row = None

    for cell in all_term_rows:
        if class_term in cell.text:
            term_row = cell

    if term_row is None:
        print("Invalid class term! Please make sure that your term input is in the following format: \"Year "
              "TimeOfYear Term\" (ex: 2021 Fall Term) and try again.")
        driver.quit()
        exit_routine()

    row_data = term_row.find_elements_by_css_selector('td')
    circle_selector = row_data[0]
    circle_selector.click()

    continue_button = driver.find_element_by_id("DERIVED_SSS_SCT_SSR_PB_GO")
    continue_button.click()


# Check if class is open, closed, or has a wait list.
def get_class_status(class_num, driver):
    # Gets the enrollment table and specific class row.
    class_table = WebDriverWait(driver, 10) \
        .until(ec.presence_of_element_located((By.ID, "SSR_REGFORM_VW$scroll$0")))

    all_class_rows = class_table.find_elements_by_css_selector('tr')
    class_row = None

    for cell in all_class_rows:
        if class_num in cell.text:
            class_row = cell

    if class_row is None:
        print("Class is not in your shopping cart, or you entered the wrong class number! Please ensure that the "
              "class is in your shopping cart, and that you have the correct class number.")
        driver.quit()
        exit_routine()

    class_status_img = class_row.find_element_by_class_name("SSSIMAGECENTER")
    class_status_img_src = class_status_img.get_attribute("src")

    return class_row, class_status_img_src


# Try to enroll in the class.
def enroll_in_class(class_row, driver):
    # Click checkbox, enroll button, and then submit button
    class_row.find_element_by_class_name("PSCHECKBOX").click()

    enroll_button = driver.find_element_by_id("DERIVED_REGFRM1_LINK_ADD_ENRL")
    enroll_button.click()

    submit_button = WebDriverWait(driver, 10) \
        .until(ec.presence_of_element_located((By.ID, "DERIVED_REGFRM1_SSR_PB_SUBMIT")))
    submit_button.click()

    # Check if enrollment occurred with no errors.
    enrollment_status_table = WebDriverWait(driver, 10) \
        .until(ec.presence_of_element_located((By.ID, "SSR_SS_ERD_ER$scroll$0")))

    all_enrollment_status_rows = enrollment_status_table.find_elements_by_css_selector('tr')
    enrollment_status_row = all_enrollment_status_rows[1]

    all_enrollment_status_data = enrollment_status_row.find_elements_by_css_selector("td")
    enrollment_message = all_enrollment_status_data[1].text

    print(enrollment_message + "\n")


def exit_routine():
    playsound(bell_path, block=False)
    print("Press the \"Q\" key to quit.")

    while True:
        if keyboard.is_pressed("q"):
            sys.exit(0)


main()
