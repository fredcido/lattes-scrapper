# coding=utf-8

import scrapy

class LattesSpider(scrapy.Spider):
    name = 'lattesspider'
    start_urls = ['http://buscatextual.cnpq.br/buscatextual/visualizacv.do?id=K4706420E7']

    def parse(self, response):
        yield {
            'nome': response.css('h2.nome:first-child::text').extract_first(),
            'bolsista': response.css('h2.nome:nth-of-type(2) span::text').extract_first(),
            'atualizacao': self.get_ultima_atiizacao(response)
        }

    def get_ultima_atiizacao(self, response):
        content = response.css('ul.informacoes-autor li:last-child *::text').extract()
        data = ""
        if len(content) > 1:
            data = content[1].split(" ")[-1]
        return data
