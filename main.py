# %%
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from imageio.v2 import imread

# constants
SLEEP_SCROLL_TIME = 2
TOTAL_SCROLL_TIME = 300
PRODUCT_PAGE_LOAD_TIME = 2
MAX_IMAGE_LOAD_RETRIES = 2
# Enter page address
dynamic_url = "https://www.digikala.com/search/category-printed-book-of-philosophy-and-psychology/?sort=7"


# %% Helper functions
def scroll_down(driver):
    """A method for scrolling the page."""

    # Get scroll height.
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        total_time = 0
        # Scroll down to the bottom.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page.
        time.sleep(SLEEP_SCROLL_TIME)

        # Calculate new scroll height and compare with last scroll height.
        new_height = driver.execute_script("return document.body.scrollHeight")

        if (new_height == last_height) or (total_time > TOTAL_SCROLL_TIME):

            break

        last_height = new_height
        total_time += SLEEP_SCROLL_TIME


def scroll_down_gradual(driver):
    """A method for scrolling the page."""

    # Get scroll height.
    last_height = driver.execute_script("return document.body.scrollHeight")

    total_time = 0
    scroll_to = 1000
    while True:
        # Scroll down to the bottom.
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script(f"window.scrollTo(0, {scroll_to});")

        # Wait to load the page.
        time.sleep(SLEEP_SCROLL_TIME)

        # Calculate new scroll height and compare with last scroll height.
        new_height = driver.execute_script("return document.body.scrollHeight")
        if (new_height - scroll_to) > 1000:
            scroll_to += 1000

        if ((new_height == last_height) and ((new_height - scroll_to) < 999)) or (
            total_time > TOTAL_SCROLL_TIME
        ):

            break

        last_height = new_height
        total_time += SLEEP_SCROLL_TIME


# %% load the list page with all products
options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.get(dynamic_url)
print("Headless Chrome Initialized")
print("waiting to load product list")
# time.sleep(20)
scroll_down_gradual(driver=driver)
print("waiting ended.")

# Get the page source (including JavaScript-rendered content)
page_source = driver.page_source

# Parse the page with Beautiful Soup
dynamic_soup = BeautifulSoup(page_source, "html.parser")
all_links = []
# links = soup.find_all("a", {"class": ["block", "cursor-pointer"]})
links = dynamic_soup.find_all("a", {"class": ["block", "cursor-pointer"]})
all_links = [link["href"] for link in links if "product" in link["href"]]
print(f"found {len(all_links)} products:")
print(*all_links, sep="\n")

# %% load every product page and get photo addresses
photo_list = []
for link in all_links:
    product_url = f"https://www.digikala.com{link}"
    product_code = product_url[product_url.find("/product/") + len("/product/") :]
    product_code = product_code[: product_code.find("/")]
    driver.get(product_url)
    print("waiting to load product photos")
    time.sleep(PRODUCT_PAGE_LOAD_TIME)
    print("waiting ended.")
    product_page = driver.page_source
    product_soup = BeautifulSoup(product_page, "html.parser")
    product_pics = []
    pics = product_soup.find_all("img", {"class": ["w-full"]})
    product_pics = [
        (product_code, photo["src"])
        for photo in pics
        if "digikala-products" in photo["src"]
    ]
    print(f"{len(product_pics)} photos found for product {link}.")
    print(*product_pics, sep="\n")
    photo_list += product_pics
# %% Clean up selenium driver
driver.quit()
# %% load and print images
unavailable_images = 0
loaded_images = 0
for img_data in photo_list:
    (product_code, image_url) = img_data
    print(f"Photo for: {product_code}:")
    attempts = 0
    while True:
        try:
            image = imread(image_url)
            plt.imshow(image)
            plt.show()
            loaded_images += 1
            break
        except:
            if attempts > MAX_IMAGE_LOAD_RETRIES:
                print(f"image load error for {product_code}")
                unavailable_images += 1
                break
            else:
                attempts += 1

# %% Print statistics
print("Summary:")
print(f"Total products found: {len(all_links)}")
print(f"Total product images: {len(photo_list)}")
print(f"Images loaded:        {loaded_images}")
print(f"Images not loaded:    {unavailable_images}")

# %%
