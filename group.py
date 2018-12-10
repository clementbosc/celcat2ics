import ssl
import urllib.request
from urllib import parse

from bs4 import BeautifulSoup


class Group:

    @staticmethod
    def get_ressource_name(link):
        return dict(parse.parse_qsl(parse.urlsplit(link).query))['ResourceName']

    @staticmethod
    def get_all_groups(parcours_link, base_link='https://edt.univ-tlse3.fr/FSI/2018_2019/'):

        groups = {}
        edt_link = '://edt.univ-tlse3.fr'

        context = ssl._create_unverified_context()

        with urllib.request.urlopen(base_link + parcours_link, context=context) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.findAll('a')

            for a in links:
                if a['href'].startswith('http'+edt_link) or a['href'].startswith('https'+edt_link):
                    groups[a.text] = Group.get_ressource_name(a['href'])

        return groups


if __name__ == '__main__':
    print(Group.get_ressource_name(
        'https://edt.univ-tlse3.fr/calendar/default.aspx?View=week&Type=group&ResourceName=formation_EPSF_s1_TDD2'))
