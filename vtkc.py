import logging
import time
from random import choice
from typing import Dict, Optional

import requests
import toml
from discord_webhook import DiscordEmbed, DiscordWebhook

LOGGING_FORMAT = "[%(asctime)s] %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_FORMAT,
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
)


class Scraper:
    def __init__(self) -> None:
        self.proxy = self.retrieve_proxy()
        self.last: Optional[int]
        self.wait_seconds: int = 10
        self.config: Dict
        self.read_startup_data()

    def read_startup_data(self) -> None:
        with open("data.toml", "r") as f:
            self.config = toml.load(f)

        if last := self.config.get("last_pid"):
            self.last = last + 1

        self.last_item_name = self.config.get("last_item_name", "")
        self.last_item_slug = self.config.get("last_item_slug", "")
        self.webhooks = self.config.get("webhooks", [])

        errors = False
        if not self.last:
            logging.exception("variable last_pid in data.toml is not set")
            errors = True
        if not self.last_item_name:
            logging.exception("variable last_item_name in data.toml is not set")
            errors = True
        if not self.last_item_slug:
            logging.exception("variable last_item_slug in data.toml is not set")
            errors = True
        if not self.webhooks or "" in self.webhooks:
            logging.exception(
                "variable webhooks in data.toml is not set or webhooks are empty strings"
            )
            errors = True

        if errors:
            raise Exception("Invalid setup")

    def save_last_scraped(self) -> None:

        self.config["last_pid"] = self.last
        self.config["last_item_name"] = self.last_item_name
        self.config["last_item_slug"] = self.last_item_slug

        with open("data.toml", "w") as toml_write:
            toml.dump(self.config, toml_write)

    def retrieve_proxy(self) -> Dict[str, str]:
        with open("proxy.txt", "r") as f:
            proxy_list = f.readlines()
            ip, port, usr, pwd = choice(proxy_list).split(":")

            return {"http": f"http://{usr}:{pwd}@{ip}:{port}"}

    def scrape_data(self) -> None:
        while True:
            try:
                resp = requests.get(
                    f"https://www.vitkac.com/product/axGetProductDetail?id={self.last}",
                    proxies=self.proxy,
                )

                if resp.status_code != 200:
                    time.sleep(self.wait_seconds)
                    logging.info("No pid created")
                else:
                    self.check_if_new_item(resp.json())

            except Exception as e:
                logging.error(e)
                self.proxy = self.retrieve_proxy()
                time.sleep(self.wait_seconds)

    def check_if_new_item(self, resp: Dict) -> None:
        item_name = resp["selected_product"]["nazwa"]
        item_slug = resp["selected_product"]["slug"]

        if item_name != self.last_item_name and self.last:
            self.send_webhook(item_name)
            logging.info(
                f"New item found: [Pid: {self.last}] {self.last_item_name[:30]}"
            )

            self.last += 1
            self.last_item_name = item_name
            self.last_item_slug = item_slug
            self.save_last_scraped()

        else:
            time.sleep(10)
            logging.info("No new items")

    def send_webhook(self, item_name: str) -> None:
        for x in self.config.get("webhooks", []):
            webhook = DiscordWebhook(url=x, rate_limit_retry=True)
            embed = DiscordEmbed(
                title="New item",
                description=f"{item_name}, {self.last}",
                color="03b2f8",
            )
            webhook.add_embed(embed)
            webhook.execute()
