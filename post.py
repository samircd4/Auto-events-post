from playwright.sync_api import sync_playwright, Page
from scraper import get_new_events
import pyperclip
import os
import requests
import shutil
from rich import print
import pandas as pd

def download_image(event_id, url):
    try:
        print('Downloading image')
        folder = 'images'
        is_exist = os.path.exists(folder)
        # extension = url.split('/')[-1].split('.')[-1]
        if not is_exist:
            os.mkdir(folder)
        file_name = f'{event_id}.{url.split(".")[-1]}'
        curr_dir = os.getcwd()
        file_path = f'{curr_dir}\\{folder}\\{file_name}'

        res = requests.get(url, stream=True)

        with open(file_path, 'wb') as file:
            shutil.copyfileobj(res.raw, file)
            file.close()
        print('SUCCESS: Image downloaded')
        return True
    except Exception as e:
        print('Image not found')
        return False


def login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=2000)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.lfgnexus.com/login")
        page.query_selector_all("a[aria-label='Member Login']")[0].click()
        page.locator("input#member_login_190-element-9").first.fill("samircd4@gmail.com")
        page.locator("input#member_login_190-element-10").first.fill("s72647D378#")
        page.locator("input#member_login_190-element-12").first.click()
        page.wait_for_timeout(5000)
        page.context.storage_state(path="state.json")
        page.close()
        context.close()
        browser.close()
        return

def get_description(page:Page, url):
    # url = 'https://bestcoastpairings.com/event/42RLNLGQCD'
    url = f'{url}?active_tab=overview'
    page.goto(url)
    try:
        details_header = page.locator('h6:has-text("Event Details:") + div')
        details_header.wait_for(state="visible", timeout=3000)
        desc = details_header.inner_html()
        page.wait_for_timeout(1000)
        page.close()
        if desc:
            print('Description added to clipboard')
        else:
            print('Description not found')
        return desc
    except:
        print('Description not found')
        page.close()
        return ""





def post_event(data):
    print(data)
    
    has_image = download_image(data['event_id'], data['img_url'])
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(storage_state="state.json")
        page = context.new_page()
        page.goto("https://www.lfgnexus.com/account/events/add")
        
        if 'login_direct_url' in page.url:
            return 'login required'
        
        with page.expect_file_chooser() as fc_info:
            page.get_by_text("Upload Image").click()
        file_chooser = fc_info.value
        if has_image:
            file_chooser.set_files(f"images/{data['event_id']}.png")
        else:
            file_chooser.set_files(f"images/default-image.png")
        
        page.get_by_label("Yes").check()
        page.get_by_placeholder("Enter the post title").click()
        page.get_by_placeholder("Enter the post title").fill(f"{data['name']} ({data['game_system']})")
        # page.get_by_label("select-").select_option("Game Night")
        page.locator('input#event_fields_322-element-15').fill(data['game_system'])
        try:
            page.get_by_label("event_fields-element-15-1").select_option(str(data['start_time']), timeout=1000)
        except:
            print('Start time is not round figure')
        try:
            page.get_by_label("event_fields-element-15-2").select_option(data['end_time'], timeout=1000)
        except:
            print('End time is not round figure')
            pass
        page.locator("#stardatepicker").click()
        page.locator("#stardatepicker").fill(data['start_date'])
        page.locator("#enddatepicker").click()
        page.locator("#enddatepicker").fill(data['end_date'])
        page.get_by_label("External Web Link").fill(data['event_link'])
        page.get_by_placeholder("Enter a location: 350 Fifth").fill(data['location'])
        # page.get_by_placeholder("Enter a location: 350 Fifth").click()
        page.get_by_placeholder("Enter a location: 350 Fifth").press("Enter")
        # page.get_by_label("Venue Name").fill("Test venue")
        page.get_by_label("Complete Address").click()
        page.locator('input#event_fields_322-element-28').fill(data['game_system'])
        
        description = get_description(page=context.new_page(), url=data['event_link'])
        pyperclip.copy(description)
        page.locator('button#html-1').click()
        page.wait_for_timeout(1000)
        page.keyboard.press("Control+V")
        
        page.get_by_role("button", name="Save Changes").click()
        page.wait_for_timeout(5000)
        
        page.close()
        context.close()
        browser.close()
        return 'success'

if __name__ == "__main__":
    # login()
    get_new_events()
    if os.path.exists('new_events.xlsx'):
        data = pd.read_excel('new_events.xlsx')
        data = data.to_dict('records')
        
        for event_details in data:
            print(f'Posting new event: {event_details["name"]}')
            response = post_event(event_details)
            if response == 'login required':
                login()
                post_event(event_details)
