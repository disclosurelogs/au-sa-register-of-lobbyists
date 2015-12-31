import pdfquery
import scraperwiki
from bs4 import BeautifulSoup
import StringIO
#from pdfquery.cache import FileCache
import re

base_url = "http://dpc.sa.gov.au"
html = scraperwiki.scrape("http://www.dpc.sa.gov.au/lobbyist-who-register")
soup = BeautifulSoup(html, "html5lib")
lobbys = []
for tr in soup.tbody:
    lobby = {}
    lobby['trading_name'] = tr.find_all('td')[0].text.split("|")[0].strip()
    lobby['business_name'] = tr.find_all('td')[1].text.strip() or lobby['trading_name']
    lobby['last_updated'] = tr.find_all('td')[2].text.strip()
    for a in tr.find_all('a'):
        if 'PDF' in a.text:
            url = a.get('href')
            if url.startswith('/sites'):
                url = base_url + url
            lobby['pdf_url'] = url
    lobbys.append(lobby)
# lobbys = [{'trading_name':'xxx','business_name':'yyy', 'last_updated':'1/1/2016', 'pdf_url':'fff'}]
listpart = re.compile('\. (.*)')
clientlistpart = re.compile('(\d\.|\.|)(.*)')
numberre = re.compile('\d')
clientnumberre = re.compile('\d(\.| )')
page_width = 595.32
page_height = 841.92
for lobby in lobbys:
    if True:
        print lobby["pdf_url"]
        binary = StringIO.StringIO(scraperwiki.scrape(lobby["pdf_url"]))
        # binary = open('test.pdf')
        pdf = pdfquery.PDFQuery(binary)#, parse_tree_cacher=FileCache("/tmp/"))
        pdf.load()
        #pdf.tree.write("test2.xml", pretty_print=True, encoding="utf-8")

        business_entity_name = lobby['business_name']
        last_updated = lobby['last_updated']
        trading_name = lobby['trading_name']
        if pdf.pq('LTTextBoxHorizontal:contains(".B.N")'):
            abn_x = float(pdf.pq('LTTextBoxHorizontal:contains(".B.N")').attr('x1'))
            abn_y = float(pdf.pq('LTTextBoxHorizontal:contains(".B.N")').attr('y0'))

        if pdf.pq('LTTextBoxHorizontal:contains(".C.N")'):
            abn_x = float(pdf.pq('LTTextBoxHorizontal:contains(".C.N")').attr('x1'))
            abn_y = float(pdf.pq('LTTextBoxHorizontal:contains(".C.N")').attr('y0'))
        abn = pdf.pq(
            'LTTextBoxHorizontal:in_bbox("%s, %s, %s, %s")' % (abn_x, abn_y, page_width, abn_y + 15))\
            .text().replace(' ','').strip()

        scraperwiki.sqlite.save(unique_keys=["abn", "business_name"],
                                data={'business_name': business_entity_name,
                                      'abn': abn,
                                      'last_updated': last_updated,
                                      'trading_name': trading_name,
                                      },
                                table_name="lobbyist_firms")
        owners = pdf.pq(':in_bbox("%s, %s, %s, %s")' % (0, float(
            pdf.pq('LTTextBoxHorizontal:contains("etails of all employees undertaking lobbying activities")').attr(
                'y0')) + 10, page_width, float(
            pdf.pq('LTTextBoxHorizontal:contains("Australian Securities and Investments Commission")').attr('y1')) - 1))
        for owner in owners:
            if owner.text and '.' in owner.text:
                name = listpart.findall(owner.text)[0].strip()
                if name and name != 'Please note that, where relevant, this information should match the details':
                    scraperwiki.sqlite.save(unique_keys=["lobbyist_firm_abn", "name"],
                                            data={'name': name, 'lobbyist_firm_name': business_entity_name,
                                                  'lobbyist_firm_abn': abn},
                                            table_name="lobbyist_firm_owners")

        employees = pdf.pq(':in_bbox("%s, %s, %s, %s")' % (
        0, pdf.pq('LTTextBoxHorizontal:contains("lient Details")').attr('y1'), page_width,
        pdf.pq('LTTextBoxHorizontal:contains("etails of all employees undertaking lobbying activities")').attr('y0')))
        for employee in employees:
            if employee.text and '.' in employee.text:
                for part in numberre.split(employee.text):
                    for name in listpart.findall(part):
                        name = name.strip()
                        if name:
                            scraperwiki.sqlite.save(unique_keys=["lobbyist_firm_abn", "name"],
                                                    data={'name': name, 'lobbyist_firm_name': business_entity_name,
                                                          'lobbyist_firm_abn': abn},
                                                    table_name="lobbyists")

        clients = pdf.pq(':in_bbox("%s, %s, %s, %s")' % (
        0, pdf.pq('LTTextBoxHorizontal:contains("y completing this form")').attr('y1'), page_width, pdf.pq(
            'LTTextBoxHorizontal:contains("lease provide the names of the organisations (or individuals) that are your clients")').attr(
            'y0'))
                         )
        for client in clients:
            if client.text:
                name = clientlistpart.findall(client.text)[0][1].strip()
                name = clientnumberre.sub('', clientnumberre.sub('',name))
                if name:
                    scraperwiki.sqlite.save(unique_keys=["lobbyist_firm_abn", "name"],
                                            data={'name': name, 'lobbyist_firm_name': business_entity_name,
                                                  'lobbyist_firm_abn': abn},
                                            table_name="lobbyist_clients")
        if pdf.pq('LTPage[page_index="1"] LTTextBoxHorizontal:contains("y completing this form")').attr('y1'):
            clients = pdf.pq('LTPage[page_index="1"] :in_bbox("%s, %s, %s, %s")' % (
            0, pdf.pq('LTPage[page_index="1"] LTTextBoxHorizontal:contains("y completing this form")').attr('y1'),
            page_width, page_height))
            for client in clients:
                if client.text and '.' in client.text:
                    name = clientlistpart.findall(client.text)[0][1].strip()
                    name = clientnumberre.sub('', clientnumberre.sub('',name))
                    if name:
                        scraperwiki.sqlite.save(unique_keys=["lobbyist_firm_abn", "name"],
                                                data={'name': name, 'lobbyist_firm_name': business_entity_name,
                                                      'lobbyist_firm_abn': abn},
                                                table_name="lobbyist_clients")
