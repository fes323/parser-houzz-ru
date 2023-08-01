import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import csv
import re

# Set up logging
logging.basicConfig(level=logging.INFO, filename="scraping_log.log", format="%(asctime)s - %(levelname)s - %(message)s")


def get_studio_links(base_url):
    studio_links = []
    page_number = 1
    page_counter = 0
    while True:
        url = f"{base_url}/p/{page_number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        studios = soup.find_all("a", class_="hz-pro-ctl")
        if not studios:
            print(f'[INFO] Поиск студий закончен. Количесто страниц: {page_counter}')
            break
        studio_links.extend([studio["href"] for studio in studios])
        page_number += 15
        print(f'[INFO] Пройдено страниц: {page_counter}')
        print(f'[INFO] Обработана ссылка: {url}')
        page_counter += 1

    return studio_links

def format_phone_number(phone_number):
    # Remove all non-numeric characters
    phone_number = re.sub(r"[^0-9]", "", phone_number)
    
    # Add country code if needed
    if phone_number.startswith("8"):
        phone_number = "+7" + phone_number[1:]
    elif phone_number.startswith("7"):
        phone_number = "+7" + phone_number[1:]
    elif phone_number.startswith("+7"):
        phone_number = "+7" + phone_number[2:]
    
    return phone_number

def get_studio_details(studio_link):
    response = requests.get(studio_link)
    soup = BeautifulSoup(response.content, "html.parser")

    def get_field_text(soup, field_name):
        try:
            return soup.find("h3", text=field_name).find_next("p").text.strip()
        except AttributeError:
            return None

    business_name = get_field_text(soup, "Business Name")
    phone_number = get_field_text(soup, "Phone Number")
    phone_number = format_phone_number(phone_number) if phone_number else None
    website = soup.find("h3", text="Website").find_next("a")["href"] if soup.find("h3", text="Website") else None
    address = get_field_text(soup, "Address")
    typical_job_cost = get_field_text(soup, "Typical Job Cost")
    socials = [social["href"] for social in soup.find("h3", text="Socials").find_all("a")] if soup.find("h3", text="Socials") else []

    print(f'[INFO] {business_name} {phone_number} {website} {address} {typical_job_cost}')
    return {
        "link": studio_link,
        "Business Name": business_name,
        "Phone Number": phone_number,
        "Website": website,
        "Address": address,
        "Typical Job Cost": typical_job_cost,
        "Socials": ", ".join(socials)
    }
    
def save_to_csv(data_list):
    # Function to save data to a CSV file
    with open("studio_data_stroitelystvo.csv", "w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = ["link", "Business Name", "Phone Number", "Website", "Address", "Typical Job Cost", "Socials"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_list)
        
def main():
    base_url = "https://www.houzz.ru/professionals/proektirovanie-i-stroitelystvo"
    studio_links = get_studio_links(base_url)

    # Try to load progress from CSV file if it exists
    try:
        df = pd.read_csv("studio_data_stroitelystvo.csv", encoding="utf-8-sig")
        processed_links = set(df["link"])
        logging.info(f"Loaded progress: {len(processed_links)} studios already processed.")
    except FileNotFoundError:
        processed_links = set()

    studio_details = []
    for link in studio_links:
        if link in processed_links:
            logging.info(f"Skipping {link} as it's already processed.")
            continue

        try:
            studio_details.append(get_studio_details(link))
            logging.info(f"Processed {link}")
            save_to_csv(studio_details)  # Save progress after processing each page
        except Exception as e:
            logging.error(f"Error processing {link}: {str(e)}")

    df = pd.DataFrame(studio_details)
    df.to_csv("studio_data_stroitelystvo.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()