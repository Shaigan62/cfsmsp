from flask import Flask, request

from cfsmsp_spider import CfsmspSpider

app = Flask(__name__)

@app.route('/')
def cfsmsp():
    tax_no = request.args['tax_no']
    reference_no = request.args['reference_no']
    cfsmsp_crawler = CfsmspSpider(tax_no=tax_no, reference_no=reference_no)
    record = cfsmsp_crawler.start_request()
    
    return record

if __name__ == '__main__':
    app.run()
