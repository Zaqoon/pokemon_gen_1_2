import os
import json

from pokemontcgsdk import Card
from pokemontcgsdk import RestClient

from fetch_api_data import sort_item

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')

RestClient.configure(API_KEY)


def get_prices(target) -> dict:
    crd_nmbr = 0
    promo_nmbr = 0
    prices_dict = {}
    for set in target:
        print(f"Populating cards from \"{set}\"")
        cards = Card.where(q=f'set.id:{set}')
        sorted_cards = sorted(cards, key=sort_item)
        for card in sorted_cards:
            if card.rarity is None:
                continue

            try:
                price = card.cardmarket.prices.trendPrice
                converted_price = euro_to_usd(price)
            except AttributeError:
                converted_price = 0.01
            if card.rarity == 'Promo':
                promo_nmbr += 1
                nmbr = promo_nmbr + 64000
            else:
                crd_nmbr += 1
                nmbr = crd_nmbr + 32000
            prices_dict[str(nmbr)] = converted_price
            print(f'{nmbr}: {converted_price}')

    return prices_dict


def euro_to_usd(euro: float) -> float:
    usd = euro * 1.04
    usd = str(round(usd, 2))
    while usd[-1] == '0' or usd[-1] == '.':
        if len(usd) == 1:
            break
        usd = usd[:-1]

    return float(usd)


def write_to_file(price_dict: dict):
    with open('data/prices.json', 'w') as file:
        data = json.dumps(price_dict, indent=4)
        file.write(data)

    print('Price data was successfully saved.')


if __name__ == '__main__':
    target_set_list = [
        "base1", "base2", "base3", "base4", "base5", "gym1", "gym2",
        "neo1", "neo2", "neo3", "neo4", "base6",
        "ecard1", "ecard2", "ecard3", "basep"
    ]

    price_dict = get_prices(target_set_list)

    write_to_file(price_dict)
