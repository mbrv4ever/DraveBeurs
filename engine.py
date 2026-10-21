# -*- coding: utf-8 -*-
"""DraveBeurs - motor: echte koersdata, portefeuille (papierhandel), leerstof.

EDUCATIEF / EDUCATIONAL ONLY. Virtueel geld, geen echt advies, geen echte
transacties.  Real market data is fetched when online (Yahoo/Stooq), cached
locally (portable), and falls back to clearly-labelled demo data offline.
"""
import json
import math
import os
import random
import sys
import time
import urllib.request

# ---------------------------------------------------------------------------
# portable paden: alles in een map naast de app
# ---------------------------------------------------------------------------
def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    d = os.path.join(app_dir(), "data")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


# ---------------------------------------------------------------------------
# instrumenten:  id -> naam, soort, yahoo-symbool, stooq-symbool
# ---------------------------------------------------------------------------
INSTRUMENTS = [
    {"id": "AAPL", "name": "Apple", "kind": "aandeel",
     "yahoo": "AAPL", "stooq": "aapl.us", "cur": "USD"},
    {"id": "MSFT", "name": "Microsoft", "kind": "aandeel",
     "yahoo": "MSFT", "stooq": "msft.us", "cur": "USD"},
    {"id": "ASML", "name": "ASML", "kind": "aandeel",
     "yahoo": "ASML", "stooq": "asml.us", "cur": "USD"},
    {"id": "SHEL", "name": "Shell", "kind": "aandeel",
     "yahoo": "SHEL", "stooq": "shel.us", "cur": "USD"},
    {"id": "WORLD", "name": "Wereld-ETF (MSCI World)", "kind": "etf",
     "yahoo": "URTH", "stooq": "urth.us", "cur": "USD"},
    {"id": "SP500", "name": "S&P 500 (index)", "kind": "index",
     "yahoo": "^GSPC", "stooq": "^spx", "cur": "USD"},
    {"id": "BTC", "name": "Bitcoin", "kind": "crypto",
     "yahoo": "BTC-USD", "stooq": "btcusd", "cur": "USD"},
    {"id": "ETH", "name": "Ethereum", "kind": "crypto",
     "yahoo": "ETH-USD", "stooq": "ethusd", "cur": "USD"},
    {"id": "GOLD", "name": "Goud", "kind": "grondstof",
     "yahoo": "GC=F", "stooq": "xauusd", "cur": "USD"},
]

INST_BY_ID = {i["id"]: i for i in INSTRUMENTS}


def _http_get(url, timeout=12):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# koers-historie ophalen  ->  list[(date_str, close_float)]
# ---------------------------------------------------------------------------
def _parse_yahoo(txt):
    d = json.loads(txt)
    res = d["chart"]["result"][0]
    ts = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    out = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        ds = time.strftime("%Y-%m-%d", time.gmtime(t))
        out.append((ds, float(c)))
    return out


def _parse_stooq(txt):
    out = []
    for line in txt.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) >= 5:
            try:
                out.append((parts[0], float(parts[4])))
            except ValueError:
                pass
    return out


def _demo_series(inst, days=2600):
    """Duidelijk gelabelde demo-data: een plausibele random walk."""
    rng = random.Random(hash(inst["id"]) & 0xffffffff)
    base = {"aandeel": 120, "etf": 90, "index": 3000, "crypto": 20000,
            "grondstof": 1500}.get(inst["kind"], 100)
    drift = {"crypto": 0.0007, "grondstof": 0.0002}.get(inst["kind"], 0.0004)
    vol = {"crypto": 0.035, "grondstof": 0.01, "index": 0.009}.get(
        inst["kind"], 0.016)
    price = base
    out = []
    t = time.time() - days * 86400
    for i in range(days):
        price *= math.exp(drift + rng.gauss(0, vol))
        if i % 1 == 0:
            ds = time.strftime("%Y-%m-%d", time.gmtime(t + i * 86400))
            out.append((ds, round(price, 2)))
    return out


