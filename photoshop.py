import win32com.client
import win32com.client.dynamic
import os
from poke_data import Card_Data
from poke_data import attack_cost_tag_line

from pokemontcgsdk import Card
from pokemontcgsdk import RestClient

from dotenv import load_dotenv

import photoshop as ps
from photoshop import Session

import re

import requests
import keyboard
import comtypes.client

load_dotenv()
RestClient.configure('API_KEY')

gen1 = ["base1", "base2", "base3", "base4", "base5", "gym1", "gym2", "basep", "neo1", "neo2", "neo3", "neo4", "base6"]
gen2 = ["ecard1", "ecard2", "ecard3"]

targetSetList = ["ex1", "ex2", "ex3", "np", "ex4", "ex5", "ex6", "ex7", "ex8", "ex9", "ex10", "ex11", "ex12", "ex13", "ex14", "ex15", "ex16"]
# targetSetList = ["ex1"]
allCard_Data = {"ex1": [], "ex2": [], "ex3": [], "np": [], "ex4": [], "ex5": [], "ex6": [], "ex7": [], "ex8": [], "ex9": [], "ex10": [], "ex11": [], "ex12": [], "ex13": [], "ex14": [], "ex15": [], "ex16": []}


psApp = win32com.client.Dispatch("Photoshop.Application")

folderDirectory = "C:/Users/Andreas/Documents/pokemon_card_templates/"
typeDictionary = {"Psychic": "psychic.psd", "Water": "water.psd", "Colorless": "colorless.psd", "Fire": "fire.psd", "Fighting": "fighting.psd", "Lightning": "lightning.psd", "Grass": "grass.psd", "Metal": "metal.psd", "Darkness": "darkness.psd"}
keywords = ["Blaine's ", "Brock's ", "Erika's ", "Lt. Surge's ", "Misty's ", "Rocket's ", "Sabrina's ", "Giovanni's ", "Koga's ", "Shining ",
            "Team Aqua's ", "Team Magma's ", "Holon's", "Dark "]
ex_pokemon = ["Magmar", "Mewtwo", "Magcargo", "Muk", "Moltres", "Milotic", "Mew"]


def splitTrainer(card_name, keywords):
    for keyword in keywords:
        if card_name.startswith(keyword):
            prefix = keyword
            suffix = card_name[len(keyword):].strip()  # Remove the matched keyword from the card name
            return prefix, suffix
    return None, None


def number_name(number, name):
    name = name.replace(" \u2605", "")
    number = number.replace("?", "QM")
    number = number.replace("!", "EM")
    
    return number, name


def deleteLayer(layerName):
    doc = psApp.ActiveDocument
    try:
        layer = doc.ArtLayers[layerName]
        layer.Delete()
    except KeyError:
        print(f"Layer '{layerName}' does not exist.")
    except Exception as e:
        print(f"An error occurred while deleting layer '{layerName}': {e}")


def moveAfter(move, target):
    doc = psApp.ActiveDocument
    layer = doc.ArtLayers[move]
    target_layer = doc.ArtLayers[target]
    layer.MoveAfter(target_layer)


def type_selection():
    damage2 = doc.ArtLayers["Damage2"]
    duo_type_string = None
    if len(card.types) == 1:
        type_string = card.types[0] + "Layer"
        layer = doc.ArtLayers[type_string]
        layer.MoveAfter(damage2)
    if len(card.types) == 2:
        if "Darkness" in card.types and "Metal" in card.types:
            if card.setName == "Team Rocket Returns":
                type_string = card.types[0] + "Layer"
                duo_type_string = "MetalDarkness"
            elif card.setName == "Delta Species":
                type_string = card.types[1] + "Layer"
                duo_type_string = "DarknessMetal"
            else:
                type_string = card.types[1] + "Layer"
                duo_type_string = "DarknessMetal"
        else:
            type_string = card.types[1] + "Layer"
        layer = doc.ArtLayers[type_string]
        layer.MoveAfter(damage2)
        if duo_type_string is None:
            duo_type_string = card.types[0] + card.types[1]
        duo_type_layer = doc.ArtLayers[duo_type_string]
        duo_type_layer.MoveAfter(damage2)


