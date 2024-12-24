from pokemontcgsdk import Card
from pokemontcgsdk import RestClient

from poke_data import rarity_weights
from poke_data import sets
from poke_data import generations
from poke_data import Card_Data

from dotenv import load_dotenv

import re
import json
import os
import shutil


load_dotenv()
api_key = os.getenv("API_KEY")
RestClient.configure(api_key)

target_set_list = [
    "base1", "base2", "base3", "base4", "base5", "gym1", "gym2",
    "neo1", "neo2", "neo3", "neo4", "base6",
    "ecard1", "ecard2", "ecard3", "basep"
]

card_data = {set_name: [] for set_name in target_set_list}

with open('prices.json', 'r') as file:
    price_dict = json.load(file)


def weight_calculation(rarity_dict: dict, set: str) -> dict:
    card_count = {'Common': 0, 'Rare': 0}
    card_count.update({rarity: 0 for rarity in rarity_dict})
    weight_dict = card_count.copy()
    for card in card_data[set]:  # Count cards in all rarity groups
        if card.rarity in rarity_dict and rarity_dict[card.rarity] > 0:
            card_count[card.rarity] += 1
        elif card.rarity == 'Rare':
            card_count['Rare'] += 1

    base_weight = 100008
    premium_weight = 0

    for rarity in rarity_dict:
        if rarity_dict[rarity] > 0:
            weight = base_weight / rarity_dict[rarity]  # Calculate combined weight of cards in rarity group
            weight_dict[rarity] = weight / card_count[rarity]  # Divide weight among all cards in rarity group

            if rarity in ['Rare Holo', 'Rare Shining', 'Rare Secret']:
                premium_weight += base_weight / rarity_dict[rarity]

    weight_dict['Premium'] = premium_weight
    remaining_weight = base_weight - premium_weight

    if 'Common' in rarity_dict and rarity_dict['Common'] == -1:
        weight_dict['Common'] = remaining_weight
    else:
        weight_dict['Rare'] = remaining_weight

    return weight_dict


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


def populateCard_Data(target):
    crd_nmbr = 32000
    for set in target:
        print(f"Populating cards from \"{set}\"")
        cards = Card.where(q=f'set.id:{set}')
        sorted_cards = sorted(cards, key=sort_item)
        for card in sorted_cards:
            price = price_dict[str(crd_nmbr)]
            current_card_data = Card_Data(card, price)
            current_card_data.generate_components()
            card_data[set].append(current_card_data)
            crd_nmbr += 1


def add_entry(poke_tag, weight_dict):
    newEntry = {"type": "item", "weight": 1, "name": "minecraft:filled_map", "functions": poke_tag[0]}
    if loot_table == "Premium_rare":
        weight = weight_dict[poke_tag[1]]
        try:
            newEntry["weight"] = round(weight)
        except:
            print(f"Error: {card.name} in {set} has weight: {weight}")
    elif loot_table == "Reverse":
        weight = reverse_weight[poke_tag[1]]
        newEntry["weight"] = round(weight)
    elif card.rarity == "Promo" or isinstance(weight_dict, int):
        newEntry["weight"] = weight_dict

    file_dict["pools"][0]["entries"].append(newEntry)


def add_loot_table(set, rarity, weight) -> None:
    newEntry = {"type": "loot_table", "weight": round(weight), "value": f"tcg:{set}/{rarity}"}
    file_dict["pools"][0]["entries"].append(newEntry)


def add_rare_card(set, loot_table, weight) -> None:
    card_dict = {
        "type": "item",
        "weight": round(weight),
        "name": "minecraft:carrot_on_a_stick",
        "functions": [
            {
                "function": "set_components",
                "components": {
                    "minecraft:custom_model_data": 1,
                    "minecraft:custom_data": {
                        f"{set}_{loot_table.lower()}_rare": 1
                    },
                    "minecraft:enchantment_glint_override": True
                }
            },
            {
                "function": "set_name",
                "name": [
                    {
                        "color": "aqua",
                        "italic": False,
                        "text": "Holographic Card"
                    }
                ]
            },
            {
                "function": "set_lore",
                "lore": [
                    {
                        "italic": True,
                        "text": "Right click to reveal card."
                    },
                    {
                        "color": sets[set]['color'],
                        "italic": False,
                        "text": sets[set]['name']
                    }
                ],
                "mode": "append"
            }
        ]
    }
    file_dict["pools"][0]["entries"].append(card_dict)


def reverse_weights(set: str) -> dict:
    rarity_dict = {
        "Rare Holo": 0, "Rare": 0, "Uncommon": 0, "Common": 0,
    }
    weight_dict = rarity_dict.copy()
    for card in card_data[set]:
        if card.rarity in rarity_dict and card.name not in energy_list:
            rarity_dict[card.rarity] += 1
    total_weight = 100800
    total_cards = sum(value for value in rarity_dict.values())

    for rarity in rarity_dict:
        if rarity_dict[rarity] > 0:
            if rarity != "Common":
                weight_dict[rarity] = (total_weight / total_cards) * rarity_dict[rarity]
            else:
                weight_dict[rarity] = total_weight // total_cards

    return weight_dict


