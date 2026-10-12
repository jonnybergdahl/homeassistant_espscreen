"""A plant as a tile (firmware 0.56.0): Home Assistant's own plant (its 2026.10 core: plant/__init__.py, const.py;
frontend: hui-plant-status-card.ts, state_active.ts, color.globals.ts) and Olen's replacement under the same domain
(homeassistant-plant: plant/__init__.py, sensor.py, number.py, const.py), whose readings the flower card shows as bars
(lovelace-flower-card: utils/attributes.ts, constants.ts). The add-on hands the screen one form for both.
"""
import asyncio
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'screen_manager/app'))
import catalogue  # noqa: E402
import core  # noqa: E402
import header_bar  # noqa: E402
import tile_icons  # noqa: E402

HAS_AIOHTTP = importlib.util.find_spec('aiohttp') is not None

GLYPH = tile_icons.GLYPHS


def home_assistant_plant():
    """Home Assistant's own plant: readings as attributes, units by reading, what is wrong as words, no range."""
    return {
        'plant.fern': {'state': 'problem', 'attributes': {
            'friendly_name': 'Fern', 'problem': 'moisture low, conductivity high',
            'sensors': {'moisture': 'sensor.fern_moisture', 'temperature': 'sensor.fern_temperature',
                        'conductivity': 'sensor.fern_conductivity', 'brightness': 'sensor.fern_light', 'battery': 'sensor.fern_battery'},
            'unit_of_measurement_dict': {'moisture': '%', 'temperature': '°C', 'conductivity': 'µS/cm', 'brightness': 'lx', 'battery': '%'},
            'moisture': 12, 'temperature': 21.43, 'conductivity': 3400, 'brightness': 5300, 'battery': 47, 'max_brightness': 5300}},
        'sensor.fern_temperature': {'state': '21.43', 'attributes': {'unit_of_measurement': '°C'}},
    }


def olen_plant():
    """(states, device entries) of Olen's plant as it sets one up: the plant's own state and statuses, and on its device
    a sensor per reading and a min and max number per range (its settings), each with its translation key."""
    states = {
        'plant.monstera': {'state': 'problem', 'attributes': {
            'friendly_name': 'Monstera', 'species': 'Monstera deliciosa', 'moisture_status': 'Low', 'temperature_status': 'ok',
            'conductivity_status': 'ok', 'illuminance_status': 'High', 'humidity_status': None, 'dli_status': 'Previous DLI Low',
            'problems': ['moisture'], 'entity_picture': '/local/monstera.jpg'}},
        'sensor.monstera_soil_moisture': {'state': '14.5', 'attributes': {'unit_of_measurement': '%', 'icon': 'mdi:water'}},
        'sensor.monstera_temperature': {'state': '22.12', 'attributes': {'unit_of_measurement': '°C', 'icon': 'mdi:thermometer'}},
        'sensor.monstera_conductivity': {'state': 'unavailable', 'attributes': {'unit_of_measurement': 'µS/cm', 'icon': 'mdi:spa-outline'}},
        'sensor.monstera_illuminance': {'state': '21000', 'attributes': {'unit_of_measurement': 'lx', 'icon': 'mdi:brightness-6'}},
        'sensor.monstera_dli': {'state': '3.1', 'attributes': {'unit_of_measurement': 'mol/d⋅m²', 'icon': 'mdi:counter'}},
        'number.monstera_min_moisture': {'state': '15', 'attributes': {}},
        'number.monstera_max_moisture': {'state': '60', 'attributes': {}},
        'number.monstera_min_temperature': {'state': '10', 'attributes': {}},
        'number.monstera_max_temperature': {'state': '35', 'attributes': {}},
        'number.monstera_min_conductivity': {'state': '350', 'attributes': {}},
        'number.monstera_max_conductivity': {'state': '2000', 'attributes': {}},
        'number.monstera_min_illuminance': {'state': '800', 'attributes': {}},
        'number.monstera_max_illuminance': {'state': '15000', 'attributes': {}},
        'number.monstera_min_dli': {'state': '6', 'attributes': {}},
        'number.monstera_max_dli': {'state': '18', 'attributes': {}},
        'number.monstera_lux_to_ppfd': {'state': '0.0185', 'attributes': {}},
    }
    keys = {'plant.monstera': None, 'sensor.monstera_soil_moisture': 'moisture', 'sensor.monstera_temperature': 'temperature',
            'sensor.monstera_conductivity': 'conductivity', 'sensor.monstera_illuminance': 'illuminance', 'sensor.monstera_dli': 'dli',
            'number.monstera_lux_to_ppfd': 'lux_to_ppfd'}
    keys.update({eid: eid.split('monstera_')[1] for eid in states if eid.startswith('number.') and 'lux' not in eid})
    device = [{'entity_id': eid, 'platform': 'plant', 'device_id': 'monstera', 'translation_key': key,
               'options': {'sensor': {'suggested_display_precision': 1}} if eid == 'sensor.monstera_temperature' else {}}
              for eid, key in keys.items()]
    return states, device


