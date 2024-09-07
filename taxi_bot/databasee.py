import sqlite3
import json
from geopy.distance import great_circle


class ClientDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS clients
                          (id INTEGER PRIMARY KEY, telegram_id INT, name TEXT, latitude REAL, longitude REAL, location TEXT, status TEXT, phone TEXT, ban INT, referred_by INTEGER, avatar TEXT, bonus INT DEFAULT 0)''')
        self.conn.commit()
    
    def check_client_in_db(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM clients WHERE telegram_id = ?''', (telegram_id,))
        if cursor.fetchone() is None:
            return False
        else:
            return True
    
    def check_client_in_db(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clients WHERE telegram_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        return count > 0
    
    def update_status_client_to_active(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE clients SET status = ? WHERE telegram_id = ?''', ('active', telegram_id,))
        self.conn.commit()
    
    def update_status_client_to_offline(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE clients SET status = ? WHERE telegram_id = ?''', ('offline', telegram_id,))
        self.conn.commit()
    
    def get_client_name(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM clients WHERE telegram_id = ?', 
                    (telegram_id,))
        return cursor.fetchone()
    
    def update_status_client_to_in_order(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE clients SET status = ? WHERE telegram_id = ?''', ('in_order', telegram_id,))
        self.conn.commit()
    
    def update_client_location(self, telegram_id, lat, long, location):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clients SET latitude = ?, longitude = ?, location = ? WHERE telegram_id = ?", (lat,long, location,telegram_id,))
        self.conn.commit()
    
    def update_client_name(self, telegram_id, name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clients SET name = ? WHERE telegram_id = ?", (name,telegram_id,))
        self.conn.commit()
    
    def add_client(self, telegram_id, name, phone, latitude, longitude, location, refferal_user):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO clients (telegram_id, name, latitude, longitude, location, status, phone, ban, referred_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (telegram_id, name, latitude, longitude, location, 'active', phone, 0, refferal_user))
        self.conn.commit()
    
    def user_exists(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone() is not None
    
    def add_bonus(self,telegram_id, bonus):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clients SET bonus = bonus + ? WHERE telegram_id = ?",(bonus,telegram_id,))
        self.conn.commit()
    
    def del_bonus(self,telegram_id, bonus):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clients SET bonus = bonus - ? WHERE telegram_id = ?",(bonus,telegram_id))
        self.conn.commit()
    
    def get_bonuses(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT bonus FROM clients WHERE telegram_id = ?",(telegram_id,))
        return cursor.fetchone()
    
    def update_avatar(self, telegram_id, avatar):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE clients SET avatar = ? WHERE telegram_id = ?',(avatar, telegram_id,))
        self.conn.commit()
    
    def get_avatar(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT avatar FROM clients WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()[0]
    
    def get_referrals(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE referred_by = ?', (user_id,))
        return cursor.fetchall()

    def get_referral_count(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM clients WHERE referred_by = ?', (user_id,))
        return cursor.fetchone()[0]
    
    def get_referal_id(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT referred_by FROM clients WHERE telegram_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result is None:
                return None
            return result[0]
        except:
            return None

    def get_nearby_active_drivers(self, client_latitude, client_longitude, radius=0.01):
        cursor = self.conn.cursor()
        cursor.execute('SELECT telegram_id FROM drivers WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ? AND status = ?', 
                    (client_latitude, radius * 2, client_longitude, radius * 2, 'active',))
        count = cursor.fetchall()

        # Если в круглой области не найдено водителей, попробуем прямоугольную область
        if count == 0:
            cursor.execute('SELECT telegram_id FROM drivers WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ? AND status = ?', 
                        (client_latitude - radius, client_latitude + radius, client_longitude - radius, client_longitude + radius, 'active',))
            count = cursor.fetchall()

        return count
    
    def get_client(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE telegram_id = ?', 
                        (telegram_id,))
        return cursor.fetchone()
    
    def get_client_status(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT status FROM clients WHERE telegram_id = ?', 
                    (telegram_id,))
        return cursor.fetchone()[0]
    
    def ban_client(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clients SET ban = 1, status = 'banned' WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()
    
    def unban_client(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE clients SET ban = 0, status = 'active' WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()
    
    def get_ifbanned_client(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT ban FROM clients WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone()[0]

    def get_nearby_active_drivers_count(self, client_latitude, client_longitude, radius=0.01):
        # Поиск в круглой области
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(status) FROM drivers WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ? AND status = ?', 
                    (client_latitude, radius * 2, client_longitude, radius * 2, 'active',))
        count = cursor.fetchone()[0]

        # Если в круглой области не найдено водителей, попробуем прямоугольную область
        if count == 0:
            cursor.execute('SELECT COUNT(status) FROM drivers WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ? AND status = ?', 
                        (client_latitude - radius, client_latitude + radius, client_longitude - radius, client_longitude + radius, 'active',))
            count = cursor.fetchone()[0]

        return count
    
    def get_location_client(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT location FROM clients WHERE telegram_id = ?",(telegram_id,))
        return cursor.fetchone()
    
    def get_client_lat_long(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT latitude,longitude FROM clients WHERE telegram_id = ?', 
                       (telegram_id,))
        return cursor.fetchone()

class DriverDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS drivers
                          (id INTEGER PRIMARY KEY, telegram_id INT, name TEXT, car TEXT, car_number TEXT, latitude REAL, longitude REAL, location TEXT, status TEXT, ban INT, phone TEXT, avatar TEXT, category TEXT, username TEXT)''')
        self.conn.commit()
    
    def check_driver_in_db(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM drivers WHERE telegram_id = ?''',(telegram_id,))
        if cursor.fetchone() is None:
            return False
        else:
            return True
    
    def add_driver(self, telegram_id, name, car, car_number, latitude, longitude, location, phone, category, username):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO drivers (telegram_id, name, car, car_number, latitude, longitude, location, status, ban, phone, category, username) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (telegram_id, name, car, car_number, latitude, longitude, location, 'active', 0, phone, category, f'@{username}'))
        self.conn.commit()
    
    def update_status_driver_to_active(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE drivers SET status = ? WHERE telegram_id = ?''', ('active', telegram_id,))
        self.conn.commit()
    
    def update_status_driver_to_offline(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE drivers SET status = ? WHERE telegram_id = ?''', ('offline', telegram_id,))
        self.conn.commit()
    
    def get_location_driver(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT location FROM drivers WHERE telegram_id = ?''', (telegram_id,))
        return cursor.fetchone()
    
    def update_driver_name(self, telegram_id, name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE drivers SET name = ? WHERE telegram_id = ?", (name,telegram_id,))
        self.conn.commit()
    
    def ban_driver(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE drivers SET ban = 1, status = 'banned' WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()
    
    def update_avatar(self, telegram_id, avatar):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE drivers SET avatar = ? WHERE telegram_id = ?',(avatar, telegram_id,))
        self.conn.commit()
    
    def get_nearby_active_clients(self, driver_latitude, driver_longitude, radius=0.01):
        cursor = self.conn.cursor()
        cursor.execute('SELECT telegram_id FROM clients WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ? AND status = ?', 
                    (driver_latitude, radius * 2, driver_longitude, radius * 2, 'active',))
        count = cursor.fetchall()
        # Если в круглой области не найдено водителей, попробуем прямоугольную область
        if count == 0:
            cursor.execute('SELECT telegram_id FROM clients WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ? AND status = ?', 
                        (driver_latitude - radius, driver_latitude + radius, driver_longitude - radius, driver_longitude + radius, 'active',))
            count = cursor.fetchall()
        return count

    
    def get_avatar(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT avatar FROM drivers WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()[0]
    
    def unban_driver(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE drivers SET ban = 0, status = 'active' WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()
    
    def get_ifbanned_driver(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT ban FROM drivers WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone()[0]
    
    def update_driver_location(self, telegram_id, lat, long, location):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE drivers SET latitude = ?, longitude = ?, location = ? WHERE telegram_id = ?", (lat,long,location,telegram_id,))
        self.conn.commit()

    def get_nearby_clients(self, driver_latitude, driver_longitude, radius=1.0):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ?', 
                       (driver_latitude, radius, driver_longitude, radius,))
        return cursor.fetchall()
    
    def get_nearby_active_clients_count(self, driver_latitude, driver_longitude, radius=1.0):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(status) FROM clients WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ? AND status = ?', 
                       (driver_latitude, radius, driver_longitude, radius, 'active',))
        return cursor.fetchall()
    
    def get_driver_car_details(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT car,car_number FROM drivers WHERE telegram_id = ?',(telegram_id,))
        return cursor.fetchone()
    
    def get_driver_status(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT status FROM drivers WHERE telegram_id = ?',(telegram_id,))
        return cursor.fetchone()[0]
    
    def get_driver_lat_long(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT latitude, longitude FROM drivers WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()
    
    def update_driver_status(self,telegram_id,status):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE drivers SET status = ? WHERE telegram_id = ?''', (status, telegram_id,))
        self.conn.commit()
    
    def get_driver(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM drivers WHERE telegram_id = ?''', (telegram_id,))
        return cursor.fetchone()

class OrderDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()

    def create_table(self):
        with sqlite3.connect('database/data.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INT, driver_id INT, destination TEXT, status TEXT, latitude REAL, longitude REAL, client_latitude REAL, client_longitude REAL, datetime TEXT,bonus INT)''')
            conn.commit()

    def add_order(self, client_id, destination, latitude, longitude, client_latitude, client_longitude, datetime, driver_id=0, bonus = 0):
        with sqlite3.connect('database/data.db') as conn:
            cursor = conn.cursor()
            if driver_id == 0:
                cursor.execute('INSERT INTO orders (client_id, destination, status, latitude, longitude, client_latitude, client_longitude, datetime, bonus) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (client_id, destination, 'pending', latitude, longitude, client_latitude, client_longitude, datetime, bonus))
                conn.commit()
            else:
                cursor.execute('INSERT INTO orders (client_id, driver_id, destination, status, latitude, longitude, client_latitude, client_longitude, datetime, bonus) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (client_id, driver_id, destination, 'accepted', latitude, longitude, client_latitude, client_longitude, datetime, bonus))
                conn.commit()

    def update_order_status(self, order_id, status):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id,))
        self.conn.commit()
    
    def select_order_datetime_user(self, user_id, datetime_str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE client_id=? AND datetime=? AND status=?", (user_id, datetime_str, 'pending',))
        return cursor.fetchone()

    def get_order_details(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        return cursor.fetchone()

    def get_active_orders_for_driver(self, driver_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE driver_id = ? AND status != ?', (driver_id, 'completed',))
        return cursor.fetchall()
    
    def get_order_by_client_id(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE client_id = ? AND status = ?', (telegram_id, 'to_client_from_taxi',))
        return cursor.fetchone()
    
    def get_order_by_cc_id(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE client_id = ? AND status = ?', (telegram_id, 'accepted',))
        return cursor.fetchone()

    def get_current_order_for_driver(self, driver_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE driver_id = ? AND status = 'accepted' OR status = 'to_client_from_taxi'", (driver_id, ))
        return cursor.fetchall()
    
    def get_driver_id(self,user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT driverid FROM orders WHERE client_id = ? AND status = ?', (user_id, 'accepted',))
        return cursor.fetchone()[0]
    
    def get_nearby_orders_for_driver(self, driver_latitude, driver_longitude, radius=0.01):
        # Поиск в круглой области
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE ABS(client_latitude - ?) < ? AND ABS(client_longitude - ?) < ? AND status = ?', 
                    (driver_latitude, radius * 2, driver_longitude, radius * 2, 'pending',))
        count = cursor.fetchall()

        # Если в круглой области не найдено водителей, попробуем прямоугольную область
        if count == 0:
            cursor.execute('SELECT * FROM orders WHERE client_latitude BETWEEN ? AND ? AND client_longitude BETWEEN ? AND ? AND status = ? OR status = ?', 
                        (driver_latitude - radius, driver_longitude + radius, driver_longitude - radius, driver_longitude + radius, 'pending', ))
            count = cursor.fetchall()
        
        return count

    def get_pending_orders(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE status = ?', ('pending',))
        return cursor.fetchall()
    
    def update_order_status_for_driver(self, order_id, driver_id, status):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE orders SET status = ? WHERE id = ? AND driver_id = ?', (status, order_id, driver_id))
        self.conn.commit()

    def update_order_status_for_client(self, order_id, client_id, status):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE orders SET status = ? WHERE id = ? AND client_id = ?', (status, order_id, client_id))
        self.conn.commit()
    
    def set_driver_order(self,order_id,driver_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE orders SET driver_id = ? WHERE id = ?', (driver_id, order_id))
        self.conn.commit()
    def get_current_order_from_driver(self, driver_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE driver_id = ? AND status = ?', (driver_id, 'to_client_from_taxi',))
        return cursor.fetchall()


class LangDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS langs
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INT, lang TEXT)''')
        self.conn.commit()
    
    def get_lang(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT lang FROM langs WHERE telegram_id = ?",(telegram_id,))
        return cursor.fetchone()[0]
    
    def add_lang(self, telegram_id, lang):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO langs (telegram_id, lang) VALUES (?, ?)',
                       (telegram_id, lang))
        self.conn.commit()
    
    def del_lang(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM langs WHERE telegram_id = ?',
                       (telegram_id,))
        self.conn.commit()
    
    def set_lang(self, telegram_id, lang):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE langs set lang = ? WHERE telegram_id = ?',
                       (lang, telegram_id,))
        self.conn.commit()

class ModeratorDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS moderators
                        (telegram_id INT)''')
        self.conn.commit()
    
    def add_moderator(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO moderators (telegram_id) VALUES (?)''', (telegram_id,))
        self.conn.commit()
    
    def get_moderators(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT telegram_id FROM moderators")
        return cursor.fetchall()
    
    def delete_moderator(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM moderators WHERE telegram_id = ?''',(telegram_id,))
        self.conn.commit()

class Zayavki_driverDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS zayavki
                        (id INTEGER PRIMARY KEY, telegram_id INT, name TEXT, car TEXT, car_number TEXT, latitude REAL, longitude REAL, location TEXT, status TEXT, ban INT, phone TEXT, category TEXT, username)''')
        self.conn.commit()
    
    def add_zayavka(self, telegram_id, name, car, car_number, latitude, longitude, location, phone, category, username):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO zayavki (telegram_id, name, car, car_number, latitude, longitude, location, status, ban, phone, category, username) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (telegram_id, name, car, car_number, latitude, longitude, location, 'active', 0, phone, category, username))
        self.conn.commit()
    
    def get_zayavka(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT telegram_id, name, car, car_number, latitude, longitude, location, phone, category, username FROM zayavki WHERE telegram_id = ?",(telegram_id,))
        return cursor.fetchone()
    
    def delete_zayavka(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM zayavki WHERE telegram_id = ?''',(telegram_id,))
        self.conn.commit()

class Temp_refDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS temp_ref
                        (telegram_id INT, referal INT)''')
        self.conn.commit()
    
    def add_temp_ref(self, telegram_id, referal):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO temp_ref (telegram_id, referal) VALUES (?, ?)''', (telegram_id, referal,))
        self.conn.commit()
    
    def get_temp_ref(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT referal FROM temp_ref WHERE telegram_id = ?",(telegram_id,))
        return cursor.fetchone()[0]
    
    def delete_temp_ref(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM temp_ref WHERE telegram_id = ?''',(telegram_id,))
        self.conn.commit()

class Order_Taxi_DB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self._create_table()
    
    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders_taxi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            destination TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            driver_latitude REAL NOT NULL,
            driver_longitude REAL NOT NULL,
            pickup_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            clients_count INTEGER NOT NULL DEFAULT 0,
            client_ids TEXT NOT NULL DEFAULT '[]',
            message_ids TEXT NOT NULL DEFAULT '[]',
            bonus INTEGER NOT NULL DEFAULT 0
        )
        ''')
        self.conn.commit()
    
    def create_order(self,driver_id,destination,latitude,longitude,driver_latitude,driver_longitude,pickup_time,sits, bonus):
        with sqlite3.connect('database/data.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO orders_taxi (driver_id,destination,latitude,longitude,driver_latitude,driver_longitude,pickup_time,sits,bonus) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (driver_id,destination,latitude,longitude,driver_latitude,driver_longitude,pickup_time,sits,bonus,))
            conn.commit()

    def get_available_orders_for_client(self, client_latitude, client_longitude, radius=0.01):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM orders_taxi 
            WHERE ABS(driver_latitude - ?) < ? AND ABS(driver_longitude - ?) < ? AND status = 'available'
        ''', (client_latitude, radius * 2, client_longitude, radius * 2))
        count = cursor.fetchall()

        if not count:
            cursor.execute('''
                SELECT * FROM orders_taxi 
                WHERE driver_latitude BETWEEN ? AND ? AND driver_longitude BETWEEN ? AND ? AND status = 'available'
            ''', (client_latitude - radius, client_latitude + radius, client_longitude - radius, client_longitude + radius))
            count = cursor.fetchall()
        
        return count
    
    def join_order(self, order_id, client_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT clients_count, client_ids, message_ids, status, sits FROM orders_taxi WHERE id = ?', (order_id,))
        result = cursor.fetchone()
        clients_count = result[0]
        client_ids = json.loads(result[1])
        message_ids = json.loads(result[2])
        status = result[3]
        sits = result[4]
        
        if status == 'available' and clients_count < 4 and client_id not in client_ids:
            client_ids.append(client_id)
            clients_count += 1
            cursor.execute('UPDATE orders_taxi SET clients_count = ?, client_ids = ? WHERE id = ?', (clients_count, json.dumps(client_ids), order_id))
            self.conn.commit()
            return True, clients_count, message_ids, client_ids, sits
        else:
            return False, clients_count, message_ids, client_ids, sits
        
    def finish_order(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE orders_taxi SET status = ? WHERE id = ?",('completed',order_id,))
        self.conn.commit()
    
    def get_order(self, driver_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders_taxi WHERE driver_id = ? AND status = 'available'", (driver_id,))
        return cursor.fetchone()
    
    def get_order_by_id(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders_taxi WHERE id = ? AND status = 'available'", (order_id,))
        return cursor.fetchone()
    
    def if_driver_in_taxi_order(self, driver_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT driver_id FROM orders_taxi WHERE driver_id = ? AND status = 'available' ", (driver_id,))
        try:
            id = cursor.fetchone()
            if id[0] == driver_id:
                return True
            else:
                return False
        except:
            return False

    def add_message_id(self, order_id, chat_id, message_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT message_ids FROM orders_taxi WHERE id = ?', (order_id,))
        result = cursor.fetchone()
        message_ids = json.loads(result[0])
        
        message_ids.append({'chat_id': chat_id, 'message_id': message_id})
        cursor.execute('UPDATE orders_taxi SET message_ids = ? WHERE id = ?', (json.dumps(message_ids), order_id,))
        self.conn.commit()
    
    def get_msg_ids(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT message_ids FROM orders_taxi WHERE id = ?', (order_id,))
        return json.loads(cursor.fetchone()[0])
    
    def get_joined_users(self,order_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT client_ids FROM orders_taxi WHERE id = ?', (order_id,))
        result = cursor.fetchone()
        if result:
            return result
        return []
    
    def get_taxi_driver_id(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT driver_id FROM orders_taxi WHERE id = ?', (order_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    
    def finish_order_for_user(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE orders_taxi SET status = ? WHERE id = ?', ('completed', order_id,))
        self.conn.commit()

    def get_sits_and_count_joined(self,order_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT sits, clients_count FROM orders_taxi WHERE id = ?', (order_id,))
        return cursor.fetchone()

class Temp_OrdersTable:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()

    def create_table(self):
        with sqlite3.connect('database/data.db') as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS temp_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        destination TEXT,
                        latitude REAL,
                        longitude REAL,
                        client_latitude REAL,
                        client_longitude REAL,
                        datetime TEXT,
                        bonus INTEGER)''')
            conn.commit()

    def add_order(self, client_id, destination, latitude, longitude, client_latitude, client_longitude, datetime, bonus):
        with sqlite3.connect('database/data.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO temp_orders (client_id, destination, latitude, longitude, client_latitude, client_longitude, datetime, bonus) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (client_id, destination, latitude, longitude, client_latitude, client_longitude, datetime,bonus,))
            conn.commit()

    def get_orders(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM temp_orders")
        orders = c.fetchall()
        return orders
    
    def get_order(self, order_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM temp_orders WHERE id = ?",(order_id,))
        return c.fetchone()
    
    def get_nearby_orders_four(self):
        def are_points_nearr(coord1, coord2, radius=5):
            # Вычисляем расстояние между двумя координатами в километрах
            distance = great_circle(coord1, coord2).km
            return distance <= radius
        cursor = self.conn.cursor()
        cursor.execute("SELECT latitude,longitude,id FROM temp_orders")
        results = cursor.fetchall()
        nearby_ids = []
        if len(results) < 3:
            # Закрываем соединение и возвращаем False, если координат меньше 4
            return False
        # Проверяем каждую координату на расстояние от остальных
        for i, row1 in enumerate(results):
            lat1, lon1, id1 = row1
            coord1 = (lat1, lon1)
            for j, row2 in enumerate(results):
                if i != j:  # Проверяем, чтобы не сравнивать одну координату с собой
                    lat2, lon2, id2 = row2
                    coord2 = (lat2, lon2)
                    if are_points_nearr(coord1, coord2):
                        if id1 not in nearby_ids:
                            nearby_ids.append(id1)
                        if id2 not in nearby_ids:
                            nearby_ids.append(id2)
        if len(nearby_ids) < 3:
            return False
        
        result = nearby_ids.copy()
        nearby_ids.clear()
        return result
    
    def del_order(self,order_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM temp_orders WHERE id = ?',(order_id,))
        self.conn.commit()