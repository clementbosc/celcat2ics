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
    '#00FF00': 'CONFÉRENCE',
    '#7D4F72': 'COURS/TD',
    '#408080': 'TP',
    '#FFFF80': 'RÉUNION',
    '#8080C0': 'TP NON ENCADRÉ'
}


def color_to_type(color):
    if color in color_to_type_tab:
        return color_to_type_tab[color]

    return None


def utc_to_local(dt):
    local = pytz.timezone("Europe/Paris")
    local_dt = local.localize(dt, is_dst=None)
    return local_dt.astimezone(pytz.utc)


def get_events(link):
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
        match = '[' + m.group(1) + ']'

        events = json.loads(match)

        for event in events:
            # type, name, salle = event_text_parser(event['text'])
            name, salle = event_text_parser(event['text'])

            type = color_to_type(event['backColor'])

            e = {
                'type': type,
                'name': name,
                'salle': salle,
                'end': utc_to_local(parser.parse(event['end'])),
                'start': utc_to_local(parser.parse(event['start'])),
                'color': event['backColor'] if 'backColor' in event else None,
                'id': event['id']
            }

            if event['text'].startswith('Global Event') or type is None:
                continue

            yield e


def event_text_parser(text):
    # regex = r"^(?:\([0-9-:]+\))<br>([A-Z\/ ]+)<br>(?:(?:.{8} - (.+)<br>.+<br>(.+))|(?:.+<br>(.+)<br>(.+)))$"
    regex = r"^(?:(?:.{8} - (.+)<br>.+<br>(.+))|(?:.+<br>(.+)))$"
    m = re.search(regex, text)

    # if m is None:
    #     return None, None, None

    # groups = m.groups()

    # if groups[3] is None or groups[4] is None:
    #     return groups[0], groups[1], groups[2]  # type, name, salle
    #
    # return groups[0], groups[4], groups[3]  # type, name, salle

    if m is None:
        return None, None

    groups = m.groups()

    if groups[2] is None:  # cours classique
        return groups[0], groups[1]  # name, salle

    # évènement
    return "", groups[2]  # name, salle


def get_date(year, day):
    return datetime.datetime(year, 1, 1) + datetime.timedelta(day - 1)


def event_is_present(tab, id):
    for event in tab:
        if event['id'] == id:
            return True
    return False


def get_all_events(year, formation):
    all_events = []

    present = datetime.datetime.now()

    for day in range(1, 365, 15):
        day_date = get_date(year, day)

        if (day_date + datetime.timedelta(days=15)) < present:
            continue

        link = 'https://edt.univ-tlse3.fr/calendar/default.aspx?View=month&Type=group&ResourceName=' + formation + '&Date=' + day_date.strftime(
            '%Y%m%d')

        for e in get_events(link):
            if not event_is_present(all_events, e['id']):
                all_events.append(e)

    return all_events


def date_for_cal(date):
    return date.strftime('%Y%m%dT%H%M%SZ')


def generate_ics(formation, year):
    events = get_all_events(year, formation)
    file = BytesIO()

    file.write("BEGIN:VCALENDAR\n".encode('utf-8'))
    file.write("VERSION:2.0\n".encode('utf-8'))
    file.write("PRODID:-//hacksw/handcal//NONSGML v1.0//EN\n".encode('utf-8'))

    for e in events:
        file.write("BEGIN:VEVENT\n".encode('utf-8'))
        file.write(
            ("UID:" + date_for_cal(datetime.datetime.now()) + "-" + str(uuid.uuid4()) + "@clementbosc.fr\n").encode(
                'utf-8'))
        file.write(("DTSTAMP:" + date_for_cal(datetime.datetime.now()) + "\n").encode('utf-8'))
        file.write(("DTSTART:" + date_for_cal(e['start']) + "\n").encode('utf-8'))
        file.write(("DTEND:" + date_for_cal(e['end']) + "\n").encode('utf-8'))
        file.write(("LOCATION:" + e['salle'] + "\n").encode('utf-8'))
        file.write(("SUMMARY:" + e['type'] + " - " + e['name'] + "\n").encode('utf-8'))
        file.write("FBTYPE:BUSY-UNAVAILABLE\n".encode('utf-8'))
        file.write("END:VEVENT\n".encode('utf-8'))

    file.write("END:VCALENDAR".encode('utf-8'))
    file.seek(0)
    return file


if __name__ == '__main__':
    formation = 'formation_EIINDE_s1_TDA1'
    year = 2018

    generate_ics(formation, year)