def get_history(inst_id, max_age_hours=12):
    """Geeft (series, source) terug. source in {'cache','yahoo','stooq','demo'}."""
    inst = INST_BY_ID[inst_id]
    cache = os.path.join(data_dir(), inst_id + ".json")
    # 1) verse cache?
    try:
        if os.path.exists(cache):
            age = (time.time() - os.path.getmtime(cache)) / 3600.0
            with open(cache, "r", encoding="utf-8") as f:
                obj = json.load(f)
            series = [(d, float(c)) for d, c in obj["series"]]
            if series and age < max_age_hours:
                return series, "cache"
            cached = series
        else:
            cached = None
    except Exception:
        cached = None
    # 2) Yahoo
    series = None
    src = None
    try:
        url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s"
               "?range=10y&interval=1d" % inst["yahoo"])
        series = _parse_yahoo(_http_get(url))
        src = "yahoo"
    except Exception:
        series = None
    # 3) Stooq
    if not series:
        try:
            url = "https://stooq.com/q/d/l/?s=%s&i=d" % inst["stooq"]
            series = _parse_stooq(_http_get(url))
            src = "stooq"
        except Exception:
            series = None
    # 4) gebruik oude cache als netwerk faalt
    if not series and cached:
        return cached, "cache"
    # 5) demo
    if not series:
        return _demo_series(inst), "demo"
    # bewaar verse data
    try:
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"series": series, "src": src, "ts": time.time()}, f)
    except Exception:
        pass
    return series, src


def latest_price(inst_id):
    series, src = get_history(inst_id)
    return (series[-1][1] if series else 0.0), src


# ---------------------------------------------------------------------------
# portefeuille (papierhandel met virtueel geld)
# ---------------------------------------------------------------------------
START_CASH = 10000.0


