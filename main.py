from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from datetime import datetime, timedelta
from pytz import timezone

import telegram_config
from db.work_with_db import *
from parse.parsing import *

count = 20
admin = '573958202'


def get_all_items_atb():
    try:
        delete_data(Name_Items)
        urls_atb = get_data_from_table(Name_Menu)
        print('Завантаження даних про товари... ')
        for cat, sub, link in urls_atb:
            soups = get_all_pages(link)
            for soup in soups:
                items = get_items_from_page(soup, cat, sub)
                if items:
                    add_data_to_table(Name_Items, items, printing_out=False)
        items_len = len(get_data_from_table(Name_Items))
        print(f'Додано {items_len} товарів у базу')
        return True
    except Exception as e:
        print(e)
        return False


def get_and_save_menu():
    delete_data(Name_Menu)
    link = 'https://zakaz.atbmarket.com'
    soup = get_soup(link)
    menu = soup.find('ul', 'category-menu')
    menu_li = menu.find_all('li', 'category-menu__item')[3:]
    mass = []
    for i in menu_li:
        sub = i.find_all('li', 'submenu__item')
        for j in sub:
            mass.append([i.a.text, j.a.text, link + j.a['href']])
    add_data_to_table(Name_Menu, mass, printing_out=False)
    print(f'Додано {len(mass)} підкатегорій у базу')


def loging(update, answer, reply_markup=None):
    # answer = answer.replace("_", "\\_").replace("*", "\\*").replace("|", "\\|").replace(".", "\\.")
    # выводит переписку в консоль + отправляет смс юзеру
    print(update.effective_user.mention_markdown_v2(), update.message.from_user.name)
    print('-', update.message.text.replace('\n', '\\n'))
    print('-', answer.replace('\n', '\\n'), '\n')
    if not reply_markup:
        reply_markup = ReplyKeyboardRemove()
    update.message.reply_text(answer, reply_markup=reply_markup, parse_mode='HTML')


def get_uts():
    dif = datetime.now().hour - datetime.utcnow().hour
    ukraine_time = timezone('Europe/Kiev')
    d_uk = datetime.now(ukraine_time)
    uts = int(str(d_uk.utcoffset())[0])
    return uts - dif


def upd_alarm(_: CallbackContext) -> None:
    'ЗАПУСТИЛОСЬ ЕЖЕДНЕВНОЕ ОБНОВЛЕНИЕ'
    try:
        get_and_save_menu()
        get_all_items_atb()
    except Exception as e:
        print(e)
    finally:
        upd()


def upd():
    t = datetime.now()
    time = datetime(t.year, t.month, t.day, 7 - get_uts(), 0, 0, 0) + timedelta(days=1)
    updater.job_queue.run_once(upd_alarm, time, context=int(admin), name='update' + str(time))


def set_count(update: Update, context: CallbackContext) -> None:
    global count
    args = context.args
    if args:
        if args[0].isdigit():
            count = int(args[0])
            answer = f"Кількість відображених товарів: {count}" if count < 40 else "Це занадто велике число"
        else:
            answer = f"Помилкова кількість"
        loging(update, answer, markup)
    else:
        answer = f"Оберіть кількість відображених товарів:"
        temp_keyboard = []
        for number in range(5, 41, 10):
            temp_keyboard.append([f'/set {number}', f'/set {number + 5}'])
        temp_markup = ReplyKeyboardMarkup(temp_keyboard, one_time_keyboard=False)
        loging(update, answer, temp_markup)


def start(update: Update, _: CallbackContext) -> None:
    # стартовая команда для юрера
    answer = 'Привіт, я бот, який допоможе тобі знайти найдешевші товари в АТБ.\n\n' \
             'Ти можеш надіслати мені назву товару українською і я складу список найвигідніших пропозицій за назвою' \
             'у даному магазині.\nНаприклад надішлі мені "напій" або "цукор".\n' \
             'Якщо товар має складну назву, напиши мені ключові слова через кому, наприклад: ' \
             '"кава, мелена" або "морожене, 1 кг", а якщо нічого не знаходить, можете написати частину слова, ' \
             'наприклад "консерв", для того, щоб знайти "консерва" або "консерви"\n\n' \
             'Ви також можете порівнювати ціни товарів у категорії, просто натисніть /go і виберіть потрібну' \
             ' категорію товарів.\n\n' \
             'Якщо ви не знайшли потрібний товар серед відображених, ви можете збільшити кількість показаних ' \
             'товарів за допомогою команди /set та вказавши ціле число, наприклад "/set 30".\n\n' \
             'Якщо ви відправите слово "акція" або "знижки", я надішлю вам список товарів з найбільшою знижкою.'
    loging(update, answer, markup)