def nameLayer():
    doc = psApp.Application.ActiveDocument
    extraExtra = 0
    extra = 0
    if card.supertype == "Pokémon":
        name = card.name
        extra = 59
        extraExtra = 66
        max_length = 70

        for item in keywords:
            match = re.search(item, name)
            if match:
                name = name.replace(item, "")
                break
        ex = re.search(" ex", name)
        star = re.search(" \u2605", name)
        delta_species = re.search(" δ", name)
        if ex:
            name = name.replace(" ex", "")
            extra -= 9
            extraExtra -= 9
            max_length -= 9
        if star:
            name = name.replace(" \u2605", "")
            extra -= 11
            extraExtra -= 11
            max_length -= 11
        if delta_species:
            name = name.replace(" δ", "")
        else:
            deleteLayer("Delta_Species")
        
        name_split = name.split()
        if "Castform" in name_split:
            name = "Castform"

        if len(card.types) > 1:
            card_type = card.types[1]
        else:
            card_type = card.types[0]

        #if card.name.startswith("Dark"):
        #    nameDarkLayer = doc.ArtLayers["NameDark"]
        #    nameDarkLayerItem = nameDarkLayer.TextItem
        #    nameDarkLayerItem.contents = name
        #    deleteLayer("Name2")
        #    deleteLayer("NameSmall")
        #   nameDarkLayer.Name = "Name"
        #    width = nameDarkLayer.Bounds[2] - nameDarkLayer.Bounds[0]
        #    if width > extra:
        #        type_string = card_type + "Extra"
        #        moveAfter(type_string, "Damage2")
        #    if width > extraExtra:
        #        type_string = type_string + "Extra"
        #        moveAfter(type_string, "Damage2")
        #        extraExtra = 100
        #    if width > max_length:
        #        nameDarkLayerItem.size = 9
        
        
        deleteLayer("NameDark")
        nameLayer = doc.ArtLayers["Name2"]
        nameLayerItem = nameLayer.TextItem
        nameLayerItem.contents = name
        width = nameLayer.Bounds[2] - nameLayer.Bounds[0]

        if width > max_length:
            deleteLayer("Name2")
            nameLayer = doc.ArtLayers["NameSmall"]
            nameLayerItem = nameLayer.TextItem
            nameLayerItem.contents = name
            nameLayer.Name = "Name"
            width = nameLayer.Bounds[2] - nameLayer.Bounds[0]
        else:
            deleteLayer("NameSmall")
            nameLayer.Name = "Name"

        if width > extra:
            type_string = card_type + "Extra"
            moveAfter(type_string, "Damage2")
            extra = 100
        if width > extraExtra:
            type_string = type_string + "Extra"
            moveAfter(type_string, "Damage2")
            extraExtra = 100

        if star:
            star_layer = doc.ArtLayers["Star"]
            star_layer.Translate(width - 6, 0)
            moveAfter("Star", "Damage2")
        ex_layers = ["ex", "ex2"]
        if ex:
            if name in ex_pokemon:
                ex_width = 5
            else:
                ex_width = 6
            for ex_layer in ex_layers:
                layer = doc.ArtLayers[ex_layer]
                layer.Translate(width - ex_width, 0)

        else:
            for layer in ex_layers:
                deleteLayer(layer)
                    
                
    if card.supertype == "Trainer":
        mediumLength = 117
        doc = psApp.Application.ActiveDocument
        nameLayer = doc.ArtLayers["Name1"]
        nameLayerItem = nameLayer.TextItem
        nameLayerItem.contents = card.name
        width = nameLayer.Bounds[2] - nameLayer.Bounds[0]
        if width > mediumLength:
            name2Layer = doc.ArtLayers["Name2"]
            name2LayerItem = name2Layer.TextItem
            name2LayerItem.contents = card.name
            deleteLayer("Name1")
            width = name2Layer.Bounds[2] - name2Layer.Bounds[0]
            name = card.name.split()
            while width > mediumLength:
                if len(name) == 1:
                    name[-1] = name[-1][:-3]
                else:
                    name.pop()
                name2LayerItem.contents = ' '.join(name) + " ..."
                width = name2Layer.Bounds[2] - name2Layer.Bounds[0]
        else:
            deleteLayer("Name2")
    if extra == 100:
        extraExtra = True
    elif extraExtra == 100:
        extraExtra = True
    else:
        extraExtra = False
    
    return extraExtra


