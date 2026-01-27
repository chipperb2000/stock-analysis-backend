#!/usr/bin/env python3
"""
Automated Stock Scanner
Runs via GitHub Actions every weekday at 5 AM
Fetches data from Railway backend and saves results
"""

import requests
import json
import os
from datetime import datetime

# Your Railway backend URL
API_URL = os.environ.get('API_URL', 'https://stock-analysis-backend-production-52ea.up.railway.app')

# S&P 500 + Russell 1000 stocks (top 1000 by market cap)
SP500_STOCKS = [
    # Mega Cap (Top 100)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'LLY', 'V',
    'UNH', 'JPM', 'XOM', 'MA', 'JNJ', 'PG', 'AVGO', 'HD', 'CVX', 'ABBV',
    'MRK', 'COST', 'ADBE', 'WMT', 'CRM', 'KO', 'NFLX', 'PEP', 'TMO', 'ORCL',
    'BAC', 'ACN', 'AMD', 'CSCO', 'MCD', 'DIS', 'ABT', 'WFC', 'GE', 'QCOM',
    'INTU', 'VZ', 'IBM', 'CMCSA', 'TXN', 'CAT', 'AMGN', 'PM', 'HON', 'UNP',
    'LOW', 'NKE', 'BA', 'GS', 'UPS', 'ELV', 'RTX', 'SBUX', 'LMT', 'SPGI',
    'T', 'BLK', 'DE', 'AXP', 'BKNG', 'MS', 'MDT', 'GILD', 'PLD', 'ADI',
    'MDLZ', 'SYK', 'ISRG', 'CI', 'VRTX', 'C', 'NOW', 'MMC', 'REGN', 'ZTS',
    'SO', 'DUK', 'PGR', 'CB', 'EOG', 'BMY', 'CME', 'MO', 'SLB', 'TGT',
    'HUM', 'USB', 'PYPL', 'LRCX', 'SCHW', 'COP', 'ADP', 'BDX', 'TJX', 'AMAT',
    
    # Large Cap (101-300)
    'TMUS', 'PNC', 'FI', 'BSX', 'PANW', 'ICE', 'MU', 'ETN', 'GD', 'AON',
    'MCO', 'INTC', 'APH', 'ITW', 'KLAC', 'CSX', 'SHW', 'CL', 'SNPS', 'CMG',
    'CDNS', 'MSI', 'WM', 'NOC', 'MAR', 'MMM', 'APD', 'CARR', 'AJG', 'TDG',
    'NSC', 'EQIX', 'ECL', 'ORLY', 'AZO', 'SRE', 'HCA', 'GM', 'ADSK', 'TT',
    'PSA', 'FCX', 'NXPI', 'ABNB', 'ROP', 'SPG', 'PCAR', 'JCI', 'AMP', 'AFL',
    'FTNT', 'BK', 'MET', 'TRV', 'AIG', 'ALL', 'MCHP', 'F', 'RSG', 'FDX',
    'HLT', 'MNST', 'NEM', 'PAYX', 'O', 'SYY', 'ROST', 'DHI', 'MSCI', 'KMB',
    'PRU', 'AEP', 'CPRT', 'YUM', 'DLR', 'AMT', 'CCI', 'GIS', 'TEL', 'CTVA',
    'KMI', 'PSX', 'WELL', 'DHR', 'DD', 'BKR', 'CBRE', 'IQV', 'ILMN', 'KHC',
    'CTSH', 'EW', 'FAST', 'BIIB', 'EA', 'GLW', 'HES', 'ROK', 'VRSK', 'KEYS',
    
    # Mid Cap (301-500)
    'ODFL', 'CEG', 'IDXX', 'HPQ', 'ED', 'VMC', 'CTAS', 'MLM', 'XEL', 'RMD',
    'EXC', 'WMB', 'MTD', 'CDW', 'OTIS', 'DOW', 'ACGL', 'LHX', 'AWK', 'PPG',
    'A', 'STZ', 'FTV', 'EXR', 'AVB', 'STE', 'EIX', 'VICI', 'GWW', 'WTW',
    'MPWR', 'ANSS', 'DXCM', 'CHD', 'TROW', 'IR', 'BAX', 'PCG', 'APTV', 'SBAC',
    'LVS', 'WEC', 'DTE', 'ARE', 'VTR', 'OMC', 'HPE', 'PEG', 'PWR', 'WST',
    'LEN', 'K', 'STT', 'MTB', 'GPN', 'EQR', 'MAA', 'ESS', 'VLO', 'FIS',
    'WAB', 'HIG', 'ENPH', 'ZBH', 'DFS', 'FITB', 'BALL', 'CNC', 'TYL', 'LYB',
    'TDY', 'HBAN', 'PPL', 'NTRS', 'CSGP', 'ETR', 'TTWO', 'VLTO', 'FE', 'TSN',
    'LDOS', 'WY', 'AEE', 'PKI', 'CNP', 'COF', 'DRI', 'WAT', 'DAL', 'EBAY',
    'CAH', 'EXPD', 'CLX', 'TFX', 'WBD', 'INVH', 'CFG', 'RF', 'SYF', 'UAL',
    
    # Small Cap (501-700)
    'KEY', 'TRGP', 'IFF', 'BRO', 'HOLX', 'AMCR', 'HUBB', 'EXPE', 'SWKS', 'TXT',
    'MKC', 'CBOE', 'NVR', 'MOH', 'NTAP', 'J', 'EFX', 'IP', 'ATO', 'PHM',
    'WDC', 'BLDR', 'CINF', 'LUV', 'DGX', 'CMS', 'STLD', 'STX', 'JBHT', 'AKAM',
    'CAG', 'FANG', 'LH', 'ALGN', 'SWK', 'NRG', 'L', 'PODD', 'LNT', 'GPC',
    'ZBRA', 'NDSN', 'POOL', 'HST', 'JKHY', 'CPT', 'CHRW', 'LKQ', 'TECH', 'MAS',
    'EVRG', 'PFG', 'CTLT', 'BBY', 'UDR', 'FDS', 'FFIV', 'PTC', 'INCY', 'BEN',
    'CRL', 'CE', 'GNRC', 'TER', 'REG', 'PAYC', 'AIZ', 'SNA', 'APA', 'MGM',
    'KIM', 'EMN', 'NCLH', 'WRB', 'IEX', 'CPB', 'AOS', 'FOXA', 'DVN', 'MKTX',
    'ALLE', 'IPG', 'UHS', 'BXP', 'HSIC', 'TAP', 'AAL', 'HAS', 'HII', 'BWA',
    'HRL', 'ALB', 'TPR', 'RHI', 'PNW', 'RJF', 'WYNN', 'PEAK', 'SEE', 'CCL',
    
    # Micro Cap (701-1000)
    'FRT', 'DXC', 'WHR', 'JNPR', 'BBWI', 'RL', 'MTCH', 'MHK', 'GL', 'PARA',
    'NI', 'IVZ', 'ZION', 'NWS', 'AIV', 'VFC', 'FMC', 'OGN', 'XRAY', 'AES',
    'BF.B', 'NWSA', 'FOX', 'LNC', 'SJM', 'CMA', 'LW', 'PNR', 'FLT', 'DISH',
    'AAP', 'MOS', 'CF', 'ROL', 'FBHS', 'DVA', 'GPS', 'KMX', 'CZR', 'IRM',
    'WBA', 'NLSN', 'HWM', 'LEG', 'OKE', 'VTRS', 'BKU', 'HSY', 'SWN', 'RRC',
    'NOV', 'HAL', 'EQT', 'CLF', 'COP', 'MUR', 'HFC', 'PXD', 'MRO', 'EOG',
    'DVN', 'FSLR', 'ENPH', 'SEDG', 'RUN', 'NOVA', 'SPWR', 'CSIQ', 'JKS', 'DQ',
    'SOL', 'MAXN', 'ARRY', 'NEE', 'DUK', 'SO', 'D', 'EXC', 'SRE', 'AEP',
    'XEL', 'WEC', 'ES', 'ED', 'FE', 'EIX', 'ETR', 'CNP', 'CMS', 'DTE',
    'PPL', 'AES', 'LNT', 'EVRG', 'NI', 'PNW', 'OGE', 'POR', 'AVA', 'BKH',
    'SJI', 'NWE', 'UTL', 'CPK', 'NJR', 'SR', 'ALE', 'HE', 'PEG', 'AEE',
    'WEC', 'CMS', 'DTE', 'ES', 'FE', 'NI', 'AES', 'VST', 'CEG', 'PCG',
    'ATO', 'AWK', 'AWR', 'CWT', 'MSEX', 'SBS', 'SJW', 'YORW', 'ARTNA', 'CMCSA',
    'ATVI', 'TTWO', 'EA', 'ZNGA', 'DKNG', 'PENN', 'RSI', 'WYNN', 'LVS', 'MGM',
    'CZR', 'MLCO', 'ERI', 'GNOG', 'BALY', 'IGT', 'EVRI', 'SGMS', 'LNW', 'AGS',
    'PLYA', 'RRR', 'MCRI', 'CNTY', 'CZR', 'GDEN', 'BOYD', 'FULL', 'BYD', 'CHDN',
    'MTN', 'CAKE', 'TXRH', 'CBRL', 'DRI', 'BLMN', 'DENN', 'RRGB', 'DIN', 'RUTH',
    'BJRI', 'RAVE', 'WEN', 'JACK', 'SONC', 'PZZA', 'DPZ', 'CMG', 'WING', 'DNKN',
    'QSR', 'YUM', 'MCD', 'SBUX', 'BROS', 'DUTCH', 'CAVA', 'SHAK', 'TOST', 'LOCO',
    'WMT', 'TGT', 'COST', 'BJ', 'DLTR', 'DG', 'FIVE', 'OLLI', 'BIG', 'ROST',
]