class TheType(unittest.TestCase):
    def test_a_plant_is_a_tile_from_firmware_0_56_0(self):
        self.assertIn('plant', core.DOMAINS)
        self.assertEqual(catalogue.of_type('plant')['firmware'], '0.56.0')
        self.assertEqual(catalogue.gates({'entity': 'plant.fern'}), [((0, 56, 0), 'type plant')])

    def test_it_has_no_action_and_no_toggle(self):
        entry = catalogue.of_type('plant')
        self.assertEqual(entry.get('controls') or [], [])

    def test_icons_and_colours_are_home_assistants(self):
        self.assertEqual(tile_icons.DEFAULTS['plant'], 'flower')
        self.assertIn('flower', tile_icons.BIG_GLYPHS)
        self.assertEqual(header_bar.DOMAIN_ICONS['plant'], 'flower')
        self.assertEqual(header_bar.accent('plant.a', {'state': 'problem'}), header_bar.RED)
        self.assertIsNone(header_bar.accent('plant.a', {'state': 'ok'}))
        self.assertTrue(header_bar.active('plant.a', {'state': 'problem'}))
        self.assertFalse(header_bar.active('plant.a', {'state': 'ok'}))


class HomeAssistantsPlant(unittest.TestCase):
    def test_the_readings_of_its_plant_status_card(self):
        states = home_assistant_plant()
        extra = core.extras({'entity': 'plant.fern'}, states)
        self.assertEqual(extra['r'], [
            {'i': GLYPH['water-percent'], 'v': '12', 'u': '%', 's': 'l'},
            {'i': GLYPH['thermometer'], 'v': '21.43', 'u': '°C'},
            {'i': GLYPH['white-balance-sunny'], 'v': '5300', 'u': 'lx'},
            {'i': GLYPH['sprout'], 'v': '3400', 'u': 'µS/cm', 's': 'h'},
            {'i': GLYPH['battery-40'], 'v': '47', 'u': '%'},
        ])
        self.assertNotIn('sp', extra)

    def test_a_reading_rounds_as_its_sensor_does(self):
        states = home_assistant_plant()
        entries = {'sensor.fern_temperature': {'options': {'sensor': {'display_precision': 1}}}}
        extra = core.extras({'entity': 'plant.fern'}, states, entries=entries)
        self.assertEqual(extra['r'][1]['v'], '21.4')

    def test_a_reading_it_has_not_had_yet_shows_no_value(self):
        states = home_assistant_plant()
        states['plant.fern']['attributes']['moisture'] = None
        states['plant.fern']['attributes']['problem'] = 'none'
        extra = core.extras({'entity': 'plant.fern'}, states)
        self.assertEqual(extra['r'][0], {'i': GLYPH['water-percent'], 'u': '%'})
        self.assertFalse(any('s' in item for item in extra['r']))