def hpLayer(extraExtra):
    doc = psApp.Application.ActiveDocument
    if card.hp is not None and card.supertype == "Pokémon":
        if extraExtra is True and int(card.hp) > 95:
            deleteLayer("HP")
            hpLayer = doc.ArtLayers["HPsmall"]
            hpLayer.Name = "HP"
        else:
            deleteLayer("HPsmall")
        hp_layer = doc.ArtLayers["HP"]
        hp_layer_item = hp_layer.TextItem
        hp_layer_item.contents = str(card.hp) + " HP"
    if card.hp is None and card.supertype == "Trainer":
        deleteLayer("HP")


def attackLayers():
    if card.attacks is None:
        deleteLayer("Attack1")
        deleteLayer("Attack2")
        deleteLayer("Damage1")
        deleteLayer("Damage2")
    else:
        damage_pattern = r'(\d+)'
        num_attacks_with_damage_above_zero = sum(1 for attack in card.attacks if (int(re.search(damage_pattern, attack.damage).group()) if attack.damage else 0) > 0)
        if len(card.attacks) == 1:
            attack = card.attacks[0]
            attack_text_and_damage(attack, 3)
            energy_cost(attack, 3)
            deleteLayer("Attack2")
            deleteLayer("Damage2")
        elif num_attacks_with_damage_above_zero > 1:
            if num_attacks_with_damage_above_zero > 1:
                attack = card.attacks[-1]
                attack_text_and_damage(attack, 2)
                energy_cost(attack, 2)

                if num_attacks_with_damage_above_zero > 1:
                    for attack in card.attacks:
                        if attack.damage != "":
                            attack_text_and_damage(attack, 1)
                            energy_cost(attack, 1)
                            break
                else:
                    attack = card.attacks[0]
                    attack_text_and_damage(attack, 1)
                    energy_cost(attack, 1)

        elif num_attacks_with_damage_above_zero < 1:
            attack = card.attacks[-1]
            attack_text_and_damage(attack, 2)
            energy_cost(attack, 2)
            attack = card.attacks[0]
            attack_text_and_damage(attack, 1)
            energy_cost(attack, 1)
        elif len(card.attacks) > 1:
            attack = card.attacks[0]
            attack_text_and_damage(attack, 1)
            energy_cost(attack, 1)
            attack = card.attacks[-1]
            attack_text_and_damage(attack, 2)
            energy_cost(attack, 2)


def attack_text_and_damage(attack, num):
    if num == 3:
        num = 1
        move = True
    else:
        move = False
    doc = psApp.Application.ActiveDocument
    attack_string = "Attack" + str(num)
    damage_string = "Damage" + str(num)
    attack_layer = doc.ArtLayers[attack_string]
    attack_layer_item = attack_layer.TextItem
    attack_layer_item.contents = attack.name
    width = attack_layer.Bounds[2] - attack_layer.Bounds[0]
    stripped_name = attack.name.split()
    if width > 67:
        while width > 67 + 9:
            if len(stripped_name) == 1:
                stripped_name[-1] = stripped_name[-1][:-3]
            else:
                stripped_name.pop()
            attack_layer_item = attack_layer.TextItem
            attack_layer_item.contents = ' '.join(stripped_name) + " ..."
            width = attack_layer.Bounds[2] - attack_layer.Bounds[0]
            

    damage_layer = doc.ArtLayers[damage_string]
    damage_layer_item = damage_layer.TextItem
    damage_layer_item.contents = attack.damage
    if move:
        attack_layer.Translate(0, 7)
        damage_layer.Translate(0, 7)
    move = False


