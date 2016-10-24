# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime, smtplib, json, logging
import smtplib
from codecs import open
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from jinja2 import Environment, PackageLoader

class MoviePipeline(object):
    
    def __init__(self, moviedb_key, gmail_account, gmail_password):
        '''
        The amount of movies is low, so storing it in the local memory won't be a problem.
        I'm planing to move this to mongodb soon.
        It's necessary to store this in the memory beacuse some movies are repeated. 
        A movie being repeated means that it has a function both saturday and sunday
        '''
        self.movies_json = {}
        # mailjet stuff
        self.gmail_account = gmail_account
        self.gmail_password = gmail_password
        # movie db stuff
        self.moviedb_key = moviedb_key
        self.movie_api_url =  'https://api.themoviedb.org/3/search/movie'
        # Change this if you want your overview in another language
        self.language = 'es-US' 
        self.logger = logging.getLogger(__name__)

    def process_item(self, item, spider):
        # We check if the movie has been scrapped before.
        name = item['name'].split(' (')[0] #Removing (ESP) or (SUB)
        if name not in self.movies_json.keys():
            self.movies_json[name] = {
                'url': item['url'],
                'functions':{item['weekday']: item['hours']},
                'overviews':{'Cines unidos': item['overview']}
            }
            movie = self.movies_json[name]

            # We do the preparations to query the moviedb API
            api_request = {'query':name,
                           'api_key': self.moviedb_key,
                           'language':self.language}
            movie_api = requests.get(self.movie_api_url, params=api_request)

            try:
                # If the movie does not exist in the movide db it would not have results 
                # (but it will still have a status code 200)  
                movie_api = movie_api.json()['results'][0]
                             

            except IndexError:
                movie['popularity'] = 'Not found'
                movie['vote_average'] = 'Not found'
                movie['overviews']['Movie db'] = 'Not found'
                self.logger.warning('The movie db api doesn\'t have the movie searched')
            
            else:
                movie['popularity'] = movie_api['popularity']
                movie['vote_average'] = movie_api['vote_average']
                movie['overviews']['Movie db'] = movie_api['overview']
            
        else:
            movie = self.movies_json[name]
            movie['functions'][item['weekday']] = item['hours']


    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            moviedb_key = crawler.settings.get('MOVIEDB_KEY'),
            gmail_account = crawler.settings.get('GMAIL_ACCOUNT'),
            gmail_password = crawler.settings.get('GMAIL_PASSWORD')
        )

    def close_spider(self, spider):
        date = datetime.date.today()
        filename = 'movies-{}-{}-{}.json'.format(date.day,
                                            date.month,
                                            date.year)
        with open(filename, 'w') as f:
            json.dump(self.movies_json, f, indent= 4, ensure_ascii=False)
        
        self.send_emails()

    def send_emails(self):
        # Email creation with jinja2.
        env = Environment(loader=PackageLoader('movie_scrapping', 'templates'))
        # Plain text
        template_plain_text = env.get_template('plain.txt')
        plain_text = template_plain_text.render(data = self.movies_json)

        # Html
        template_html = env.get_template('email.html')
        email_html = template_html.render(data = self.movies_json)

        # Metadata
        subject = 'Lista de peliculas disponibles para este fin de semana'
        recipents = 'julioocz@gmail.com'

        self.smtp_email(subject, email_html, plain_text, recipents)
    
    def smtp_email(self, subject, html, plain, to):
        # Creating message container
        message = MIMEMultipart('alternative')
        message['subject'] = subject
        message['To'] = to
        message['From'] = self.gmail_account
        message.preamble = """
        Tu lector de emails no soporta el formato de nuestro reporte
        """

        # Record the MIME type text/html.
        body_html = MIMEText(html, 'html')

        # Plain text
        body_text = MIMEText(plain, 'plain')

        # attachment
        message.attach(body_text)
        message.attach(body_html)

        # Configuring google smtp server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.gmail_account, self.gmail_password)
        server.send_message(message)
        server.quit()


        
