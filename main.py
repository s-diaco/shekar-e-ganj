# %%
from io import BytesIO
import pathlib
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import imagehash
from PIL import Image

# constants
SLEEP_SCROLL_TIME = 2
TOTAL_SCROLL_TIME = 300
PRODUCT_PAGE_LOAD_TIME = 2
MAX_IMAGE_LOAD_RETRIES = 2
REF_IMAGE_PATH = "ref_images/iphone.jpg"
HASHDIFF_CUT_OFF = 5
START_PAGE = 1
TOTAL_PAGES = 200

# Enter page address
dynamic_url = "https://www.digikala.com/search/notebook-netbook-ultrabook/?sort=7"


# %% Helper functions


def get_product_urls(driver, dynamic_url: str, start_page=None, num_pages=None):
    all_product_links = []
    if num_pages is None:
        driver.get(dynamic_url)
        print("waiting to load product list")
        # time.sleep(20)
        links = scroll_down_gradual(driver=driver)
        all_product_links = [
            link["href"] for link in links if "product" in link["href"]
        ]
        print(f"found {len(all_product_links)} products.")
        photo_list, loaded_images, unavailable_images = get_product_images(
            driver=driver, product_codes=all_product_links
        )
    else:
        for page_no in range(1, num_pages + 1):
            driver.get(f"{dynamic_url}&page={page_no}")
            print(f"Page {page_no}. waiting to load product list")
            # time.sleep(20)
            links = scroll_down_gradual(driver=driver)
            new_links = [link["href"] for link in links if "product" in link["href"]]
            all_product_links += new_links
            print(f"found {len(links)} new products. Total: {len(all_product_links)}")
            photo_list, loaded_images, unavailable_images = get_product_images(
                driver=driver, product_codes=new_links
            )
    # print(*all_links, sep="\n")
    return all_product_links, photo_list, loaded_images, unavailable_images


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

        # Get the page source (including JavaScript-rendered content)
        page_source = driver.page_source

        # Parse the page with Beautiful Soup
        dynamic_soup = BeautifulSoup(page_source, "html.parser")
        # links = soup.find_all("a", {"class": ["block", "cursor-pointer"]})
        links = dynamic_soup.find_all("a", {"class": ["block", "cursor-pointer"]})
        return links


def compare_tierce_images(pil_image):
    # Convert cv2Img from OpenCV format to PIL format
    # pilImg = cv2.cvtColor(cv2Img, cv2.COLOR_BGR2RGB)

    # get first and last third of the image
    w, h = pil_image.size
    first_tierce = pil_image.crop((0, 0, w / 3, h / 3))
    last_tierce = pil_image.crop((w * 0.66, h * 0.66, w, h))

    ref_image = Image.open(REF_IMAGE_PATH)

    # get first and last third of the ref_image
    w, h = ref_image.size
    first_ref_tierce = ref_image.crop((0, 0, w / 3, h / 3))
    last_ref_tierce = ref_image.crop((w * 0.66, h * 0.66, w, h))

    # Get the average hashes of both images
    hash00 = imagehash.average_hash(first_tierce)
    hash01 = imagehash.average_hash(first_ref_tierce)
    hash_diff = hash00 - hash01  # Finds the distance between the hashes of images
    if hash_diff < HASHDIFF_CUT_OFF:
        print(f"These images are similar! hashdiff: {hash_diff}")
        return True
    else:
        print(f"Images are not similar. hashdiff: {hash_diff}")

    # Get the average hashes of both images
    hash10 = imagehash.average_hash(last_tierce)
    hash11 = imagehash.average_hash(last_ref_tierce)
    hash_diff = hash10 - hash11  # Finds the distance between the hashes of images
    if hash_diff < HASHDIFF_CUT_OFF:
        print(f"Found similar images! hashdiff: {hash_diff}")
        return True
    else:
        print(f"Images are not similar. hashdiff: {hash_diff}")
    return False


# %% load every product page and get photo addresses
def get_product_images(driver, product_codes: list):
    photo_list = []
    unavailable_images = 0
    loaded_images = 0
    for link in product_codes:
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
        # load and print images
        for img_data in product_pics:
            (product_code, image_url) = img_data
            print(f"Loading Photo for: {product_code}:")
            attempts = 0
            pathlib.Path("images").mkdir(parents=True, exist_ok=True)
            pathlib.Path("images_not_matched").mkdir(parents=True, exist_ok=True)
            while True:
                try:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image_data = BytesIO(response.content)
                        image = Image.open(image_data)
                        # plt.figure(figsize=(3, 3))
                        # image = imread(image_url)
                        # pimage = Image.open(f"images/{product_code}.jpg")
                        # pil_image = Image.fromarray(image)
                        if compare_tierce_images(pil_image=image):
                            image.save(f"images/{product_code}.jpg")
                            # plt.imshow(image)
                            # plt.axis("off")
                            # plt.show()
                            display(image)
                        else:
                            image.save(
                                f"images_not_matched/img-{loaded_images}_{product_code}.jpg"
                            )
                        loaded_images += 1
                        break
                except:
                    if attempts > MAX_IMAGE_LOAD_RETRIES:
                        print(
                            f"image load error for {product_code}. Loading Noxt Image..."
                        )
                        unavailable_images += 1
                        break
                    else:
                        print(f"image load error for {product_code}. retrying...")
                        attempts += 1
    return photo_list, loaded_images, unavailable_images


# %%
# test_img = Image.open("ref_images/galaxy_code.jpg")
# compare_tierce_images(test_img)

# %% start
options = Options()
options.add_argument("--headless=new")
# options.binary_location='/usr/bin/chromedriver'
driver = webdriver.Chrome(options=options)
print("Headless Chrome Initialized")

product_codes, photo_list, loaded_images, unavailable_images = get_product_urls(
    driver=driver,
    dynamic_url=dynamic_url,
    start_page=START_PAGE,
    num_pages=TOTAL_PAGES,
)
# %% Clean up selenium driver
driver.quit()

# %% Print statistics
print("Summary:")
print(f"Total products found: {len(product_codes)}")
print(f"Total product images: {len(photo_list)}")
print(f"Images loaded:        {loaded_images}")
print(f"Images not loaded:    {unavailable_images}")

# %%
