from flask import Flask, send_file, request, render_template, redirect, url_for

from group import Group
from parcours import Parcours
from generer_ics import generate_ics
from generer_ics import build_ics_link
import datetime
from flask_scss import Scss

app = Flask(__name__)
Scss(app, static_dir='static/css', asset_dir='assets')


@app.route('/')
def hello_world():
    formation = request.args.get('formation')
    year = request.args.get('year')
    filtre_yes = request.args.getlist('filtre_yes')
    filtre_no = request.args.getlist('filtre_no')

    if formation is None:
        return redirect('/choisir-parcours', code=302)

    if len(filtre_yes) == 0:
        filtre_yes = None

    if len(filtre_no) == 0:
        filtre_no = None

    if year is None:
        year = datetime.datetime.now().year
    year = int(year)

    return send_file(generate_ics(formation, year, filtre_yes, filtre_no),
                     as_attachment=True,
                     attachment_filename='calendar.ics')


@app.route('/choisir-parcours')
def choose_parcours():
    return render_template('choose_parcours.html', parcours=Parcours.get_all_parcours())


@app.route('/choisir-groupe/<parcours_link>')
def choose_group(parcours_link):
    name = request.args.get('name')
    return render_template('choose_group.html', groups=Group.get_all_groups(parcours_link), name=name)


@app.route('/fichier-ics/<group>')
def ics_link(group):
    print(request)
    return render_template('ics_link.html', group=group, link=build_ics_link(group))


if __name__ == '__main__':
    app.run()
