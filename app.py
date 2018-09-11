from flask import Flask, send_file, request
from main import generate_ics

app = Flask(__name__)


@app.route('/')
def hello_world():
    formation = request.args.get('formation')
    year = int(request.args.get('year'))

    return send_file(generate_ics(formation, year),
                     as_attachment=True,
                     attachment_filename='calendar.ics')


if __name__ == '__main__':
    app.run()
