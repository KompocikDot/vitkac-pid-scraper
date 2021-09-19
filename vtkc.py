import requests
from random import choice
import time
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime

class Scraper:
     def __init__(self):
          self.proxy = self.Get_proxy()
          self.webhooks = ["", ""]
          self.last = 1604825
          self.sleeper = 10
          self.Read_last()

     def Read_last(self):
          with open("data.txt", "r") as f:
               data = f.readlines()

          self.last = int(data[0].strip())
          self.last_item_name = data[1].strip()
          self.last_item_slug = data[2].strip()

     def Save_last(self):
          with open("data.txt", "w") as f:
               data = [self.last, self.last_item_name, self.last_item_slug]
               f.writelines(data)

     def Get_proxy(self):
          with open("proxy.txt", "r") as f:
               proxy_list = f.readlines()
               proxy = choice(proxy_list).split(":")

               ip = proxy[0]
               port = proxy[1]
               usr = proxy[2]
               pwd = proxy[3]
               return {"http": f"http://{usr}:{pwd}@{ip}:{port}", "https": f"https://{usr}:{pwd}@{ip}:{port}"}

     def Scrape(self):
          while True:
               try:
                    resp = requests.get(f"https://www.vitkac.com/product/axGetProductDetail?id={self.last}")
                    if resp.status_code != 200:
                         time.sleep(self.sleeper)
                         print(f"{datetime.now()} | No pid created")
                    else:
                         self.Check(resp.json())

               except Exception as e:
                    print(f"{datetime.now()} | ERROR - {e}")
                    self.proxy = self.Get_proxy()
                    time.sleep(self.sleeper)
     

     
     def Check(self, resp):
          nazwa = resp["selected_product"]["nazwa"]
          slug = resp["selected_product"]["slug"]
          pid = self.last

          if nazwa != self.last_item_name:
               self.Webhook(nazwa)
               self.last += 1
               self.last_item_name = nazwa
               self.last_item_slug = slug
               self.Save_last()
               print(f"{datetime.now()} | New item")

          else:
               time.sleep(10)
               print(f"{datetime.now()} | No new items")

     def Webhook(self, nazwa):
          for x in self.webhooks:
               webhook = DiscordWebhook(url=x, rate_limit_retry=True)
               embed = DiscordEmbed(title="New item", description=f"{nazwa}, {self.last}", color='03b2f8')
               webhook.add_embed(embed)
               webhook.execute()

Scraper().Scrape()
