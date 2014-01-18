import datetime
import numpy
import operator
import os


DATA_DIRECTORY = 'data'
OUTPUT_DIRECTORY = 'output'

WINDOWS = {
    "1w": 5, 
    "2w": 10, 
    "1m": 20, 
    "3m": 60
}

NUM_STOCKS = 4


def load_symbols():
    symbols = {}

    for root, dirs, files in os.walk(DATA_DIRECTORY):
        for name in files:
            fname = os.path.join(root, name)
            print 'Reading ' + fname

            stocks_file = open(fname, 'r')

            for line in stocks_file:
                tokens = line.rstrip('\r\n').split(',')

                if tokens[0] not in symbols:
                    symbols[tokens[0]] = []

                if tokens[6] == "0":
                    continue

                eod = {}
                eod['date'] = datetime.datetime.strptime(tokens[1], "%Y%m%d")
                eod['value'] = float(tokens[5])

                symbols[tokens[0]].append(eod)

    for s in symbols:
        symbols[s] = sorted(symbols[s], key=operator.itemgetter('date'))

    return symbols


def get_values(eods, date, window):
    values = []

    for eod in reversed(eods):
        if eod['date'] <= date:
            values.insert(0, eod['value'])

            if len(values) == window:
                return values

    return None


def simulate(symbols, date):
    sim_results = {}

    for window_name, window_interval in WINDOWS.items():
        for name, eods in symbols.items():
            values = get_values(eods, date, window_interval)

            if values is None:
                continue

            xi = numpy.arange(0, window_interval)
            A = numpy.array([xi, numpy.ones(window_interval)])
            w = numpy.linalg.lstsq(A.T, values)[0]

            volatility = 0.0
            for i in range(window_interval):
                y = w[0] * xi[i] + w[1]
                volatility += abs((y - values[i]) / values[i])

            volatility /= window_interval

            if name not in sim_results:
                sim_results[name] = {
                    'eod': values[-1]
                }

            sim_results[name][window_name] = w[0]
            # sim_results[name][window_name] = w[0] / volatility

        # print str(date) + ', ' + name + ', ' + str(len(values)) + ' eods, score ' + str(w[0] / volatility) + ' w ' + str(w) + ', volatility ' + str(volatility)

    # for name in sorted(symbols_magic, key=symbols_magic.get):
    #     print str(date) + ', ' + name + ', ' + str(symbols_magic[name])
    return sim_results


def avg_portfolio_score(portfolio, sim_results):
    avg_score = 0.0
    for name in portfolio:
        avg_score += sim_results[name]['score']
    
    return avg_score / len(portfolio)


def min_portfolio_stock(portfolio, sim_results):
    min_score = None
    min_name = None
    for name in portfolio:
        if min_score is None or min_score > sim_results[name]['score']:
            min_score = sim_results[name]['score']
            min_name = name
    
    return min_name


if __name__ == '__main__':
    symbols = load_symbols()
    portfolio = {}

    start_date = datetime.datetime(2013, 5, 20);

    while True:
        print 'Day ' + str(start_date)

        sim_results = simulate(symbols, start_date)

        csv = open(os.path.join(OUTPUT_DIRECTORY, str(start_date) + '.csv'), 'w')

        csv.write('name,1w,2w,1m,3m\n')

        for name, scores in sim_results.items():
            csv.write(name 
                + ',' + str(scores.get('1w', 0))
                + ',' + str(scores.get('2w', 0))
                + ',' + str(scores.get('1m', 0))
                + ',' + str(scores.get('3m', 0)) + '\n')

        csv.close()

        sim_sorted = sorted(sim_results.items(), key=lambda (k, v): v['score'], reverse=True)

        avg_score = 0.0
        for sim in sim_sorted:
            avg_score += sim[1]['score']

        avg_score /= len(sim_sorted)

        print 'AVG SCORE ' + str(avg_score)

        for name in portfolio:
            print "IN PORTFOLIO " + name + ', score ' + str(sim_results[name]['score']) + ', diff ' + str((sim_results[name]['eod'] - portfolio[name]['buy_price']) / portfolio[name]['buy_price'] * 100)

        for i in range(NUM_STOCKS):
            print "TOP " + sim_sorted[i][0] + ', score ' + str(sim_sorted[i][1]['score']) + ', eod ' + str(sim_sorted[i][1]['eod'])

        for i in range(NUM_STOCKS):
            if sim_sorted[i][0] in portfolio:
                continue

            if len(portfolio) < NUM_STOCKS:
                portfolio[sim_sorted[i][0]] = {
                    'buy_price': sim_sorted[i][1]['eod']
                }

                print 'BUY ' + sim_sorted[i][0] + ', score ' + str(sim_sorted[i][1]['score']) + ', price ' + str(sim_sorted[i][1]['eod'])

            if sim_sorted[i][1]['score'] > avg_portfolio_score(portfolio, sim_results):
                portfolio[sim_sorted[i][0]] = {
                    'buy_price': sim_sorted[i][1]['eod']
                }

                print 'BUY ' + sim_sorted[i][0] + ', score ' + str(sim_sorted[i][1]['score']) + ', price ' + str(sim_sorted[i][1]['eod'])

                min_stock = min_portfolio_stock(portfolio, sim_results)

                print 'SELL ' + min_stock + ', score ' + str(sim_results[min_stock]['score']) + ', price ' + str(sim_results[min_stock]['eod'])

                del portfolio[min_stock]

        start_date += datetime.timedelta(days=1)