def echo(update: Update, context: CallbackContext) -> None:
    # Основной читалель смс от юзера
    if update.message.text.lower() in {'акція', 'акция', 'акции', 'скидки', 'скидка', 'знижка', 'знижки'}:
        items = get_data_from_table(Name_Items)
        result = list(filter(lambda x: x[9], items))
        result.sort(key=lambda x: x[9], reverse=True)
        answer = to_list_items(result, sort=False)
        if not answer:
            answer = 'Немає товарів'
        loging(update, answer)
    else:
        names = update.message.text.split(',')
        items = get_data_from_table(Name_Items)
        result = items
        for name in names:
            result = list(filter(lambda x: re.search(name, x[2], re.IGNORECASE), result))  # str(x[2]).find(name) != -1
        answer = to_list_items(result)
        if not answer:
            answer = 'Немає товарів'
        loging(update, answer)


def cancel(update: Update, _: CallbackContext) -> None:
    answer = 'Скасування дій'
    loging(update, answer, markup)


def category(update: Update, _: CallbackContext) -> None:
    # визначимося з категорією товарів
    answer = 'Обери категорію:'
    temp_keyboard = []
    categories = list(set([el[0] for el in get_data_from_table(Name_Menu, select='Category')]))
    categories.sort()
    for cat in categories:
        temp_keyboard.append(['/c ' + cat])
    temp_keyboard.append(['/cancel'])
    temp_markup = ReplyKeyboardMarkup(temp_keyboard, one_time_keyboard=False)
    loging(update, answer, temp_markup)


def subcategory(update: Update, context: CallbackContext) -> None:
    # визначимося з підкатегорією товарів
    cat = ' '.join(context.args)
    print(cat)
    answer = 'Обери підкатегорію:'
    temp_keyboard = []
    subcategories = list(
        set([el[0] for el in get_data_from_table(Name_Menu, select='Subcategory', where=f'Category = "{cat}"')]))
    subcategories.sort()
    for sub in subcategories:
        temp_keyboard.append(['/s ' + sub])
    temp_keyboard.append(['/cancel'])
    temp_markup = ReplyKeyboardMarkup(temp_keyboard, one_time_keyboard=False)
    loging(update, answer, temp_markup)


def to_list_items(items, length=None, sort=True):
    # формування відповіді з товарами(назва, посилання, ціна)
    answer = '' if items else 'Немає товарів...'
    if sort:
        items = sorted(items, key=lambda x: (x[6] == '', x[6]))
        items = sorted(items, key=lambda x: (x[8] == '', x[8]))
    for it in items[:length if length else count]:
        answer += f'{it[2]}\n' + (f'[<a href="{it[-1]}">фото</a>/' if it[-1] else '') + \
                  f'<a href="{it[-2]}">посил.</a>]' \
                  f' {it[6]} грн ' + (f'| {it[8]} грн/кг ' if it[8] else '') + \
                  (f'| -{it[9]}%' if it[9] else '') + f'\n\n'
    return answer


def open_sub(update: Update, context: CallbackContext) -> None:
    # формування товарів з конкретної підкатегорії
    sub = ' '.join(context.args)
    print(sub)
    answer = f'{sub}\n'
    items = get_data_from_table(Name_Items, where=f'Subcategory = "{sub}"')
    answer += to_list_items(items)
    loging(update, answer)


if __name__ == '__main__':
    print(f'Старт бота: {datetime.now()}')
    updater = Updater(telegram_config.token)
    dispatcher = updater.dispatcher
    reply_keyboard = [['/start', '/go', '/set']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

    get_and_save_menu()
    get_all_items_atb()
    upd()

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("go", category))
    dispatcher.add_handler(CommandHandler("c", subcategory))
    dispatcher.add_handler(CommandHandler("s", open_sub))
    dispatcher.add_handler(CommandHandler("cancel", cancel))
    dispatcher.add_handler(CommandHandler("set", set_count))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    updater.start_polling()
    updater.idle()

'''
git add .
git commit -am "make it better"
git push -u origin main 
'''