def deck_special_cards(type_specific_cards: dict) -> None:
    for loot_table in type_specific_cards:
        print(f"Creating loot table for {loot_table} Holo Cards ...")
        file_directories = ['gen_1/type_rares', 'gen_2/type_rares']
        for directory in file_directories:
            if os.path.exists(directory):
                shutil.rmtree(directory)
            os.makedirs(directory)

        file_dict = {"type": "minecraft:chest", "pools": [{"rolls": 1, "entries": []}]}
        with open(f"{gen}/{loot_table.lower()}.json", "w") as file:
            for card_tag in type_specific_cards[loot_table]:
                weight = card_tag[1]
                add_entry(card_tag, weight)
            file_dict = json.dumps(file_dict, indent=4)
            file.write(file_dict)


if __name__ == "__main__":
    populateCard_Data(target_set_list)  # Populate data

    energy_list = [
        "Fighting Energy", "Fire Energy", "Grass Energy",
        "Lightning Energy", "Psychic Energy", "Water Energy"
    ]
    type_specific_cards = {
        gen: {
            "Grass": [],
            "Fire": [],
            "Water": [],
            "Psychic": [],
            "Fighting": [],
            "Lightning": [],
            "Colorless": [],
            "Darkness": [],
            "Metal": []
        }
        for gen in generations
    }

    for gen in type_specific_cards:
        if os.path.exists(gen):
            shutil.rmtree(gen)
        os.makedirs(gen)

    for set in target_set_list:
        print(f"Creating loot table for {set} ...")
        gen = 'gen_1'
        for generation, set_names in generations.items():
            if set in set_names:
                gen = generation
                break

        os.makedirs(f"{gen}/loot_tables/{set}")

        tag_lines = {
            "Common": [],
            "Uncommon": [],
            "Rare": [],
            "Premium": [],
            "Premium_rare": [],
            "Reverse": [],
            "Reverse_rare": [],
            "Energy": []
        }

        if set == "basep":
            weight = len(card_data[set]) + 90
            file_dict = {"type": "minecraft:chest", "pools": [{"rolls": 1, "entries": []}]}
            with open(f"{gen}/loot_tables/{set}/promos.json", "w") as file:
                for card in card_data[set]:
                    card_object = [card.functions, card.rarity]
                    add_entry(card_object, weight)
                    weight -= 2
                file_dict = json.dumps(file_dict, indent=4)
                file.write(file_dict)
            continue
        else:
            weight_dict = weight_calculation(rarity_weights[set], set)
            reverse_weight = reverse_weights(set)

        for card in card_data[set]:
            card_object = [card.functions, card.rarity]
            if card.rarity in ["Common", "Uncommon", "Rare", "Promo"]:
                tag_lines[card.rarity].append(card_object)
            if card.rarity in ["Rare Holo", "Rare Holo EX", "Rare Holo Star", "Rare Secret"]:
                tag_lines["Premium_rare"].append(card_object)
            if card.rarity in ["Common"] and card.name not in energy_list:
                tag_lines["Reverse"].append(card_object)
            if card.rarity in ["Rare Holo"] and card.name not in energy_list:
                tag_lines["Reverse_rare"].append(card_object)
            if card.name in energy_list:
                tag_lines["Energy"].append(card_object)

            if card.rarity == "Rare Holo" and card.supertype == "Pokémon":
                card_object = [card.functions, sets[set]["weight"]]
                for card_type in card.types:
                    type_specific_cards[gen][card_type].append(card_object)

        for loot_table in tag_lines.keys():
            if len(loot_table) > 0:
                file_dict = {"type": "minecraft:chest", "pools": [{"rolls": 1, "entries": []}]}
                if len(loot_table) > 0:
                    with open(f"{gen}/loot_tables/{set}/{loot_table.lower()}.json",
                              "w") as file:
                        if loot_table != "Reverse":
                            for card_tag in tag_lines[loot_table]:
                                add_entry(card_tag, weight_dict)
                        else:
                            for card_tag in tag_lines["Common"]:
                                if card_tag not in tag_lines["Energy"]:
                                    add_entry(card_tag, weight_dict)
                        if loot_table == "Premium":
                            if weight_dict["Common"] > 0:
                                add_loot_table(set, "common", weight_dict["Common"])
                            if weight_dict["Rare"] > 0:
                                add_loot_table(set, "rare", weight_dict["Rare"])
                            add_rare_card(set, loot_table, weight_dict["Premium"])
                        if loot_table == "Reverse":
                            add_loot_table(set, "uncommon", reverse_weight["Uncommon"])
                            add_loot_table(set, "rare", reverse_weight["Rare"])
                            add_rare_card(set, loot_table, reverse_weight["Rare Holo"])
                        file_dict = json.dumps(file_dict, indent=4)
                        file.write(file_dict)

    # Rares for types in decks
    file_directories = ['gen_1/type_rares', 'gen_2/type_rares']
    for directory in file_directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

    for gen in generations:
        for loot_table in type_specific_cards[gen].keys():
            print(f"Creating loot table for {loot_table} Holo Cards ...")
            file_dict = {"type": "minecraft:chest", "pools": [{"rolls": 1, "entries": []}]}
            with open(f"{gen}/type_rares/{loot_table.lower()}.json", "w") as file:
                for card_tag in type_specific_cards[gen][loot_table]:
                    weight = card_tag[1]
                    add_entry(card_tag, weight)
                file_dict = json.dumps(file_dict, indent=4)
                file.write(file_dict)
