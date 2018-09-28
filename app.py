from flask import Flask, send_file, request
from main import generate_ics
import datetime

app = Flask(__name__)


@app.route('/')
def hello_world():
    formation = request.args.get('formation')
    year = int(request.args.get('year'))
    filtre_yes = request.args.getlist('filtre_yes')
    filtre_no = request.args.getlist('filtre_no')

    if len(filtre_yes) == 0:
        filtre_yes = None

    if len(filtre_no) == 0:
        filtre_no = None

    if year is None:
        year = int(datetime.datetime.now().year)

    return send_file(generate_ics(formation, year, filtre_yes, filtre_no),
                     as_attachment=True,
                     attachment_filename='calendar.ics')


if __name__ == '__main__':
    app.run()
