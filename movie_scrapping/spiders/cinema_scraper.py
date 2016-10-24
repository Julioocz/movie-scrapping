import datetime


import scrapy
from movie_scrapping.items import MovieScrappingItem
import smtplib

class CinemaSpider(scrapy.Spider):
    """
    This spider crawl the movie title and presentation hours from the cinesunidos pages.
    This spider is suposed to run every friday, getting the movies names and hours for the saturday
    for me to see with my girlfiend ;)
    """
    name = "cinema"
    
    # Movies schudle are stored in a webpage for a particular movie theather for a eachday
    # We create a date for the starting url.
    # This is suposed to run the friday, so days + 1 = saturday
    date = datetime.date.today() + datetime.timedelta(days=1)
    url = "http://www.cinesunidos.com/Home/SearchTheater/Puerto%20La%20Cruz/1019/{}/{}"
    start_urls = [
        url.format(date.day, date.month)
    ]

    def parse(self, response):
        movies = response.css('li')
        weekday = self.date.strftime("%A")
        
        for movie in movies:
            name = movie.css('.peli a::text').extract_first()
            hours = movie.css('.hora a::text').extract()
            relative_url = movie.css('.peli a::attr(href)').extract_first()
            real_url = response.urljoin(relative_url)
            item = MovieScrappingItem()
            item['name'] = name
            item['hours'] = hours
            item['weekday'] = weekday
            item['url'] = real_url
            #We get the specific overview from the movie theather
            request = scrapy.Request(real_url, self.parse_specific_movie, dont_filter=True)
            request.meta['item'] = item
            yield request
            
        #adding the sunday too
        self.date = self.date + datetime.timedelta(days=1)
        next_page = self.url.format(self.date.day, self.date.month)
        if (datetime.date.today() + datetime.timedelta(days=2) >= self.date): #We stop at sunday
            yield scrapy.Request(next_page, self.parse)
        
    def parse_specific_movie(self, response):
        item = response.meta['item']
        item['overview'] = response.css('.texto_det_peli p::text').extract_first()
        yield item

        
        
        