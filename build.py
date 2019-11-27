import requests
from slpp import slpp as lua
import html
from datetime import datetime, timezone


url = 'https://raw.githubusercontent.com/WFCD/warframe-items/development/data/json/All.json'
backup = 'https://warframe.fandom.com/wiki/Module:Weapons/data?action=edit'

print('Loading WF item data...')

data = requests.get(url).json()

print('parsing backup')

bkup = requests.get(backup).text
bkup = bkup.split('WeaponData =')[1].split('return WeaponData')[0].strip()
backup = {}


for k, v in lua.decode(bkup)['Weapons'].items():
	key = html.unescape(k).lower()
	backup[key] = v

print('Parsing data...')

weapons = [i for i in data if 'disposition' in i and 'type' in i]

stats = {}

for w in weapons:
	for k, v in w.items():
		if k not in stats:
			stats[k] = set()
		try:
			stats[k].add(v)
		except TypeError:
			pass

print('Scanned unique stats:')

for s in stats:
	print(s, end=' - ')
	print(all(s in w for w in weapons))


for o in weapons:
	# Some of the API data is missing valid DPS numbers, so correct them using the wiki.
	if o['damagePerSecond'] <= 1 or o['totalDamage'] <= 20:
		if o['name'].lower() not in backup.keys():
			raise Exception('No backup found: %s' % o['name'])
		else:
			bk = backup[o['name'].lower()]
			dmg = 0
			for at in ['NormalAttack', 'AreaAttack', 'ChargeAttack']:
				if at not in bk:
					continue
				print(o['name'], bk[at])
				dmg = 0
				for k, v in bk[at]['Damage'].items():
					dmg += v
				dmg = round(dmg, 2)
				rate = o['fireRate']
				if 'FireRate' in bk[at]:
					rate = bk[at]['FireRate']
				o['totalDamage'] = dmg
				o['fireRate'] = rate
				o['damagePerSecond'] = round(rate*dmg)
				break

ordered = sorted(weapons, key=lambda x: (x['disposition'], x['damagePerSecond'], len(x['name'])), reverse=True)

with open('Rivens.md', 'w') as out:
	out.write('# Warframe Dispositions\n\n')
	for x in range(max(t['disposition'] for t in ordered), 0, -1):
		out.write('## Disposition %s\n\n' % x)
		out.write('''|Weapon | Type | Total DPS | Trigger | Hit Damage | Fire Rate| Magazine|\n--- | --- | --- | --- | --- | --- | ---\n''')
		for o in filter(lambda y: y['disposition'] == x, ordered):
			out.write('[%s](%s)|%s|%s|%s|%s|%s|%s\n' %
					  (o['name'], o['wikiaUrl'], o['type'] or 'Unknown', round(o['damagePerSecond']), o['trigger'], o['totalDamage'], round(o['fireRate'], 2), o['magazineSize']) )
		out.write('\n\n')
	out.write('__Generated on:__ %s UTC' % datetime.now(timezone.utc).strftime("%Y/%m/%d, %H:%M:%S"))

print('Built weapon table.')
