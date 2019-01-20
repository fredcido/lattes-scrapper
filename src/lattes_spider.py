import scrapy

class LattesSpider(scrapy.Spider):
    name = 'lattesspider'
    start_urls = ['http://buscatextual.cnpq.br/buscatextual/visualizacv.do?id=K4706420E7']

    def parse(self, response):
        yield {
            'nome': response.css('h2.nome:first-child::text').extract_first(),
            'bolsista': response.css('h2.nome::text')[1].extract(),
        }