def energy_cost(attack, num):
    if num == 3:
        num = 1
        move = True
    else:
        move = False
    pokemon_type = card.types[0]
    if "Darkness" in card.types and "Metal" in card.types:
        if card.setName == "Team Rocket Returns":
            pokemon_type = card.types[1]
        elif card.setName == "Delta Species":
            pokemon_type = card.types[0]
        else:
            pokemon_type = card.types[0]
    doc = psApp.Application.ActiveDocument
    damage1 = doc.ArtLayers["Damage1"]
    for i, energy in enumerate(attack.cost):
        energy_string = str(num) + energy + str(i+1)
        energy_layer = doc.ArtLayers[energy_string]
        energy_layer.MoveAfter(damage1)
        if move:
            energy_layer.Translate(0, 7)
    attack_cost_and_energy = attack_cost_tag_line(attack)
    # energy_background = "Attack" + str(num) + attack_cost_and_energy[1]
    energy_background = "Attack" + str(num) + pokemon_type
    layer = doc.ArtLayers[energy_background]
    layer.MoveAfter(damage1)
    if move:
        layer.Translate(0, 7)
    move = False


def resistanceLayer():
    doc = psApp.Application.ActiveDocument
    damage2 = doc.ArtLayers["Damage2"]
    if card.resistance is not None:
        resistance_type1 = card.resistance[0].type + "Resistance1"
        if len(card.resistance) > 1:
            resistance_type2 = card.resistance[1].type + "Resistance2"
            layer2 = doc.ArtLayers[resistance_type2]
            layer2.MoveAfter(damage2)
        layer = doc.ArtLayers[resistance_type1] 
        layer.MoveAfter(damage2)


def weaknessLayer():
    doc = psApp.Application.ActiveDocument
    damage2 = doc.ArtLayers["Damage2"]
    if card.weakness is not None:
        weakness_type1 = card.weakness[0].type + "Weakness1"
        if len(card.weakness) > 1:
            weakness_type2 = card.weakness[1].type + "Weakness2"
            layer2 = doc.ArtLayers[weakness_type2]
            layer2.MoveAfter(damage2)
        layer = doc.ArtLayers[weakness_type1] 
        layer.MoveAfter(damage2)


def retreatCostLayer():
    doc = psApp.Application.ActiveDocument
    damage2 = doc.ArtLayers["Damage2"]
    if card.convertedRetreatCost is not None:
        for i in range(1, card.convertedRetreatCost + 1):
            swap = "Swap" + str(i)
            layer = doc.ArtLayers[swap]
            layer.MoveAfter(damage2)


def rarity():
    doc = psApp.Application.ActiveDocument
    if card.rarity == 'Rare Holo Star':
        card_rarity = "Rare Shining"
    else:
        card_rarity = card.rarity
    if card.supertype == "Pokémon":
        if len(card.types) == 1 and card.types[0] == "Lightning" and card_rarity in ["Rare", "Rare Holo", "Rare Shining"]:
            card_rarity += card.types[0]
    if card.supertype == "Trainer":
        moveAfter(card_rarity, "Subtype")
    else:
        damage2 = doc.ArtLayers["Damage2"]
        layer = doc.ArtLayers[card_rarity]
        layer.MoveAfter(damage2)
    if card.rarity == "Promo":
        layer = doc.ArtLayers["Promo"]
        layer_item = layer.TextItem
        layer_item.contents = card.number


def trainer_subtype():
    doc = psApp.Application.ActiveDocument
    try:
        if card.subtypes is not None:
            if card.subtypes[0] == "Pokémon Tool":
                subtype = "Tool"
            elif card.subtypes[0] in ["Technical Machine", "Rocket's Secret Machine"]:
                subtype = "Trainer"
            else:
                subtype = card.subtypes[0]
            subtype_layer = doc.ArtLayers["Subtype"]
            subtype_layer_item = subtype_layer.TextItem
            subtype_layer_item.contents = str(subtype.upper())
    except:
        print(f"Failed to find subtype!")