def calculate_score(indicators):
    """Calculate composite score based on backtested methodology"""
    score = 0
    
    # RSI Score
    rsi = indicators.get('rsi', 50)
    if rsi < 30:
        score += 30
    elif rsi < 45:
        score += 20
    elif rsi > 70:
        score -= 10
    else:
        score += 10
    
    # ADX Score
    adx = indicators.get('adx', 0)
    if adx > 40:
        score += 30
    elif adx > 25:
        score += 20
    else:
        score += 5
    
    # Variance Score
    variance = indicators.get('variance', 50)
    if variance < 20:
        score += 25
    elif variance < 30:
        score += 15
    else:
        score += 5
    
    # EMA Alignment Score
    if indicators.get('emaAlignment') == 'Bullish':
        score += 25
    else:
        score += 5
    
    # Bonus: Strong trend + oversold RSI
    if adx > 40 and rsi < 45:
        score += 20
    
    return score

def scan_stocks():
    """Scan all stocks and return sorted results"""
    print(f"Starting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {API_URL}")
    
    results = []
    success_count = 0
    
    for i, ticker in enumerate(SP500_STOCKS):
        try:
            print(f"Scanning {ticker}... ({i+1}/{len(SP500_STOCKS)})")
            
            response = requests.get(
                f"{API_URL}/api/stock/{ticker}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate score
                score = calculate_score(data)
                data['score'] = score
                
                # Add company name
                data['name'] = get_company_name(ticker)
                
                results.append(data)
                success_count += 1
                print(f"✓ {ticker}: Score {score}")
            else:
                print(f"✗ {ticker}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"✗ {ticker}: Error - {str(e)}")
            continue
    
    print(f"\nScan complete: {success_count}/{len(SP500_STOCKS)} successful")
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

def get_company_name(ticker):
    """Get company name for ticker"""
    names = {
        'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.', 'AMZN': 'Amazon.com Inc.',
        'NVDA': 'NVIDIA Corporation', 'META': 'Meta Platforms Inc.',
        'TSLA': 'Tesla Inc.', 'BRK.B': 'Berkshire Hathaway',
        'LLY': 'Eli Lilly and Company', 'V': 'Visa Inc.',
        'UNH': 'UnitedHealth Group', 'JPM': 'JPMorgan Chase & Co.',
        'XOM': 'Exxon Mobil Corporation', 'MA': 'Mastercard Incorporated',
        'JNJ': 'Johnson & Johnson', 'PG': 'Procter & Gamble',
        'AVGO': 'Broadcom Inc.', 'HD': 'The Home Depot',
        'CVX': 'Chevron Corporation', 'ABBV': 'AbbVie Inc.',
        'MRK': 'Merck & Co.', 'COST': 'Costco Wholesale',
        'ADBE': 'Adobe Inc.', 'WMT': 'Walmart Inc.',
        'CRM': 'Salesforce Inc.', 'KO': 'The Coca-Cola Company',
        'NFLX': 'Netflix Inc.', 'PEP': 'PepsiCo Inc.',
        'TMO': 'Thermo Fisher Scientific', 'ORCL': 'Oracle Corporation',
        'BAC': 'Bank of America', 'ACN': 'Accenture plc',
        'AMD': 'Advanced Micro Devices', 'CSCO': 'Cisco Systems',
        'MCD': 'McDonald\'s Corporation', 'DIS': 'The Walt Disney Company',
        'ABT': 'Abbott Laboratories', 'WFC': 'Wells Fargo',
        'GE': 'General Electric', 'QCOM': 'QUALCOMM Incorporated',
        'INTU': 'Intuit Inc.', 'VZ': 'Verizon Communications',
        'IBM': 'IBM', 'CMCSA': 'Comcast Corporation',
        'TXN': 'Texas Instruments', 'CAT': 'Caterpillar Inc.',
        'AMGN': 'Amgen Inc.', 'PM': 'Philip Morris International',
        'HON': 'Honeywell International', 'UNP': 'Union Pacific Corporation',
        'LOW': 'Lowe\'s Companies', 'NKE': 'NIKE Inc.',
        'BA': 'The Boeing Company', 'GS': 'Goldman Sachs',
        'UPS': 'United Parcel Service', 'ELV': 'Elevance Health',
        'RTX': 'RTX Corporation', 'SBUX': 'Starbucks Corporation',
        'LMT': 'Lockheed Martin', 'SPGI': 'S&P Global Inc.',
        'T': 'AT&T Inc.', 'BLK': 'BlackRock Inc.',
        'DE': 'Deere & Company', 'AXP': 'American Express',
        'BKNG': 'Booking Holdings', 'MS': 'Morgan Stanley',
        'MDT': 'Medtronic plc', 'GILD': 'Gilead Sciences',
        'PLD': 'Prologis Inc.', 'ADI': 'Analog Devices',
        'MDLZ': 'Mondelez International', 'SYK': 'Stryker Corporation',
        'ISRG': 'Intuitive Surgical', 'CI': 'The Cigna Group',
        'VRTX': 'Vertex Pharmaceuticals', 'C': 'Citigroup Inc.',
        'NOW': 'ServiceNow Inc.', 'MMC': 'Marsh & McLennan',
        'REGN': 'Regeneron Pharmaceuticals', 'ZTS': 'Zoetis Inc.',
        'SO': 'The Southern Company', 'DUK': 'Duke Energy',
        'PGR': 'The Progressive Corporation', 'CB': 'Chubb Limited',
        'EOG': 'EOG Resources', 'BMY': 'Bristol-Myers Squibb',
        'CME': 'CME Group Inc.', 'MO': 'Altria Group',
        'SLB': 'Schlumberger Limited', 'TGT': 'Target Corporation',
        'HUM': 'Humana Inc.', 'USB': 'U.S. Bancorp',
        'PYPL': 'PayPal Holdings', 'LRCX': 'Lam Research',
        'SCHW': 'Charles Schwab', 'COP': 'ConocoPhillips',
        'ADP': 'Automatic Data Processing', 'BDX': 'Becton Dickinson',
        'TJX': 'The TJX Companies', 'AMAT': 'Applied Materials Inc.'
    }
    return names.get(ticker, ticker)

def save_results(results):
    """Save scan results to JSON file"""
    output = {
        'scanDate': datetime.now().isoformat(),
        'totalScanned': len(results),
        'top10': results[:10],
        'allResults': results
    }
    
    with open('scan_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Results saved to scan_results.json")
    print(f"\nTop 10 Stocks:")
    for i, stock in enumerate(results[:10], 1):
        print(f"  {i}. {stock['ticker']} - Score: {stock['score']}")

if __name__ == '__main__':
    results = scan_stocks()
    save_results(results)
