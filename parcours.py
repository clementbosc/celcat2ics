import collections
import ssl
import urllib.request

from bs4 import BeautifulSoup


class Parcours:

    def __init__(self, name, link):
        self.name = name
        self.link = link

    @staticmethod
    def get_short_link(link):
        return link.split('/')[-1]

    @staticmethod
    def get_all_parcours(link='https://edt.univ-tlse3.fr/FSI/2018_2019/index.html'):

        parcours = {}
        all_parcours_kind = ['L1', 'L2', 'L3', 'M1', 'M2']

        context = ssl._create_unverified_context()

        with urllib.request.urlopen(link, context=context) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            options = soup.findAll('option')

            for o in options:
                if not o['value'].startswith('http'):
                    continue

                parcours_kind = o.text[:2]
                parcours_kind = 'AUTRES' if parcours_kind not in all_parcours_kind else parcours_kind

                if parcours_kind not in parcours:
                    parcours[parcours_kind] = {}

                parcours[parcours_kind][o.text] = Parcours.get_short_link(o['value'])

        return collections.OrderedDict(sorted(parcours.items()))


if __name__ == '__main__':
    parcours = Parcours.get_all_parcours()
    print(parcours)
