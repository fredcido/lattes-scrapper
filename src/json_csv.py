import csv
import os
import json

def transform():
  json_file = os.path.join(os.getcwd(), 'pesquisadores.json')
  with open(json_file) as f:
      data = json.load(f)
  header = None
  rows = []
  for item in data:
      if header is None:
          header = [text.encode('utf-8') for text in list(item['data'].keys())]
      row = [
          item['nome'],
          item['atualizacao'],
          item['link'],
          item['bolsista'],
      ]
      row = [text.encode('utf-8') if text is not None else "N/A" for text in row]
      for title, items in item['data'].iteritems():
          row.append(len(items))
      rows.append(row)

  header = ['Nome', 'Atualizacao', 'Link', 'Bolsista'] + header
  rows = [header] + rows

  with open('data.csv', 'w') as csv_file:
      writer = csv.writer(csv_file) 
      writer.writerows(rows)

  csv_file.close()


if __name__ == '__main__':
    transform()