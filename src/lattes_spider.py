# coding=utf-8

import scrapy
import re

ANO_INICIAL=2013
ANO_FINAL=2017

class LattesSpider(scrapy.Spider):
    name = 'lattesspider'
    start_urls = ['http://buscatextual.cnpq.br/buscatextual/visualizacv.do?id=K4706420E7']

    def parse(self, response):
        yield {
            'nome': response.css('h2.nome:first-child::text').extract_first(),
            'bolsista': response.css('h2.nome:nth-of-type(2) span::text').extract_first(),
            'atualizacao': self.get_ultima_atualizacao(response),
            'link': self.get_endereco_lattes(response),
            'data': self.extract_data(response)
        }

    def get_ultima_atualizacao(self, response):
        content = response.css('ul.informacoes-autor li:last-child *::text').extract()
        data = ""
        if len(content) > 1:
            data = content[1].split(" ")[-1]
        return data

    def get_endereco_lattes(self, response):
        content = response.css('ul.informacoes-autor li:first-child *::text').extract()
        url = response.request.url
        if len(content) > 1:
            url = content[1].split(" ")[-1]
        return url

    def extract_data(self, response):
        generic_ones = {
            'CapitulosLivrosPublicados': 'Capítulos de livros publicados',
            'TrabalhosPublicadosAnaisCongresso': 'Trabalhos completos publicados em anais de congressos',
            'TrabalhosPublicadosAnaisCongresso': 'Resumos expandidos publicados em anais de congressos',
            'TrabalhosPublicadosAnaisCongresso': 'Resumos publicados em anais de congressos',
            'ApresentacoesTrabalho': 'Apresentações de Trabalho',
        }

        data = {
            'Artigos completos publicados em periódicos': self.extract_artigos(response),
            'Projetos de pesquisa': self.extract_projetos(response),
        }

        for key, value in generic_ones.iteritems():
            items = self.extract_cita_artigos(response, key)
            data[value] = items

        return data

    def extract_projetos(self, response):
        container = response.css('a[name="ProjetosPesquisa"]').xpath('following-sibling::*[2]')
        children = container.css('.layout-cell-3')
        valid_data = []
        for child in children:
            anos = child.css('b::text').extract_first()
            if anos is None:
                continue
            
            ano_ini = anos.split(" - ")[0]
            ano_fim = anos.split(" - ")[1]
            if ano_fim == "Atual":
                ano_fim = 2018

            if self.validate_year(ano_ini) or self.validate_year(ano_fim):
                data = " ".join(child.xpath('following-sibling::*[1]').css('*::text').extract())
                valid_data.append(data)

        return valid_data


    def extract_cita_artigos(self, response, item):
        cita_artigos = response.css('div.cita-artigos')
        valid_data = []
        for artigo in cita_artigos:
            if len(artigo.css("a[name='%s']" % item).extract()) > 0:
                next_item = artigo.xpath('following-sibling::*[1]')
                while len(next_item) > 0 and len(next_item.xpath("self::div[contains(@class, 'cita-artigos')]").extract()) < 1:
                    content = next_item.css('.layout-cell-pad-5 *::text').extract()
                    text = " ".join(content)
                    if self.validate_year(text):
                        valid_data.append(text)
                    next_item = next_item.xpath('following-sibling::*[1]')
        return valid_data

    def extract_artigos(self, response):
        artigos = response.css('#artigos-completos .artigo-completo .layout-cell-11 .layout-cell-pad-5')
        data = [" ".join(artigo.css('*::text').extract()) for artigo in artigos]
        return self.filter_data(data)
    
    def filter_data(self, data):
        valid_data = []
        for item in data:
            if self.validate_year(item):
                valid_data.append(item)
        return valid_data

    def validate_year(self, text):
        match = re.match(r'.*([1-3][0-9]{3})', text)
        if match is None:
            return False
        ano = int(match.groups()[-1])
        return ano >= ANO_INICIAL and ano <= ANO_FINAL
