import json
import os

SAVE_FILE = "delta_save.json"

def load_game():
    if not os.path.exists(SAVE_FILE):
        return {'crystals': 0, 'unlocked_units': ['soldier', 'flame', 'sniper', 'mine']}
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'crystals' not in data: data['crystals'] = 0
            if 'unlocked_units' not in data: data['unlocked_units'] = ['soldier', 'flame', 'sniper', 'mine']
            return data
    except:
        return {'crystals': 0, 'unlocked_units': ['soldier', 'flame', 'sniper', 'mine']}

def save_game(crystals, unlocked_units):
    data = {'crystals': crystals, 'unlocked_units': unlocked_units}
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
