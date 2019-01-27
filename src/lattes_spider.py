# coding=utf-8

import scrapy
import re
import os
import json_csv

ANO_INICIAL = 2013
ANO_FINAL = 2017

FEED_EXPORT_ENCODING = 'utf-8'

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

class LattesSpider(scrapy.Spider):
    name = 'lattesspider'
    file = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    start_urls = [l.strip() for l in open(os.path.join(__location__, 'profiles.txt')).readlines()]

    def closed(self, reason):
        json_csv.transform()

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
            'Capítulos de livros publicados': 'CapitulosLivrosPublicados',
            'Trabalhos completos publicados em anais de congressos': 'TrabalhosPublicadosAnaisCongresso',
            'Resumos expandidos publicados em anais de congressos': 'TrabalhosPublicadosAnaisCongresso',
            'Resumos publicados em anais de congressos': 'TrabalhosPublicadosAnaisCongresso',
            'Apresentações de Trabalho': 'ApresentacoesTrabalho',
        }

        data = {
            'Artigos completos publicados em periódicos': self.extract_artigos(response),
            'Projetos de pesquisa': self.extract_projetos(response, 'ProjetosPesquisa'),
            'Projetos de ensino': self.extract_projetos(response, 'ProjetosExtensao'),
            'Participação em bancas de trabalhos de conclusão': self.extract_participacao(response, 'ParticipacaoBancasTrabalho'),
            'Participação em eventos, congressos, exposições e feiras': self.extract_participacao(response, 'ParticipacaoEventos'),
            'Orientações e supervisões concluídas': self.extract_participacao(response, 'Orientacoesconcluidas'),
        }

        for key, value in generic_ones.iteritems():
            items = self.extract_cita_artigos(response, value, key)
            data[key] = items

        return data

    def extract_participacao(self, response, titulo):
        next_item = response.css('a[name="%s"]' % titulo).xpath('following-sibling::*[1]')
        valid_data = []
        while len(next_item) > 0 and len(next_item.xpath("self::a").extract()) < 1:
            content = self.trata_text(next_item.css('.layout-cell-pad-5 *::text').extract())
            if self.validate_year(content):
                valid_data.append(content)
            next_item = next_item.xpath('following-sibling::*[1]')
        return valid_data

    def extract_projetos(self, response, projeto):
        container = response.css('a[name="%s"]' % projeto).xpath('following-sibling::*[2]')
        children = container.css('.layout-cell-3')
        valid_data = []
        for child in children:
            anos = child.css('b::text').extract_first()
            if anos is None:
                continue
            
            ano_ini = anos.split(" - ")[0]
            ano_fim = anos.split(" - ")[1]
            if ano_fim == "Atual":
                ano_fim = "2018"

            if self.validate_year(ano_ini) or self.validate_year(ano_fim):
                data = self.trata_text(child.xpath('following-sibling::*[1]').css('*::text').extract())
                valid_data.append(data)

        return valid_data


    def extract_cita_artigos(self, response, item, title):
        cita_artigos = response.css('div.cita-artigos')
        valid_data = []
        for artigo in cita_artigos:
            if len(artigo.css("a[name='%s']" % item).extract()) > 0:
                titulo = self.trata_text(artigo.css('b *::text').extract())
                if title.decode('utf-8') not in titulo:
                    continue
                next_item = artigo.xpath('following-sibling::*[1]')
                while len(next_item) > 0 and len(next_item.xpath("self::div[contains(@class, 'cita-artigos')]").extract()) < 1:
                    text = self.trata_text(next_item.css('.layout-cell-pad-5 *::text').extract())
                    if self.validate_year(text):
                        valid_data.append(text)
                    next_item = next_item.xpath('following-sibling::*[1]')
        return valid_data

    def extract_artigos(self, response):
        artigos = response.css('#artigos-completos .artigo-completo .layout-cell-11 .layout-cell-pad-5')
        data = [self.trata_text(artigo.css('*::text').extract()) for artigo in artigos]
        return self.filter_data(data)
    
    def filter_data(self, data):
        valid_data = []
        for item in data:
            if self.validate_year(item):
                valid_data.append(item)
        return valid_data

    def validate_year(self, text):
        match = re.search(r'.*([1-3][0-9]{3})', text)
        if match is None:
            return False
        ano = int(match.groups()[-1])
        return ano >= ANO_INICIAL and ano <= ANO_FINAL

    def trata_text(self, texto):
        if isinstance(texto, list):
            texto = " ".join(texto)
        return texto.strip()