def downloadImages():
    for setName in targetSetList:
        for card in allCard_Data[setName]:
            if card.name not in ["Fire Energy", "Fighting Energy", "Grass Energy", "Water Energy", "Psychic Energy", "Lightning Energy"]:
                if key.lower() == "r":
                    number, name = number_name(card.number, card.name)
                    card_path = f"C:/Users/Andreas/Documents/pokemon_card_templates/cropped/{setName}/{number} {name}.png"
                    if os.path.exists(card_path):
                        continue
                if card.rarity != "":
                    directory = f"C:/Users/Andreas/Documents/pokemon_card_templates/downloaded/{setName}"
                    outputPath = f"C:/Users/Andreas/Documents/pokemon_card_templates/cropped/{setName}"
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    if not os.path.exists(outputPath):
                        os.makedirs(outputPath)
                    imageURL = card.images['large']
                    number, name = number_name(card.number, card.name)
                    fileName = f"{number} {name}.png"
                    fileName = f"{number} {name}.png"
                    savePath = directory + "/" + fileName
                    response = requests.get(imageURL)
                    if response.status_code == 200:
                        with open(savePath, "wb") as file:
                            file.write(response.content)
                        print("Image downloaded successfully!")
                    else:
                        print("Failed to download image.")
                    imagePath = rf"C:/Users/Andreas/Documents/pokemon_card_templates/downloaded/{setName}/{number} {name}.png"
                    doc = psApp.Open(imagePath)
                    if card.setName != "ex3":
                        width_height = [doc.Width, doc.Height]
                        if not width_height == [400, 550]:
                            doc.ResizeImage(400, 550)
                    if card.supertype == "Pokémon":
                        if setName  == "ex3":
                            doc.Crop([67, 107, 667, 474]) #Left, Top, Right, Bottom
                        elif setName  == "ex6":
                            doc.Crop([38, 58, 363, 254]) #Left, Top, Right, Bottom
                        else:
                            doc.Crop([33, 55, 366, 253]) #Left, Top, Right, Bottom
                        if card.subtypes != "Basic":
                            if card.subtypes != "Baby":
                                psApp.DoAction('spot_healing_evolution', 'pokemon_gen3')
                                print("Performing spot healing...")
                        print("Perform spot healing along the edges and press \'Enter\'.")
                        keyboard.wait('Enter')
                        doc.ResizeImage(112, 69)
                    if card.supertype == "Trainer":
                        doc.Crop([39, 81, 359, 265])
                        print("Perform spot healing along the edges and press \'Enter\'.")
                        keyboard.wait('Enter')
                        doc.ResizeImage(120, 70)
                    if card.supertype == "Energy" and card.rarity != "":
                        if card.name in ["Darkness Energy", "Metal Energy"]:
                            doc.Crop([14, 86, 385, 376])
                        else:
                            doc.Crop([14, 70, 385, 360])
                        doc.ResizeImage(120, 94)
                    outputPath = rf"C:/Users/Andreas/Documents/pokemon_card_templates/cropped/{setName}/{number} {name}.png"
                    options = win32com.client.Dispatch("Photoshop.PNGSaveOptions")
                    doc.SaveAs(outputPath, options)
                    doc.Close(2)

          
def insertImages():
    number, name = number_name(card.number, card.name)
    directory = f"C:/Users/Andreas/Documents/pokemon_card_templates/cropped/{setName}/{number} {name}.png"
    doc = psApp.Open(directory)
    try:
        backgroundLayer = doc.BackgroundLayer
        backgroundLayer.IsBackgroundLayer = False
        layer = doc.ArtLayers["Layer 0"]
    except:
        layer = doc.ArtLayers["Layer 1"]
    layer.Copy()
    doc.Close(2)
    doc = psApp.ActiveDocument
    doc.Paste()
    layer = doc.ArtLayers["Layer 1"]
    if card.supertype == "Pokémon":
        name = doc.ArtLayers["Name"]
        layer.MoveAfter(name)
        layer.Translate(0,-9)
    if card.supertype == "Trainer":
        layer.Translate(0,18)
    if card.supertype == "Energy":
        layer.Translate(0,12)