class Portfolio:
    def __init__(self):
        self.cash = START_CASH
        self.holdings = {}        # id -> shares (float)
        self.cost = {}            # id -> kostprijs van huidig bezit (euro)
        self.realized = 0.0       # vastgelegde winst/verlies (euro)
        self.log = []             # list of dicts
        self.deposited = START_CASH

    def to_dict(self):
        return {"cash": self.cash, "holdings": self.holdings, "cost": self.cost,
                "realized": self.realized, "log": self.log,
                "deposited": self.deposited}

    @classmethod
    def from_dict(cls, d):
        p = cls()
        p.cash = float(d.get("cash", START_CASH))
        p.holdings = {k: float(v) for k, v in d.get("holdings", {}).items()}
        p.cost = {k: float(v) for k, v in d.get("cost", {}).items()}
        p.realized = float(d.get("realized", 0.0))
        p.log = list(d.get("log", []))
        p.deposited = float(d.get("deposited", START_CASH))
        return p

    def save(self, path=None):
        path = path or os.path.join(data_dir(), "portfolio.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f)
        except Exception:
            pass

    @classmethod
    def load(cls, path=None):
        path = path or os.path.join(data_dir(), "portfolio.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        except Exception:
            return cls()

    def reset(self):
        self.__init__()

    def deposit(self, amount):
        amount = max(0.0, float(amount))
        self.cash += amount
        self.deposited += amount
        self.log.append({"t": time.time(), "type": "inleg", "eur": amount})

    def buy(self, inst_id, eur, price):
        eur = float(eur)
        if price <= 0 or eur <= 0 or eur > self.cash + 1e-6:
            return False, "no_funds"
        shares = eur / price
        self.cash -= eur
        self.holdings[inst_id] = self.holdings.get(inst_id, 0.0) + shares
        self.cost[inst_id] = self.cost.get(inst_id, 0.0) + eur
        self.log.append({"t": time.time(), "type": "koop", "id": inst_id,
                         "shares": shares, "price": price, "eur": eur})
        return True, "ok"

    def sell(self, inst_id, eur, price):
        eur = float(eur)
        have = self.holdings.get(inst_id, 0.0)
        if price <= 0 or have <= 0:
            return False, "no_position"
        shares = min(have, eur / price)
        proceeds = shares * price
        cost_part = self.cost.get(inst_id, 0.0) * (shares / have)
        self.realized += proceeds - cost_part      # vastgelegde winst/verlies
        self.cost[inst_id] = self.cost.get(inst_id, 0.0) - cost_part
        self.cash += proceeds
        self.holdings[inst_id] = have - shares
        if self.holdings[inst_id] < 1e-9:
            del self.holdings[inst_id]
            self.cost.pop(inst_id, None)
        self.log.append({"t": time.time(), "type": "verkoop", "id": inst_id,
                         "shares": shares, "price": price, "eur": proceeds})
        return True, "ok"

    def holdings_value(self, prices):
        return sum(sh * prices.get(i, 0.0) for i, sh in self.holdings.items())

    def cost_basis(self):
        return sum(self.cost.values())

    def unrealized_pnl(self, prices):
        # papieren winst/verlies op wat je NU nog bezit
        return self.holdings_value(prices) - self.cost_basis()

    def realized_pnl(self):
        return self.realized

    def total_value(self, prices):
        return self.cash + self.holdings_value(prices)

    def pnl(self, prices):
        return self.total_value(prices) - self.deposited

    def pnl_pct(self, prices):
        return (self.pnl(prices) / self.deposited * 100.0
                if self.deposited else 0.0)


# ---------------------------------------------------------------------------
# slimme tips op basis van de portefeuille  ->  list[(key, **fmt)]
# ---------------------------------------------------------------------------
def analyze(portfolio, prices):
    tips = []
    total = portfolio.total_value(prices)
    hv = portfolio.holdings_value(prices)
    if total <= 0:
        return tips
    # cash drag
    if portfolio.cash / total > 0.6 and portfolio.deposited > 0:
        tips.append(("cash_drag",))
    # concentratie
    biggest = 0.0
    big_id = None
    for i, sh in portfolio.holdings.items():
        v = sh * prices.get(i, 0.0)
        if v > biggest:
            biggest = v
            big_id = i
    if hv > 0 and biggest / hv > 0.5 and big_id:
        tips.append(("concentration", INST_BY_ID[big_id]["name"]))
    # crypto-aandeel
    crypto_v = sum(sh * prices.get(i, 0.0) for i, sh in portfolio.holdings.items()
                   if INST_BY_ID[i]["kind"] == "crypto")
    if hv > 0 and crypto_v / hv > 0.4:
        tips.append(("much_crypto",))
    # spreiding goed
    if len(portfolio.holdings) >= 4 and hv > 0 and biggest / hv < 0.45:
        tips.append(("well_diversified",))
    return tips


# ---------------------------------------------------------------------------
# leerstof: lessen + quiz  (NL/EN)
# ---------------------------------------------------------------------------
LESSONS = [
    {"nl": ("Wat is beleggen?",
            "Beleggen is geld in bezittingen stoppen (zoals aandelen of ETF's) "
            "die in waarde kunnen stijgen of dalen. Doel: je geld op lange "
            "termijn laten groeien. Anders dan sparen is er risico: koersen "
            "bewegen op en neer."),
     "en": ("What is investing?",
            "Investing means putting money into assets (like stocks or ETFs) "
            "that can rise or fall in value. The goal: grow your money over the "
            "long term. Unlike saving, there is risk: prices move up and down.")},
    {"nl": ("Spreiding (diversificatie)",
            "Leg niet alles op één aandeel. Door te spreiden over veel "
            "bedrijven, sectoren en landen daalt je risico: gaat er één "
            "onderuit, dan vangen de anderen het op. Een wereld-ETF doet dit "
            "automatisch."),
     "en": ("Diversification",
            "Don't put everything in one stock. Spreading across many "
            "companies, sectors and countries lowers risk: if one drops, the "
            "others cushion it. A world ETF does this automatically.")},
    {"nl": ("Risico en rendement",
            "Meer mogelijk rendement gaat samen met meer risico. Crypto kan hard "
            "stijgen én hard dalen; een wereld-ETF beweegt rustiger. Kies wat "
            "bij jou en je tijdshorizon past."),
     "en": ("Risk and return",
            "Higher potential return comes with higher risk. Crypto can soar "
            "and crash; a world ETF moves more calmly. Choose what fits you and "
            "your time horizon.")},
    {"nl": ("Samengestelde rente",
            "Rendement op je rendement. Als je winst opnieuw meegroeit, gaat je "
            "vermogen steeds sneller omhoog. Tijd is hierbij je grootste vriend "
            "— vroeg beginnen loont enorm."),
     "en": ("Compound growth",
            "Return on your return. When gains keep growing too, your wealth "
            "rises ever faster. Time is your biggest friend here — starting "
            "early pays off hugely.")},
    {"nl": ("Periodiek inleggen (DCA)",
            "Elke maand een vast bedrag inleggen heet dollar-cost-averaging. Je "
            "koopt automatisch meer als het goedkoop is en minder als het duur "
            "is, en hoeft de 'beste dag' niet te raden."),
     "en": ("Regular investing (DCA)",
            "Investing a fixed amount each month is dollar-cost averaging. You "
            "automatically buy more when it's cheap and less when it's "
            "expensive, and don't have to guess the 'best day'.")},
    {"nl": ("Kosten en geduld",
            "Hoge kosten en veel handelen vreten rendement op. Goedkope "
            "indexfondsen en rustig vasthouden verslaan vaak druk handelen. "
            "Beleggen is een marathon, geen sprint."),
     "en": ("Costs and patience",
            "High fees and frequent trading eat returns. Cheap index funds and "
            "calm holding often beat busy trading. Investing is a marathon, not "
            "a sprint.")},
    {"nl": ("Inflatie",
            "Geld verliest langzaam koopkracht: voor €100 koop je over 20 jaar "
            "minder dan nu. Sparen alleen houdt vaak geen gelijke tred met "
            "inflatie; beleggen kan helpen je koopkracht te behouden of laten "
            "groeien — met meer risico."),
     "en": ("Inflation",
            "Money slowly loses buying power: €100 buys less in 20 years than "
            "today. Saving alone often doesn't keep up with inflation; investing "
            "can help preserve or grow your buying power — with more risk.")},
    {"nl": ("Kosten op lange termijn",
            "Een verschil van 1% kosten per jaar lijkt klein, maar over 30 jaar "
            "kan het tienduizenden euro's schelen door het samengestelde "
            "effect. Let dus goed op lopende kosten van een fonds."),
     "en": ("Costs over the long run",
            "A 1%-per-year fee difference seems tiny, but over 30 years it can "
            "cost tens of thousands due to compounding. So watch a fund's "
            "ongoing costs closely.")},
    {"nl": ("Tijd in de markt > timing",
            "Niemand koopt steevast op de bodem. Wie bij elke dip in paniek "
            "verkoopt, mist vaak de sterkste herstelweken. Rustig blijven en "
            "lang beleggen verslaat meestal het 'perfecte moment' zoeken."),
     "en": ("Time in the market > timing",
            "Nobody reliably buys the bottom. Panic-selling every dip often "
            "misses the strongest recovery weeks. Staying calm and investing "
            "long usually beats hunting the 'perfect moment'.")},
    {"nl": ("Te mooi om waar te zijn",
            "Beloofde 'gegarandeerde' hoge winst, druk om snel in te stappen, "
            "of een muntje dat 'gegarandeerd ontploft' — dat zijn alarmbellen. "
            "Bij beleggen bestaat geen gratis hoog rendement zonder risico."),
     "en": ("Too good to be true",
            "Promised 'guaranteed' high returns, pressure to get in fast, or a "
            "coin that 'will surely moon' — those are red flags. In investing "
            "there is no free high return without risk.")},
]

QUIZ = [
    {"nl": ("Wat verlaagt je risico het meest?",
            ["Alles op één aandeel zetten",
             "Spreiden over veel bedrijven/landen",
             "Zo vaak mogelijk handelen"]),
     "en": ("What lowers your risk the most?",
            ["Putting everything in one stock",
             "Spreading across many companies/countries",
             "Trading as often as possible"]),
     "answer": 1,
     "exp_nl": "Spreiding vangt klappen op: één verliezer weegt minder zwaar.",
     "exp_en": "Diversification cushions blows: one loser weighs less."},
    {"nl": ("Wat hoort meestal bij hoog mogelijk rendement?",
            ["Hoog risico", "Geen risico", "Gegarandeerde winst"]),
     "en": ("What usually comes with high potential return?",
            ["High risk", "No risk", "Guaranteed profit"]),
     "answer": 0,
     "exp_nl": "Rendement en risico gaan hand in hand. Pas op voor 'gegarandeerd'.",
     "exp_en": "Return and risk go together. Beware of 'guaranteed'."},
    {"nl": ("Wat is samengestelde rente?",
            ["Rente op je rente", "Een belasting", "Een soort aandeel"]),
     "en": ("What is compound growth?",
            ["Return on your return", "A tax", "A type of stock"]),
     "answer": 0,
     "exp_nl": "Je winst groeit mee, dus het gaat steeds sneller — tijd helpt.",
     "exp_en": "Your gains grow too, so it speeds up — time helps."},
    {"nl": ("Elke maand een vast bedrag inleggen heet...",
            ["Dollar-cost averaging", "Hefboom", "Shorten"]),
     "en": ("Investing a fixed amount monthly is called...",
            ["Dollar-cost averaging", "Leverage", "Shorting"]),
     "answer": 0,
     "exp_nl": "DCA: je hoeft de markt niet te timen.",
     "exp_en": "DCA: you don't have to time the market."},
    {"nl": ("Wat doet een wereld-ETF voor je?",
            ["Automatisch spreiden over de hele wereld",
             "Gegarandeerd 10% per jaar",
             "Alleen één bedrijf kopen"]),
     "en": ("What does a world ETF do for you?",
            ["Automatically spread across the whole world",
             "Guarantee 10% per year",
             "Buy only one company"]),
     "answer": 0,
     "exp_nl": "Eén koop = honderden bedrijven wereldwijd.",
     "exp_en": "One buy = hundreds of companies worldwide."},
    {"nl": ("Wat is vaak het slimst op lange termijn?",
            ["Rustig vasthouden en spreiden", "Elke dag kopen en verkopen",
             "Alles in de munt van het moment"]),
     "en": ("What is often smartest long term?",
            ["Calmly hold and diversify", "Buy and sell every day",
             "All-in on the hot coin"]),
     "answer": 0,
     "exp_nl": "Kosten en paniek-handelen schaden rendement; geduld wint vaak.",
     "exp_en": "Costs and panic-trading hurt returns; patience often wins."},
    {"nl": ("Wat doet inflatie met spaargeld dat stil staat?",
            ["Het wordt minder waard in koopkracht",
             "Het groeit vanzelf", "Niets"]),
     "en": ("What does inflation do to idle savings?",
            ["It loses buying power", "It grows by itself", "Nothing"]),
     "answer": 0,
     "exp_nl": "Door inflatie koop je later minder voor hetzelfde bedrag.",
     "exp_en": "Inflation means the same amount buys less later."},
    {"nl": ("Hoeveel maakt 1% kosten per jaar uit over 30 jaar?",
            ["Heel veel, door samengesteld effect",
             "Vrijwel niets", "Alleen in het eerste jaar"]),
     "en": ("How much does a 1% yearly fee matter over 30 years?",
            ["A lot, due to compounding", "Almost nothing",
             "Only in year one"]),
     "answer": 0,
     "exp_nl": "Kleine jaarlijkse kosten tikken enorm aan op lange termijn.",
     "exp_en": "Small yearly fees add up enormously over the long run."},
    {"nl": ("De markt zakt hard. Wat is vaak verstandig?",
            ["Rustig blijven en je plan volgen",
             "Alles in paniek verkopen", "Alles lenen en bijkopen"]),
     "en": ("The market drops hard. What's often wise?",
            ["Stay calm and stick to your plan",
             "Panic-sell everything", "Borrow and go all-in"]),
     "answer": 0,
     "exp_nl": "Wie paniekt mist vaak het herstel; tijd in de markt telt.",
     "exp_en": "Panicking often misses the recovery; time in the market counts."},
    {"nl": ("Iemand belooft 'gegarandeerd 20% per maand'. Wat doe je?",
            ["Wegblijven - dit is een alarmbel",
             "Direct al je geld inleggen", "Geld lenen om mee te doen"]),
     "en": ("Someone promises 'guaranteed 20% a month'. You...",
            ["Stay away - it's a red flag",
             "Put in all your money now", "Borrow to join"]),
     "answer": 0,
     "exp_nl": "Gegarandeerd hoog rendement bestaat niet; pas op voor oplichting.",
     "exp_en": "Guaranteed high returns don't exist; beware of scams."},
]


def simulate_dca(inst_id, monthly, start_date):
    """Maandelijks 'monthly' euro inleggen vanaf start_date.
    Geeft tijdlijn (datum, ingelegd, waarde) + samenvatting."""
    series, src = get_history(inst_id)
    pts = [(d, c) for d, c in series if d >= start_date and c > 0]
    if not pts:
        return None
    shares = 0.0
    contributed = 0.0
    last_month = None
    timeline = []
    for d, c in pts:
        ym = d[:7]
        if ym != last_month:
            shares += monthly / c
            contributed += monthly
            last_month = ym
        timeline.append((d, contributed, shares * c))
    return {"timeline": timeline, "contributed": contributed,
            "value": timeline[-1][2], "src": src,
            "start": pts[0][0], "end": pts[-1][0]}


if __name__ == "__main__":
    # kleine zelftest (offline -> demo)
    p = Portfolio()
    price, src = latest_price("AAPL")
    print("AAPL prijs %.2f (bron %s)" % (price, src))
    p.buy("AAPL", 3000, price)
    p.buy("BTC", 2000, latest_price("BTC")[0])
    prices = {"AAPL": price, "BTC": latest_price("BTC")[0]}
    print("totaal %.2f  winst %.2f (%.1f%%)" % (
        p.total_value(prices), p.pnl(prices), p.pnl_pct(prices)))
    print("tips:", analyze(p, prices))
    print("lessen:", len(LESSONS), "quiz:", len(QUIZ))
