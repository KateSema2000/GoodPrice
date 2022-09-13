from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from util.utils import *
import requests

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_abt_map():
    with open('map_atb.xml', 'r', encoding="utf-8") as file:
        text = file.read()
        soup = BeautifulSoup(text, 'lxml')
        urls = [link.text for link in soup.find_all('loc')]
        urls = list(filter(lambda x: (str(x).find('catalog') != -1), urls[1:]))
    used_way, used_url = [], []
    urls_atb = urls
    for url in urls_atb:
        way = url.split('/')[-1:]
        if way not in used_way:
            if str(way[0]).isdigit():
                used_way.append(way)
                used_url.append(url)
    return used_url


def get_soup(url):
    try:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'lxml')
        return soup
    except Exception as e:
        return None


def get_next_page_soup(url, i):
    return get_soup(f'{url}{"?page="}{i}')


def get_all_pages(url):
    soups = []
    soup = get_soup(url)
    soups.append(soup)
    next = soup.find('li', class_="product-pagination__item next")
    page_number = 2
    while next:
        soup = get_next_page_soup(url, page_number)
        if soup:
            soups.append(soup)
            page_number += 1
            next = soup.find('li', class_="product-pagination__item next")
        else:
            next = False
    return soups


_name = 'name'
_price = 'price'
_price_per_kg = 'price_per_kg'
_discount_price = 'discount_price'
_discount = 'discount'
_weight = 'weight'
_count = 'count'
_measurement = 'measurement'
_img = 'img'

_tag = 'tag'
_class = 'class_'
_attribute = 'attribute'

way_items = {_tag: 'article', _class: 'catalog-item js-product-container'}
way_name = {_tag: 'a', _class: 'blue-link'}
way_price = {_tag: 'data', _class: 'product-price__top', _attribute: 'value'}
way_discount_price = {_tag: 'data', _class: 'product-price__bottom', _attribute: 'value'}
way_count = {_tag: 'span', _class: 'product-price__unit', }
way_img = {_tag: 'img', _class: 'catalog-item__img', _attribute: 'src'}
way_links = {_tag: 'a', _class: 'catalog-item__photo-link', _attribute: 'href'}


# a class="catalog-item__photo-link
def get_all_items(page, way):
    values = page.find_all(way[_tag], class_=way[_class])
    if _attribute in way.keys():
        values = [name[way[_attribute]] for name in values]
    return values


def get_values_from_mass(mass, way):
    values = [el.find(way[_tag], class_=way[_class]) for el in mass]
    if _attribute in way.keys():
        values = [el if not el else el[way[_attribute]] for el in values]
    else:
        values = [el if not el else del_space(el.text) for el in values]
    return values


def get_items_from_page(page, cat, sub):
    items_data = get_all_items(page, way_items)
    items = []

    names = get_values_from_mass(items_data, way_name)
    prices = get_values_from_mass(items_data, way_price)
    prices = [el if not el else float(el) for el in prices]
    discount_prices = get_values_from_mass(items_data, way_discount_price)
    discount_prices = [el if not el else float(el) for el in discount_prices]
    discounts = [None if not pd else calculate_discount(p, pd) for p, pd in zip(prices, discount_prices)]
    weights_and_measurements = [get_weight_from_name(name) for name in names]
    weights = [el[0] for el in weights_and_measurements]
    measurements = [el[1] for el in weights_and_measurements]
    counts = get_values_from_mass(items_data, way_count)
    counts = [el if not el else el.split('/')[-1] for el in counts]
    for i in range(0, len(counts)):
        if counts[i] == 'кг':
            weights[i] = 1.0
            measurements[i] = 'кг'
    prices_per_kg = [get_price_per_kg(p, w, m, c) for p, w, m, c in zip(prices, weights, measurements, counts)]
    url_atb = 'https://zakaz.atbmarket.com'
    links = get_values_from_mass(items_data, way_links)
    links = [url_atb + str(el) for el in links]
    imgs = get_values_from_mass(items_data, way_img)
    imgs = [(url_atb + str(el)) if el[0] == '/' else el for el in imgs]

    for i, it in enumerate(items_data):
        items.append([cat, sub])
        items[-1].append(names[i])
        items[-1].append(weights[i])
        items[-1].append(measurements[i])
        items[-1].append(counts[i])
        items[-1].append(prices[i])
        items[-1].append(discount_prices[i])
        items[-1].append(prices_per_kg[i])
        items[-1].append(discounts[i])
        items[-1].append(links[i])
        items[-1].append(imgs[i])
    return items
