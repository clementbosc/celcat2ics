import urllib.request
from bs4 import BeautifulSoup
import re
import json
import datetime
from dateutil import parser
import pytz
import ssl
import uuid
from io import BytesIO

color_to_type_tab = {
	'#00FF00': 'CONFERENCE',
	'#7D4F72': 'COURS/TD',
	'#408080': 'TP',
	'#FFFF80': 'REUNION / RENCONTRE',
	'#8080C0': 'TP NON ENCADRÉ',
	'#8080FF': 'COURS',
	'#FF8080': 'TD',
	'#FCFAAB': 'SOUTIEN',
	'#FF8000': 'EXAMEN'
}


def color_to_type(color):
	if color in color_to_type_tab:
		return color_to_type_tab[color]

	return ''


def get_summary(event):
	notes = ''
	summary = event['type']

	if event['name'] != '':
		summary += ' - ' + event['name']
		if event['details'] is not None:
			notes = event['details']
	elif event['details'] is not None:
		summary += ' - ' + event['details']

	return summary, notes


def utc_to_local(dt):
	local = pytz.timezone("Europe/Paris")
	local_dt = local.localize(dt, is_dst=None)
	return local_dt.astimezone(pytz.utc)


def get_events(link):
	print(link)
	context = ssl._create_unverified_context()

	with urllib.request.urlopen(link, context=context) as response:
		html = response.read()
		soup = BeautifulSoup(html, 'html.parser')
		script = soup.findAll('script')
		script = script[-2]

		for s in script:
			js = s
			break

		regex = r"v\.events\.list = \[(.+)\]"
		m = re.search(regex, js)
		if m is None:
			return []
		match = '[' + m.group(1) + ']'

		events = json.loads(match)

		for event in events:
			if event['text'].startswith('Global Event'):
				continue

			type, name, group, salle, details = event_text_parser(event['text'])
			type = color_to_type(event['backColor']) if (type is None and 'backColor' in event) else type
			name = '' if name is None else name
			salle = '' if salle is None else salle
			type = '' if type is None else type
			group = '' if group is None else group

			e = {
				'type': type,
				'name': name,
				'group': group,
				'details': details,
				'salle': salle,
				'end': utc_to_local(parser.parse(event['end'])),
				'start': utc_to_local(parser.parse(event['start'])),
				'color': event['backColor'] if 'backColor' in event else None,
				'id': event['id']
			}

			# if type is None:
			#     continue

			yield e


def event_text_parser(text):
	regex = r"^(?:\([0-9-:]+\)<br>(?P<type>(?:(?!<br>).)*)<br>)?(?P<cours>[A-Z0-9]{8} - (?:(?!<br>).)*<br>)?(?P<group>(?:(?!<br>).)*)<br>(?P<salle>(?:(?!<br>).)*)(?:<br>(?P<complement>(?:(?!<br>).)*))?$"
	m = re.search(regex, text)

	if m is None:
		return None, None, None, None, None

	values = list(m.groupdict().values())
	values[1] = values[1][11:-4] if values[1] is not None else values[1]
	return values


def get_date(year, day):
	return datetime.datetime(year, 1, 1) + datetime.timedelta(day - 1)


def get_range():
	present = datetime.datetime.now()
	days = []
	doy = int(present.strftime('%j'))
	current_year = datetime.datetime.now().year

	for day in range(245, 365, 15):
		days.append(get_date(current_year if doy >= 245 else current_year - 1, day))

	for day in range(1, 245, 15):
		days.append(get_date(current_year if doy <= 245 else current_year + 1, day))

	return days


def event_is_present(tab, id):
	for event in tab:
		if event['id'] == id:
			return True
	return False


def get_all_events(year, formation, type):
	all_events = []
	present = datetime.datetime.now()

	for f_name in formation:

		for day in get_range():

			print(day)

			if (day + datetime.timedelta(days=15)) < present:
				continue

			link = 'https://edt.univ-tlse3.fr/calendar/default.aspx?View=month&Type=' + type + '&ResourceName=' + f_name + '&Date=' + day.strftime(
				'%Y%m%d')

			for e in get_events(link):
				if not event_is_present(all_events, e['id']):
					all_events.append(e)

	return all_events


def date_for_cal(date):
	return date.strftime('%Y%m%dT%H%M%SZ')


def generate_ics(formation, year, type='group', filtre_yes=None, filtre_no=None, filtre_group=None):
	events = get_all_events(year, formation, type)

	if filtre_yes is not None:
		events = list(filter(lambda x: x['type'] in delete_case(filtre_yes), events))

	if filtre_no is not None:
		events = list(filter(lambda x: x['type'] not in delete_case(filtre_no), events))

	if filtre_group is not None:
		events = list(filter(lambda x: x['group'] in delete_case(filtre_group), events))

	file = BytesIO()

	file.write("BEGIN:VCALENDAR\n".encode('utf-8'))
	file.write("VERSION:2.0\n".encode('utf-8'))
	file.write("PRODID:-//hacksw/handcal//NONSGML v1.0//EN\n".encode('utf-8'))

	for e in events:
		summary, notes = get_summary(e)
		file.write("BEGIN:VEVENT\n".encode('utf-8'))
		file.write(
			("UID:" + date_for_cal(datetime.datetime.now()) + "-" + str(uuid.uuid4()) + "@clementbosc.fr\n").encode(
				'utf-8'))
		file.write(("DTSTAMP:" + date_for_cal(datetime.datetime.now()) + "\n").encode('utf-8'))
		file.write(("DTSTART:" + date_for_cal(e['start']) + "\n").encode('utf-8'))
		file.write(("DTEND:" + date_for_cal(e['end']) + "\n").encode('utf-8'))
		file.write(("LOCATION:" + e['salle'] + "\n").encode('utf-8'))
		file.write(("DESCRIPTION:" + notes + "\n").encode('utf-8'))
		file.write(("SUMMARY:" + summary + "\n").encode('utf-8'))
		file.write("TRANSP:OPAQUE\n".encode('utf-8'))
		file.write("FBTYPE:BUSY-UNAVAILABLE\n".encode('utf-8'))
		file.write("END:VEVENT\n".encode('utf-8'))

	file.write("END:VCALENDAR".encode('utf-8'))
	file.seek(0)
	return file


def delete_case(l):
	return list(map(lambda x: x.upper(), l))


def build_ics_link(ressource_name):
	return '/?formation=' + ressource_name


if __name__ == '__main__':
	formation = 'formation_EIINDE_s1_TDA1'
	year = 2018

	generate_ics(formation, year, 'group', ['TP', 'CONFERENCE'])