def save_card():
    output = rf"C:/Users/Andreas/Documents/pokemon_card_templates/finished files/{setName}"
    if not os.path.exists(output):
        os.makedirs(output)
    number, name = number_name(card.number, card.name)
    outputFile = rf"{output}/{number} {name}.png"
    app = comtypes.client.CreateObject('Photoshop.Application')
    doc = app.activeDocument
    optionPNG = comtypes.client.CreateObject('Photoshop.PNGSaveOptions')
    optionPNG.quality = 12
    doc.saveAs(outputFile, optionPNG, True)
    doc.Close(2)
    print(f"Card {card.number}/{card.printedTotal} {card.name} was sucessfully saved.")


def zoom():
    return None
    psApp.DoAction('zoom', 'Default Actions')


def sortItem(card):
    match = re.match(r'^([A-Za-z]*)(\d+)(.*)', card.number)
    if match:
        prefix = match.group(1)  # Capture any letters or characters before the numeric part
        numeric_part = int(match.group(2))  # Capture the numeric part as an integer
        suffix = match.group(3)  # Capture any characters after the numeric part
        if prefix:
            return (0, prefix, numeric_part, suffix)  # Sort by prefix, then numeric part, and finally suffix
        else:
            return (1, '', numeric_part, suffix)  # Sort non-prefix cards after prefix cards
    else:
        return (0, '', 0, '')  # Default value if no match is found


def populateCard_Data():
    for set in targetSetList:
        print(f"Populating cards from \"{set}\"")
        cards = Card.where(q=f'set.id:{set}')
        sorted_cards = sorted(cards, key=sortItem)
        for card in sorted_cards:
            currCard_Data = Card_Data(card)
            currCard_Data.generateLoreList()
            currCard_Data.generateNameLoreDict()
            allCard_Data[set].append(currCard_Data)
      

print("Do you wish to download images? Type \'Y\' for Yes or \'N\' for No. Press \'R\' to only make non existing cards.")
key = keyboard.read_key()
if key.lower() == "y":
    print("Downloading images...")
    downloadImages()
elif key.lower() == "r":
    print("Resuming from the last saved image.")
    downloadImages()
elif key.lower() != "y":
    print("Proceeding without downloading images...")


populateCard_Data()  


for setName in targetSetList:
    print(f"Searching through {setName} ...")
    set_number = setName.replace("ex", "")
    try:
        if int(set_number) < 9:
            continue
    except:
        continue
    for card in allCard_Data[setName]:
        if key.lower() == "r":
            number, name = number_name(card.number, card.name)
            card_path = f"C:/Users/Andreas/Documents/pokemon_card_templates/finished files/{setName}/{number} {name}.png"
            if os.path.exists(card_path):
                    continue
        if card.supertype == "Pokémon":
            if card.types is not None and card.types[0] in typeDictionary:
                path = rf"C:/Users/Andreas/Documents/pokemon_card_templates/gen3/gen3_prototype.psd"
                doc = psApp.Open(path)
                zoom()
                type_selection()
                extraExtra = nameLayer()
                hpLayer(extraExtra)
                resistanceLayer()
                weaknessLayer()
                retreatCostLayer()
                rarity()
                attackLayers()
                insertImages()
                save_card()
        if card.supertype == "Trainer":
            psApp.Open(f"C:/Users/Andreas/Documents/pokemon_card_templates/gen3/trainer.psd")
            zoom()
            extraExtra = nameLayer()
            hpLayer(extraExtra=False)
            trainer_subtype()
            rarity()
            insertImages()
            save_card()
        if card.supertype == "Energy":
            if card.name in ["Fire Energy", "Fighting Energy", "Grass Energy", "Water Energy", "Psychic Energy", "Lightning Energy"]:
                continue
            psApp.Open(f"C:/Users/Andreas/Documents/pokemon_card_templates/gen3/energy.psd")
            zoom()
            insertImages()
            save_card()