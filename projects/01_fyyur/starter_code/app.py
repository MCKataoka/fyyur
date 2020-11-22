#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    image_link = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String))


class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime())
    # Foreign Keys
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    # relationships
    artist = db.relationship(
        Artist,
        backref=db.backref('shows', cascade='all, delete')
    )
    venue = db.relationship(
        Venue,
        backref=db.backref('shows', cascade='all, delete')
    )


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

    cities = db.session.query(
        Venue.city, Venue.state).group_by('city', 'state').all()

    data = [dict() for x in range(len(cities))]

    current_time = datetime.utcnow()

    for i, city in enumerate(data):
        city['city'] = cities[i][0]
        city['state'] = cities[i][1]
        venues = db.session.query(Venue.id, Venue.name).filter_by(
            city=cities[i][0]).order_by(Venue.name).all()
        city['venues'] = [dict() for x in range(len(venues))]
        for j, venue in enumerate(city['venues']):
            venue['id'] = venues[j][0]
            venue['name'] = venues[j][1]
            up_co = db.session.query(Show).filter(
                Show.start_time > current_time, Show.venue_id == venues[j][0]).all()
            venue['num_upcoming_shows'] = len(up_co)

    print('DATA:', data)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO_STILL: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    error = False
    try:

        search_term = request.form['search_term']
        search = "%{}%".format(search_term)

        posts = Venue.query.filter(Venue.name.ilike(search)).all()
        current_time = datetime.utcnow()

        response = {
            "count": len(posts),
            "data": [dict() for x in range(len(posts))]
        }

        for i, post in enumerate(posts):
            response['data'][i] = post

        for venue in response['data']:
            up_sh = db.session.query(Show).filter(
                Show.start_time > current_time, Show.venue_id == venue.id).all()
            venue.num_upcoming_shows = len(up_sh)

    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        print(error)

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    data = Venue.query.filter_by(id=venue_id).first()
    current_time = datetime.utcnow()

    up_sh = db.session.query(Show).filter(
        Show.start_time > current_time, Show.venue_id == venue_id).all()
    pa_sh = db.session.query(Show).filter(
        Show.start_time < current_time, Show.venue_id == venue_id).all()

    for i, artist in enumerate(up_sh):
        name = db.session.query(
            Artist.name).filter(Artist.id == up_sh[i].artist_id).first()
        artist.artist_name = name[0]
        image_link = db.session.query(
            Artist.image_link).filter(Artist.id == up_sh[i].artist_id).first()
        artist.artist_image_link = image_link[0]

    for i, artist in enumerate(pa_sh):
        name = db.session.query(
            Artist.name).filter(Artist.id == pa_sh[i].artist_id).first()
        artist.artist_name = name[0]
        image_link = db.session.query(
            Artist.image_link).filter(Artist.id == pa_sh[i].artist_id).first()
        artist.artist_image_link = image_link[0]

    data.past_shows = pa_sh
    data.upcoming_shows = up_sh
    data.past_shows_count = len(pa_sh)
    data.upcoming_shows_count = len(up_sh)

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = NewVenue()
    return render_template('forms/new_venue.html', form=form)


@ app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False
    try:

        name = request.get_json()['name']
        address = request.get_json()['address']
        city = request.get_json()['city']
        state = request.get_json()['state']
        phone = request.get_json()['phone']
        genres = request.get_json()['genres']
        facebook_link = request.get_json()['facebook_link']
        website = request.get_json()['website']
        image_link = request.get_json()['image_link']
        venue = Venue(name=name, city=city, state=state, address=address,
                      phone=phone, genres=genres, facebook_link=facebook_link, website=website, image_link=image_link)
        db.session.add(venue)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        print(error)
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@ app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO_STILL: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    data = Artist.query.all()
    # TODO: replace with real data returned from querying the database
    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO_STILL: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    error = False
    try:

        search_term = request.form['search_term']
        search = "%{}%".format(search_term)

        posts = Artist.query.filter(Artist.name.ilike(search)).all()
        current_time = datetime.utcnow()

        response = {
            "count": len(posts),
            "data": [dict() for x in range(len(posts))]
        }

        for i, post in enumerate(posts):
            response['data'][i] = post

        for artist in response['data']:
            up_sh = db.session.query(Show).filter(
                Show.start_time > current_time, Show.artist_id == artist.id).all()
            artist.num_upcoming_shows = len(up_sh)

    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        print(error)

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id

    data = Artist.query.filter_by(id=artist_id).first()
    current_time = datetime.utcnow()

    up_sh = db.session.query(Show).filter(
        Show.start_time > current_time, Show.artist_id == artist_id).all()
    pa_sh = db.session.query(Show).filter(
        Show.start_time < current_time, Show.artist_id == artist_id).all()

    for i, venue in enumerate(up_sh):
        name = db.session.query(
            Venue.name).filter(Venue.id == up_sh[i].venue_id).first()
        venue.venue_name = name[0]
        image_link = db.session.query(
            Venue.image_link).filter(Venue.id == up_sh[i].venue_id).first()
        venue.venue_image_link = image_link[0]

    for i, venue in enumerate(pa_sh):
        name = db.session.query(
            Venue.name).filter(Venue.id == pa_sh[i].venue_id).first()
        venue.venue_name = name[0]
        image_link = db.session.query(
            Venue.image_link).filter(Venue.id == pa_sh[i].venue_id).first()
        venue.venue_image_link = image_link[0]

    data.past_shows = pa_sh
    data.upcoming_shows = up_sh
    data.past_shows_count = len(pa_sh)
    data.upcoming_shows_count = len(up_sh)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()
    print('Artist: ', artist.name)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    error = False
    try:
        artist = Artist.query.get(artist_id)

        artist.name = request.get_json()['name']
        artist.city = request.get_json()['city']
        artist.state = request.get_json()['state']
        artist.phone = request.get_json()['phone']
        artist.genres = request.get_json()['genres']
        artist.facebook_link = request.get_json()['facebook_link']

        db.session.commit()
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        print(error)

    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = Venue.query.filter_by(id=venue_id).first()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.get_json()['name']
        venue.city = request.get_json()['city']
        venue.state = request.get_json()['state']
        venue.phone = request.get_json()['phone']
        venue.genres = request.get_json()['genres']
        venue.facebook_link = request.get_json()['facebook_link']

        db.session.commit()
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        print(error)
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = NewArtist()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False
    try:

        name = request.get_json()['name']
        city = request.get_json()['city']
        state = request.get_json()['state']
        phone = request.get_json()['phone']
        genres = request.get_json()['genres']
        facebook_link = request.get_json()['facebook_link'],
        website = request.get_json()['website']
        image_link = request.get_json()['image_link']
        artist = Artist(name=name, city=city, state=state,
                        phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website)
        db.session.add(artist)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        print(error)
    # on successful db insert, flash success
    flash('Artist ' + request.get_json()['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@ app.route('/shows')
def shows():

    data = Show.query.order_by('start_time').all()

    for show in data:
        artist = Artist.query.join(
            Show, Artist.id == Show.artist_id).filter_by(id=show.id).first()
        venue = Venue.query.join(
            Show, Venue.id == Show.venue_id).filter_by(id=show.id).first()
        show.artist_name = artist.name
        show.artist_image_link = artist.image_link
        show.venue_name = venue.name
        print('Artists Name:', show.artist_name)

    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    error = False
    try:

        artist_id = request.get_json()['artist_id']
        venue_id = request.get_json()['venue_id']
        start_time = request.get_json()['start_time']
        show = Show(artist_id=artist_id, venue_id=venue_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        print(error)
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