class OlensPlant(unittest.TestCase):
    def test_the_sensors_of_its_device_and_not_its_settings(self):
        states, device = olen_plant()
        related = core.plant_related('plant.monstera', device, states)
        self.assertEqual(related, {'moisture': 'sensor.monstera_soil_moisture', 'temperature': 'sensor.monstera_temperature',
                                   'conductivity': 'sensor.monstera_conductivity', 'illuminance': 'sensor.monstera_illuminance',
                                   'dli': 'sensor.monstera_dli'})

    def test_a_reading_it_has_no_sensor_for_stays_out(self):
        # Olen's plant makes a sensor for every reading and the integration disables those without a sensor of their
        # own (air humidity, CO2, soil temperature, VPD): disabled, they have no state.
        states, device = olen_plant()
        device.append({'entity_id': 'sensor.monstera_air_humidity', 'platform': 'plant', 'translation_key': 'humidity',
                       'disabled_by': 'integration'})
        self.assertNotIn('humidity', core.plant_related('plant.monstera', device, states))
        states['sensor.monstera_air_humidity'] = {'state': 'unavailable', 'attributes': {}}
        device[-1]['disabled_by'] = None
        self.assertEqual(core.plant_related('plant.monstera', device, states)['humidity'], 'sensor.monstera_air_humidity')

    def test_by_its_unique_id_where_the_registry_names_no_key(self):
        states, device = olen_plant()
        # Soil temperature ends like a temperature, and is no temperature of the air.
        states['sensor.monstera_soil_temperature'] = {'state': '19', 'attributes': {'unit_of_measurement': '°C'}}
        device.append({'entity_id': 'sensor.monstera_soil_temperature', 'platform': 'plant', 'translation_key': 'soil_temperature'})
        for item in device:
            unique = {'moisture': 'current-moisture', 'dli': 'dli', 'soil_temperature': 'current-soil-temperature'}.get(item['translation_key'])
            item['translation_key'] = None
            if unique:
                item['unique_id'] = f'01ENTRY-{unique}'
        self.assertEqual(core.plant_related('plant.monstera', device, states),
                         {'moisture': 'sensor.monstera_soil_moisture', 'dli': 'sensor.monstera_dli'})

    def test_its_readings_in_the_flower_cards_order(self):
        states, device = olen_plant()
        entries = {item['entity_id']: item for item in device}
        extra = core.extras({'entity': 'plant.monstera'}, states, device=device, entries=entries)
        self.assertEqual(extra['sp'], 'Monstera deliciosa')
        self.assertEqual(extra['r'], [
            {'i': GLYPH['water'], 'v': '14.5', 'u': '%', 's': 'l'},
            # Olen's spa-outline is not in the screen's font: drawn with Home Assistant's sprout.
            {'i': GLYPH['sprout'], 'u': 'µS/cm'},
            {'i': GLYPH['thermometer'], 'v': '22.1', 'u': '°C'},
            {'i': GLYPH['brightness-6'], 'v': '21000', 'u': 'lx', 's': 'h'},
            # The dot operator the screen's fonts lack, as the middle dot they have.
            {'i': GLYPH['counter'], 'v': '3.1', 'u': 'mol/d·m²', 's': 'l'},
        ])

    def test_the_screen_gets_it_with_the_plants_state(self):
        states, device = olen_plant()
        extra = core.extras({'entity': 'plant.monstera'}, states, device=device)
        message = core.state_message(0, {'entity': 'plant.monstera', 'name': ''}, states, extra)
        self.assertEqual((message['state'], message['name']), ('problem', 'Monstera'))
        self.assertEqual(message['x'], extra)
        self.assertLess(len(core.encode(message)), 1024)



@unittest.skipUnless(HAS_AIOHTTP, 'the manager needs aiohttp')
class TheManager(unittest.TestCase):
    """The path a screen's message takes (Manager.tile_message): Olen's plant needs its device's entries handed in,
    which only some domains get (a card with no readings on the bench, 2026-10-12)."""

    def test_the_tile_message_carries_olens_readings_and_watches_their_sensors(self):
        sys.path.insert(0, str(ROOT / 'tests'))
        import test_scaling
        from manager_fixtures import with_screen_grid
        from server import Manager
        states, device = olen_plant()
        ha = test_scaling.fake_ha(firmware='0.56.0')
        ha.states.update(states)
        ha.registry.extend(device)
        with tempfile.TemporaryDirectory() as folder:
            manager = Manager(with_screen_grid(ha), Path(folder) / 'screens.json')
            tile = {'entity': 'plant.monstera', 'name': '', 'options': {}}
            message = asyncio.run(manager.tile_message(0, tile))
            self.assertEqual(len(message['x']['r']), 5)
            self.assertEqual(message['x']['sp'], 'Monstera deliciosa')
            self.assertIn('sensor.monstera_soil_moisture', manager.related_entities(tile))

    def test_its_photo_is_a_cover_from_its_entity_picture(self):
        # Olen's plant shows OpenPlantbook's picture of its species, or a file in Home Assistant (/local/...): the card
        # asks for it as a cover, and the app fetches it as a person's photo on a map (never a private address).
        sys.path.insert(0, str(ROOT / 'tests'))
        import camera_feed
        import test_scaling
        from manager_fixtures import with_screen_grid
        from server import Manager
        states, device = olen_plant()
        ha = test_scaling.fake_ha(firmware='0.56.0')
        ha.states.update(states)
        ha.registry.extend(device)
        asked = []

        async def entity_picture(picture):
            asked.append(picture)
            return b'picture'
        ha.entity_picture = entity_picture
        with tempfile.TemporaryDirectory() as folder:
            manager = Manager(with_screen_grid(ha), Path(folder) / 'screens.json')
            self.assertTrue(camera_feed.cover_supported('plant.monstera'))
            self.assertEqual(manager.cover_picture('plant.monstera'), '/local/monstera.jpg')
            self.assertEqual(asyncio.run(manager.cover_image('plant.monstera')), b'picture')
            self.assertEqual(asked, ['/local/monstera.jpg'])
            message = asyncio.run(manager.tile_message(0, {'entity': 'plant.monstera', 'name': '', 'options': {}}))
            self.assertEqual(len(message['x']['pic']), 10)
            # A plant without a photo has no mark, and nothing to fetch.
            del ha.states['plant.monstera']['attributes']['entity_picture']
            self.assertEqual(manager.cover_picture('plant.monstera'), '')
            with self.assertRaises(ValueError):
                asyncio.run(manager.cover_image('plant.monstera'))


if __name__ == '__main__':
    unittest.main()
