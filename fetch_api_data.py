from pokemontcgsdk import Card
from pokemontcgsdk import RestClient

from poke_data import CardData

from dotenv import load_dotenv

import os
import json
import re
import pickle

load_dotenv()
api_key = os.getenv("API_KEY")
RestClient.configure(api_key)


def sort_item(card):
    match = re.match(r'^([A-Za-z]*)(\d+)(.*)', card.number)
    if match:
        prefix = match.group(1)  # Capture any letters or characters before the numeric part
        numeric_part = int(match.group(2))  # Capture the numeric part as an integer
        suffix = match.group(3)  # Capture any characters after the numeric part
        if prefix:
            return 0, prefix, numeric_part, suffix  # Sort by prefix, then numeric part, and finally suffix
        else:
            return 1, '', numeric_part, suffix  # Sort non-prefix cards after prefix cards
    else:
        return 0, '', 0, ''  # Default value if no match is found


def fetch_api(target: list) -> dict:
    card_dict = {set_name: [] for set_name in target}

    with open('data/prices.json', 'r') as file:
        price_dict = json.load(file)

    for set_name in target:
        print(f"Populating cards from \"{set_name}\"")
        cards = Card.where(q=f'set.id:{set_name}')
        sorted_cards = sorted(cards, key=sort_item)
        for card in sorted_cards:
            print(card.name)
            current_card_data = CardData(card, price_dict)
            current_card_data.generate_components()
            card_dict[set_name].append(current_card_data)

    return card_dict


def save_data(card_dict: dict):
    with open('data/api_data.pkl', 'wb') as file:
        pickle.dump(card_dict, file)

    print('Data successfully saved to data/api_data.pkl')


if __name__ == '__main__':
    target_set_list = [
        "base1", "base2", "base3", "base4", "base5", "gym1", "gym2",
        "neo1", "neo2", "neo3", "neo4", "base6",
        "ecard1", "ecard2", "ecard3", "basep"
    ]

    card_data = fetch_api(target_set_list)

    save_data(card_data)
