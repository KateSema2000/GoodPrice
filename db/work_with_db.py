import sqlite3

path_db_1 = 'goodprice_1.db'

Name_Menu = 'Menu'
Name_Items = 'Items'

Add_Menu = '(Category TEXT, Subcategory TEXT, Link TEXT)'
Add_Items = '(Category TEXT,Subcategory TEXT,Name TEXT,Weight REAL,Measurement TEXT,Count TEXT,PriceGeneral REAL,' \
            'PriceDiscont REAL,PricePerKg REAL,Discont REAL,Link TEXT,ImgUrl TEXT)'

Insert_Menu = '(Category,Subcategory,Link) VALUES(?,?,?);'
Insert_Items = '(Category,Subcategory,Name,Weight,Measurement,Count,PriceGeneral,PriceDiscont,PricePerKg,Discont,' \
               'Link,ImgUrl) VALUES(?,?,?,?,?,?,?,?,?,?,?,?);'

insert_dict = {Name_Items: Insert_Items, Name_Menu: Insert_Menu}

add_dict = {Name_Items: Add_Items, Name_Menu: Add_Menu}


def find_key(the_dict, name):
    finds = []
    for key in the_dict:
        if name.find(key) != -1:
            finds.append([the_dict[key], len(name.replace(key, ''))])
    finds.sort(key=lambda x: x[1])
    if not finds:
        print('Нема подібних таблиць')
    return '' if not finds else finds[0][0]


get_add = lambda name: find_key(add_dict, name)
get_insert = lambda name: find_key(insert_dict, name)


def create_table(name, path=path_db_1):
    with sqlite3.connect(path) as db:
        cursor = db.cursor()
        query = f"CREATE TABLE IF NOT EXISTS {name} {get_add(name)}"
        cursor.execute(query)
        db.commit()
    print('Створена таблиця:', name)


def add_data_to_table(name, items, crash=False, path=path_db_1, printing_out=True):
    with sqlite3.connect(path) as db:
        cursor = db.cursor()
        query = f'INSERT INTO {name} {get_insert(name)}'
        try:
            cursor.executemany(query, items)
            db.commit()
            if printing_out:
                print('Додано', len(items), "елементів до таблиці", name)
        except Exception as e:
            print(e)
            create_table(name)
            if not crash:
                add_data_to_table(name, items, crash=True)


def update_data(name, what, value, where=None, path=path_db_1):
    with sqlite3.connect(path) as db:
        cursor = db.cursor()
        query = f"UPDATE {name} set {what} = {value} {f' WHERE {where}' if where else ''}"
        cursor.execute(query)
        db.commit()
    print(f'Оновлені елементи в таблиці {name}')


def delete_data(name, where=None, ask=False, path=path_db_1):
    with sqlite3.connect(path) as db:
        before = len(get_data_from_table(name, path=path))
        cursor = db.cursor()
        query = f"DELETE FROM {name}{f' WHERE {where}' if where else ''}"
        if ask:
            answer = input(f'Видалити усі дані таблиці? Запрос: {query}')
            if 'YyНн'.find(answer) == -1:
                return
        cursor.execute(query)
        db.commit()
        after = len(get_data_from_table(name, path=path))
    print(f'Видалені елементи: {before - after} з таблиці {name}')


def get_data_from_table(name, select=None, where=None, path=path_db_1):
    Items = []
    with sqlite3.connect(path) as db:
        query = f"SELECT {select if select else '*'} FROM {name}{f' WHERE {where}' if where else ''}"
        data = db.execute(query)
        for el in data:
            Items.append(el)
    return Items


def get_next_id(name, id='Id', path=path_db_1):
    Items = []
    with sqlite3.connect(path) as db:
        query = f"SELECT {id} FROM {name}"
        data = db.execute(query)
        for el in data:
            Items.append(el[0])
    return max(Items) + 1 if Items else 0
