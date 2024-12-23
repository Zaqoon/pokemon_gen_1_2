import os
import json

from pokemontcgsdk import Card
from pokemontcgsdk import RestClient

from api_grab import target_set_list, sort_item

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')

RestClient.configure(API_KEY)


def get_prices(target) -> dict:
    crd_nmbr = 32000
    prices_dict = {}
    for set in target:
        print(f"Populating cards from \"{set}\"")
        cards = Card.where(q=f'set.id:{set}')
        sorted_cards = sorted(cards, key=sort_item)
        for card in sorted_cards:
            prices = card.tcgplayer.prices
            prices_dict[str(crd_nmbr)] = prices
            crd_nmbr += 1

    return prices_dict


def write_to_file(price_dict: dict):
    with open('prices.json', 'w') as file:
        data = json.dumps(price_dict, indent=4)
        file.write(data)


if __name__ == '__main__':
    price_dict = get_prices(target_set_list)
    write_to_file(price_dict)
