import sys
import time
from playsound import playsound
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

bell_path = "audio\\bell.mp3"


def main():
    # Get user input.
    driver_path, username, password, class_num, class_term, time_delay = get_user_input()
    driver = webdriver.Chrome(driver_path)

    # Go to Google and search for CUNYFirst. CUNYFirst doesn't allow you to login if you use the URL directly.
    driver.get("https://www.google.com/")
    searchbar = driver.find_element_by_name("q")
    searchbar.send_keys("CUNYfirst")
    searchbar.submit()
    driver.find_element_by_partial_link_text("CUNYfirst").click()

    # Enter username and password.
    driver.find_element_by_id("CUNYfirstUsernameH").send_keys(username)
    driver.find_element_by_id("CUNYfirstPassword").send_keys(password)
    driver.find_element_by_id("submit").click()

    # Go to the Student Center.
    driver.find_element_by_link_text("Student Center").click()

    # Click on the Enrollment Shopping Cart Button.
    driver.switch_to.frame("TargetContent")
    shopping_cart_button = WebDriverWait(driver, 10) \
        .until(ec.presence_of_element_located((By.ID, "DERIVED_SSS_SCL_SSS_ENRL_CART$276$")))

    shopping_cart_button.click()

    # Returns the status of a given class, based on its class number.
    try:
        # TODO: CLICK ON TERM. after clicking the Enrollment Shopping Cart button it will show you a term selection (
        #  ex: Spring 2021, Summer 2021). Other times, however, it will bring you directly to a single term if there
        #  is only one applicable at the moment (for example, as of 1/31/2021 Spring 2021 is the only active term).
        #  If term selection isn't available (no such element for term table), we can assume that there's only one
        #  active term.
        class_row, class_status_img_src = get_class_status(class_num, driver)
    except NoSuchElementException:
        class_row, class_status_img_src = get_class_status(class_num, driver)

    while class_status_img_src == "https://cssa.cunyfirst.cuny.edu/cs/cnycsprd/cache850/PS_CS_STATUS_CLOSED_ICN_1.gif":
        print(f"Class is closed! Checking again in {time_delay} seconds.")
        time.sleep(float(time_delay))

        # Refresh page and check status again.
        shopping_cart_tab = driver.find_element_by_link_text("shopping cart")
        shopping_cart_tab.click()
        get_class_status(class_num, driver)

    if class_status_img_src == "https://cssa.cunyfirst.cuny.edu/cs/cnycsprd/cache850/PS_CS_STATUS_WAITLIST_ICN_1.gif":
        print("Class has a wait list. Attempting to join the wait list.")

    if class_status_img_src == "https://cssa.cunyfirst.cuny.edu/cs/cnycsprd/cache850/PS_CS_STATUS_OPEN_ICN_1.gif":
        print("Class is open! Attempting to enroll.")

    enroll_in_class(class_row, driver)
    time.sleep(3)
    driver.quit()


# Gets user input.
def get_user_input():
    driver_path = input(
        "Enter the location of your chromedriver.exe. (ex: C:\\Users\\Bob\\Desktop\\chromedriver.exe)\n").strip()
    username = input(
        "Enter your CUNYFirst username (without the @login.cuny.edu, just the FirstName.LastNameNumber)\n").strip()
    password = input("Enter your CUNYFirst password\n").strip()
    class_num = input("Enter the class number (ex: 45378)\n").strip()
    class_term = input("Enter the class term (ex: Spring 2021 Term)\n").strip()
    time_delay = input("Enter the time in seconds that you wish to wait in between class status checks (ex: Check if "
                       "class is open. If not, wait this many seconds and check again.)\n").strip()

    return driver_path, username, password, class_num, class_term, time_delay


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
        print("Class is not in shopping cart! Please add the class to your cart and try again.")
        playsound(bell_path)
        driver.quit()
        sys.exit(1)

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

    enrollment_status_img = enrollment_status_row.find_element_by_class_name("SSSIMAGECENTER")
    enrollment_status_img_src = enrollment_status_img.get_attribute("src")

    if enrollment_status_img_src != "https://cssa.cunyfirst.cuny.edu/cs/cnycsprd/cache850" \
                                    "/PS_CS_STATUS_SUCCESS_ICN_1.gif":
        print("There was an error enrolling. Please see the CUNYFirst error message below and try again.\n")

    print(enrollment_message)
    playsound(bell_path)


main()
