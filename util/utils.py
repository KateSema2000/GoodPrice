import re


def printl(mass):
    for i, el in enumerate(mass):
        print(f'{i + 1}: {el}')


def del_space(text_with_space):
    return ' '.join(text_with_space.split())


def calculate_discount(price, price_discount):
    return round(100 - 100 * (price / price_discount), 2)


def get_price_per_kg(price, w, m, c):
    if c == 'шт':
        if m == 'г' or m == 'мл':
            return int(((1000 / w) * price) * 100) / 100
        if m == 'кг' or m == 'л':
            return int((price / w) * 100) / 100
    else:
        return float(price)
    return ''


def get_weight_from_name(name):
    sh = '\d+[.,]?\d*[ ]?[кгмлшт]+\\b'
    sh1 = '\d+[.,]?\d*'
    sh2 = '[кгмлшт]+\\b'
    weight = ''
    try:
        res = re.search(sh, name)
        weight += res[0] if res else ''
        m = re.search(sh2, weight)[0]
        w = float(re.search(sh1, weight)[0].replace(',', '.'))
        return w, m
    except:
        return None, None
