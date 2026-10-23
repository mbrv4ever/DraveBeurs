# -*- coding: utf-8 -*-
"""DraveBeurs - leerzame beleggings-simulator (PyQt6).

EDUCATIEF: virtueel geld, papierhandel, GEEN financieel advies, GEEN echte
transacties. Echte koersdata wordt opgehaald als je online bent (anders
demo-data). Taal volgt de pc (NL/EN). Portable: alles in de app-map.
"""
import bisect
import locale
import os
import sys

from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import (QPainter, QPen, QColor, QFont, QDesktopServices,
                         QIcon)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QPushButton, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QLineEdit, QTabWidget, QComboBox,
                             QSlider, QTableWidget, QTableWidgetItem, QMessageBox,
                             QTextEdit, QButtonGroup, QRadioButton, QFrame,
                             QHeaderView)

import engine as E


def _lang():
    try:
        loc = (locale.getdefaultlocale()[0] or "")
    except Exception:
        loc = ""
    return "nl" if loc.lower().startswith("nl") else "en"


LANG = _lang()

TX = {
    "title": {"nl": "DraveBeurs - leer beleggen", "en": "DraveBeurs - learn investing"},
    "disclaimer": {
        "nl": "Educatief spel met virtueel geld - geen financieel advies, "
              "geen echte transacties.",
        "en": "Educational game with virtual money - not financial advice, "
              "no real transactions."},
    "mode": {"nl": "Modus", "en": "Mode"},
    "live": {"nl": "Live (nu)", "en": "Live (now)"},
    "timetravel": {"nl": "Tijdreis", "en": "Time travel"},
    "forward": {"nl": "Spoel vooruit »", "en": "Fast forward »"},
    "date": {"nl": "Datum", "en": "Date"},
    "cash": {"nl": "Contant", "en": "Cash"},
    "total": {"nl": "Totaal", "en": "Total"},
    "pnl": {"nl": "Winst/verlies", "en": "Profit/loss"},
    "unreal": {"nl": "Op papier (nog niet verkocht)", "en": "On paper (unsold)"},
    "real": {"nl": "Vastgelegd (verkocht)", "en": "Realized (sold)"},
    "tab_market": {"nl": "Markt", "en": "Market"},
    "tab_port": {"nl": "Portefeuille", "en": "Portfolio"},
    "tab_learn": {"nl": "Leren", "en": "Learn"},
    "tab_dca": {"nl": "Inleg-simulator", "en": "Deposit simulator"},
    "dca_monthly": {"nl": "Maandbedrag (€)", "en": "Monthly (€)"},
    "dca_from": {"nl": "Vanaf jaar", "en": "From year"},
    "dca_calc": {"nl": "Bereken", "en": "Calculate"},
    "dca_contrib": {"nl": "Ingelegd", "en": "Contributed"},
    "dca_value": {"nl": "Waarde", "en": "Value"},
    "dca_intro": {
        "nl": "Zie wat élke maand een vast bedrag inleggen (DCA) over de jaren "
              "doet. Je koopt automatisch meer als het goedkoop is en minder als "
              "het duur is.",
        "en": "See what investing a fixed amount every month (DCA) does over the "
              "years. You automatically buy more when it's cheap and less when "
              "it's expensive."},
    "dca_result": {
        "nl": "Je legde in totaal €%.0f in; dat werd €%.0f (verschil €%.0f).",
        "en": "You contributed €%.0f in total; it became €%.0f (difference €%.0f)."},
    "price": {"nl": "Koers", "en": "Price"},
    "source": {"nl": "bron", "en": "source"},
    "amount": {"nl": "Bedrag (€)", "en": "Amount (€)"},
    "buy": {"nl": "Kopen", "en": "Buy"},
    "sell": {"nl": "Verkopen", "en": "Sell"},
    "deposit": {"nl": "Inleggen €1000", "en": "Deposit €1000"},
    "reset": {"nl": "Opnieuw beginnen", "en": "Reset"},
    "instrument": {"nl": "Belegging", "en": "Asset"},
    "shares": {"nl": "Aantal", "en": "Units"},
    "value": {"nl": "Waarde", "en": "Value"},
    "weight": {"nl": "Aandeel", "en": "Weight"},
    "bought": {"nl": "Gekocht voor €%.0f %s", "en": "Bought €%.0f of %s"},
    "sold": {"nl": "Verkocht voor €%.0f %s", "en": "Sold €%.0f of %s"},
    "no_funds": {"nl": "Niet genoeg contant geld.", "en": "Not enough cash."},
    "no_pos": {"nl": "Je bezit dit niet.", "en": "You don't own this."},
    "lessons": {"nl": "Lessen", "en": "Lessons"},
    "quiz": {"nl": "Quiz", "en": "Quiz"},
    "check": {"nl": "Controleer", "en": "Check"},
    "next": {"nl": "Volgende", "en": "Next"},
    "correct": {"nl": "Goed!", "en": "Correct!"},
    "wrong": {"nl": "Niet helemaal.", "en": "Not quite."},
    "score": {"nl": "Score", "en": "Score"},
    "tips": {"nl": "Tips", "en": "Tips"},
    "reset_q": {"nl": "Alles opnieuw beginnen met €10.000?",
                "en": "Restart everything with €10,000?"},
    "demo_warn": {"nl": "  (demo-data: geen internet)", "en": "  (demo data: offline)"},
    "donate": {"nl": "Bevalt het? Doneer:", "en": "Enjoying it? Donate:"},
    "loading": {"nl": "laden...", "en": "loading..."},
}

TIPS_TXT = {
    "cash_drag": {"nl": "Je hebt veel contant geld staan dat niets opbrengt; "
                        "overweeg gespreid in te leggen.",
                  "en": "You hold a lot of idle cash; consider investing it in a "
                        "spread-out way."},
    "concentration": {"nl": "Groot deel zit in %s. Spreiden verlaagt je risico.",
                      "en": "A big part is in %s. Diversifying lowers your risk."},
    "much_crypto": {"nl": "Veel crypto: dat kan hard schommelen. Houd het klein "
                          "t.o.v. je totaal.",
                    "en": "Lots of crypto: it can swing hard. Keep it small "
                          "vs your total."},
    "well_diversified": {"nl": "Mooi gespreid! Zo vang je tegenvallers beter op.",
                         "en": "Nicely diversified! That cushions setbacks."},
}


def T(k):
    d = TX.get(k, {})
    return d.get(LANG) or d.get("en") or k


def tip_text(t):
    key = t[0]
    s = TIPS_TXT.get(key, {}).get(LANG) or TIPS_TXT.get(key, {}).get("en") or key
    if len(t) > 1 and "%s" in s:
        return s % t[1]
    return s


DONATE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

BG = "#10131c"
CARD = "#1a1f2e"
ACCENT = "#3fb6ff"
GREEN = "#4ad07a"
RED = "#e85d5d"
TEXTC = "#e8eef6"


# ---------------------------------------------------------------------------
def price_on(series, date_str):
    """Laatste slotkoers op of vóór date_str."""
    if not series:
        return 0.0
    dates = [d for d, _ in series]
    i = bisect.bisect_right(dates, date_str) - 1
    if i < 0:
        i = 0
    return series[i][1]


# ---------------------------------------------------------------------------
class Chart(QWidget):
    def __init__(self):
        super().__init__()
        self.series = []
        self.setMinimumHeight(240)

    def set_series(self, series):
        self.series = series or []
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(CARD))
        if len(self.series) < 2:
            p.setPen(QColor(TEXTC))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, T("loading"))
            return
        ys = [c for _, c in self.series]
        lo, hi = min(ys), max(ys)
        if hi - lo < 1e-9:
            hi = lo + 1
        m = 28
        n = len(self.series)
        up = ys[-1] >= ys[0]
        col = QColor(GREEN if up else RED)
        # grid
        p.setPen(QPen(QColor("#2a3144"), 1))
        for g in range(5):
            gy = m + (h - 2 * m) * g / 4
            p.drawLine(m, int(gy), w - m, int(gy))
        # lijn

        def X(i):
            return m + (w - 2 * m) * i / (n - 1)

        def Y(v):
            return h - m - (h - 2 * m) * (v - lo) / (hi - lo)

        p.setPen(QPen(col, 2))
        prev = None
        step = max(1, n // 1200)
        for i in range(0, n, step):
            pt = (X(i), Y(ys[i]))
            if prev:
                p.drawLine(int(prev[0]), int(prev[1]), int(pt[0]), int(pt[1]))
            prev = pt
        # labels
        p.setPen(QColor(TEXTC))
        f = QFont("Segoe UI", 8)
        p.setFont(f)
        p.drawText(4, int(Y(hi)) + 4, "%.0f" % hi)
        p.drawText(4, int(Y(lo)) + 4, "%.0f" % lo)
        p.drawText(m, h - 8, self.series[0][0])
        p.drawText(w - m - 70, h - 8, self.series[-1][0])


class DualChart(QWidget):
    """Twee lijnen: ingelegd (grijs) en waarde (groen/rood)."""
    def __init__(self):
        super().__init__()
        self.vals = []
        self.contribs = []
        self.setMinimumHeight(260)

    def set_data(self, vals, contribs):
        self.vals = vals or []
        self.contribs = contribs or []
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(CARD))
        if len(self.vals) < 2:
            p.setPen(QColor(TEXTC))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "—")
            return
        hi = max(max(self.vals), max(self.contribs)) or 1.0
        lo = 0.0
        m = 30
        n = len(self.vals)
        p.setPen(QPen(QColor("#2a3144"), 1))
        for g in range(5):
            gy = m + (h - 2 * m) * g / 4
            p.drawLine(m, int(gy), w - m, int(gy))

        def X(i):
            return m + (w - 2 * m) * i / (n - 1)

        def Y(v):
            return h - m - (h - 2 * m) * (v - lo) / (hi - lo)

        def line(data, color, width):
            p.setPen(QPen(QColor(color), width))
            prev = None
            step = max(1, n // 1200)
            for i in range(0, n, step):
                pt = (X(i), Y(data[i]))
                if prev:
                    p.drawLine(int(prev[0]), int(prev[1]), int(pt[0]), int(pt[1]))
                prev = pt
        line(self.contribs, "#9fb0c8", 2)
        up = self.vals[-1] >= self.contribs[-1]
        line(self.vals, GREEN if up else RED, 3)
        p.setPen(QColor(TEXTC))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(4, int(Y(hi)) + 4, "%.0f" % hi)
        p.drawText(m, h - 8, "%s" % (T("dca_contrib")))
        p.setPen(QColor(GREEN if up else RED))
        p.drawText(w - m - 90, h - 8, "%s" % (T("dca_value")))


# ---------------------------------------------------------------------------
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(T("title"))
        self.resize(1040, 720)
        ic = os.path.join(E.app_dir(), "assets", "icon.ico")
        if os.path.exists(ic):
            self.setWindowIcon(QIcon(ic))
        self.setStyleSheet(
            "QWidget{background:%s;color:%s;font-family:'Segoe UI';font-size:13px}"
            "QPushButton{background:%s;border:1px solid #33405c;border-radius:6px;"
            "padding:7px 12px}QPushButton:hover{background:#26314a}"
            "QLineEdit,QComboBox{background:#0d1018;border:1px solid #33405c;"
            "border-radius:5px;padding:5px}"
            "QTabWidget::pane{border:1px solid #2a3144}"
            "QTabBar::tab{background:%s;padding:8px 16px;margin:2px}"
            "QTabBar::tab:selected{background:%s;color:#06121f}"
            "QListWidget,QTableWidget,QTextEdit{background:%s;border:1px solid "
            "#2a3144;border-radius:6px}" % (BG, TEXTC, CARD, CARD, ACCENT, CARD))

        self.port = E.Portfolio.load()
        self.cache = {}          # id -> (series, src)
        self.mode_live = True
        self.sim_date = None
        self.cur_id = E.INSTRUMENTS[0]["id"]

        self._build_ui()
        self._series_for(self.cur_id)
        self._set_sim_range()
        self._refresh_all()

    # ---- data helpers ----
    def _series_for(self, iid):
        if iid not in self.cache:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self.cache[iid] = E.get_history(iid)
            finally:
                QApplication.restoreOverrideCursor()
        return self.cache[iid]

    def _all_dates(self):
        s, _ = self._series_for(self.cur_id)
        return [d for d, _ in s]

    def _cur_date(self):
        if self.mode_live or not self.sim_date:
            return "9999-99-99"
        return self.sim_date

    def price_of(self, iid):
        s, _ = self._series_for(iid)
        if self.mode_live:
            return s[-1][1] if s else 0.0
        return price_on(s, self._cur_date())

    def prices_held(self):
        ids = set(self.port.holdings) | {self.cur_id}
        return {i: self.price_of(i) for i in ids}

    def _set_sim_range(self):
        s, _ = self._series_for(self.cur_id)
        if s:
            self.sim_idx_max = len(s) - 1
            self.slider.setMaximum(max(1, len(s) - 1))
            start = int(len(s) * 0.45)
            self.slider.setValue(start)
            self.sim_date = s[start][0]

    # ---- UI ----
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # topbar
        top = QHBoxLayout()
        ttl = QLabel("DraveBeurs")
        ttl.setStyleSheet("font-size:22px;font-weight:bold;color:%s" % ACCENT)
        top.addWidget(ttl)
        top.addSpacing(16)
        top.addWidget(QLabel(T("mode") + ":"))
        self.mode_cb = QComboBox()
        self.mode_cb.addItems([T("live"), T("timetravel")])
        self.mode_cb.currentIndexChanged.connect(self._mode_changed)
        top.addWidget(self.mode_cb)
        self.date_lbl = QLabel("")
        top.addWidget(self.date_lbl)
        self.fwd_btn = QPushButton(T("forward"))
        self.fwd_btn.clicked.connect(self._forward)
        top.addWidget(self.fwd_btn)
        top.addStretch(1)
        self.money_lbl = QLabel("")
        self.money_lbl.setStyleSheet("font-size:14px")
        top.addWidget(self.money_lbl)
        root.addLayout(top)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self._slider_moved)
        root.addWidget(self.slider)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self._build_market_tab()
        self._build_port_tab()
        self._build_learn_tab()
        self._build_dca_tab()

        # onderbalk: disclaimer + donatie
        bottom = QHBoxLayout()
        dis = QLabel("⚠  " + T("disclaimer"))
        dis.setStyleSheet("color:#9fb0c8;font-size:11px")
        bottom.addWidget(dis)
        bottom.addStretch(1)
        dn = QLabel('%s <a href="%s" style="color:%s">%s</a>'
                    % (T("donate"), DONATE, ACCENT, DONATE))
        dn.setOpenExternalLinks(True)
        dn.setStyleSheet("font-size:11px")
        bottom.addWidget(dn)
        root.addLayout(bottom)

    def _build_market_tab(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        self.inst_list = QListWidget()
        self.inst_list.setMaximumWidth(260)
        kindlbl = {"aandeel": {"nl": "aandeel", "en": "stock"},
                   "etf": {"nl": "ETF", "en": "ETF"},
                   "index": {"nl": "index", "en": "index"},
                   "crypto": {"nl": "crypto", "en": "crypto"},
                   "grondstof": {"nl": "grondstof", "en": "commodity"}}
        for ins in E.INSTRUMENTS:
            k = kindlbl.get(ins["kind"], {}).get(LANG, ins["kind"])
            it = QListWidgetItem("%s\n   %s" % (ins["name"], k))
            it.setData(Qt.ItemDataRole.UserRole, ins["id"])
            self.inst_list.addItem(it)
        self.inst_list.setCurrentRow(0)
        self.inst_list.currentRowChanged.connect(self._inst_changed)
        lay.addWidget(self.inst_list)

        right = QVBoxLayout()
        self.name_lbl = QLabel("")
        self.name_lbl.setStyleSheet("font-size:18px;font-weight:bold")
        right.addWidget(self.name_lbl)
        self.chart = Chart()
        right.addWidget(self.chart, 1)
        self.price_lbl = QLabel("")
        self.price_lbl.setStyleSheet("font-size:15px")
        right.addWidget(self.price_lbl)
        row = QHBoxLayout()
        row.addWidget(QLabel(T("amount") + ":"))
        self.amount = QLineEdit("1000")
        self.amount.setMaximumWidth(120)
        row.addWidget(self.amount)
        bbuy = QPushButton(T("buy"))
        bbuy.setStyleSheet("background:%s;color:#06210f;font-weight:bold" % GREEN)
        bbuy.clicked.connect(self._buy)
        row.addWidget(bbuy)
        bsell = QPushButton(T("sell"))
        bsell.setStyleSheet("background:%s;color:#2a0707;font-weight:bold" % RED)
        bsell.clicked.connect(self._sell)
        row.addWidget(bsell)
        row.addStretch(1)
        right.addLayout(row)
        self.msg_lbl = QLabel("")
        self.msg_lbl.setStyleSheet("color:%s" % ACCENT)
        right.addWidget(self.msg_lbl)
        lay.addLayout(right, 1)
        self.tabs.addTab(w, T("tab_market"))

    def _build_port_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        self.sum_lbl = QLabel("")
        self.sum_lbl.setStyleSheet("font-size:15px")
        lay.addWidget(self.sum_lbl)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            [T("instrument"), T("shares"), T("value"), T("weight")])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table, 1)
        tipbox = QLabel(T("tips"))
        tipbox.setStyleSheet("font-weight:bold;margin-top:6px")
        lay.addWidget(tipbox)
        self.tips_lbl = QLabel("")
        self.tips_lbl.setWordWrap(True)
        self.tips_lbl.setStyleSheet("color:#ffd98a")
        lay.addWidget(self.tips_lbl)
        row = QHBoxLayout()
        bdep = QPushButton(T("deposit"))
        bdep.clicked.connect(self._deposit)
        row.addWidget(bdep)
        brs = QPushButton(T("reset"))
        brs.clicked.connect(self._reset)
        row.addWidget(brs)
        row.addStretch(1)
        lay.addLayout(row)
        self.tabs.addTab(w, T("tab_port"))

    def _build_learn_tab(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        left = QVBoxLayout()
        left.addWidget(QLabel(T("lessons")))
        self.les_list = QListWidget()
        self.les_list.setMaximumWidth(260)
        for ls in E.LESSONS:
            self.les_list.addItem(ls[LANG][0])
        self.les_list.currentRowChanged.connect(self._lesson_sel)
        left.addWidget(self.les_list)
        lay.addLayout(left)
        right = QVBoxLayout()
        self.les_text = QTextEdit()
        self.les_text.setReadOnly(True)
        right.addWidget(self.les_text, 1)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        right.addWidget(line)
        self.quiz_idx = 0
        self.quiz_score = 0
        self.q_lbl = QLabel("")
        self.q_lbl.setWordWrap(True)
        self.q_lbl.setStyleSheet("font-weight:bold")
        right.addWidget(self.q_lbl)
        self.q_group = QButtonGroup(self)
        self.q_btns = []
        for _ in range(3):
            rb = QRadioButton("")
            self.q_group.addButton(rb)
            self.q_btns.append(rb)
            right.addWidget(rb)
        qrow = QHBoxLayout()
        self.check_btn = QPushButton(T("check"))
        self.check_btn.clicked.connect(self._quiz_check)
        qrow.addWidget(self.check_btn)
        self.next_btn = QPushButton(T("next"))
        self.next_btn.clicked.connect(self._quiz_next)
        qrow.addWidget(self.next_btn)
        qrow.addStretch(1)
        self.qscore_lbl = QLabel("")
        qrow.addWidget(self.qscore_lbl)
        right.addLayout(qrow)
        self.q_fb = QLabel("")
        self.q_fb.setWordWrap(True)
        right.addWidget(self.q_fb)
        lay.addLayout(right, 1)
        self.tabs.addTab(w, T("tab_learn"))
        self.les_list.setCurrentRow(0)
        self._load_quiz()

    def _build_dca_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        intro = QLabel(T("dca_intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#9fb0c8")
        lay.addWidget(intro)
        row = QHBoxLayout()
        row.addWidget(QLabel(T("instrument") + ":"))
        self.dca_inst = QComboBox()
        for ins in E.INSTRUMENTS:
            self.dca_inst.addItem(ins["name"], ins["id"])
        row.addWidget(self.dca_inst)
        row.addWidget(QLabel(T("dca_monthly") + ":"))
        self.dca_amt = QLineEdit("100")
        self.dca_amt.setMaximumWidth(90)
        row.addWidget(self.dca_amt)
        row.addWidget(QLabel(T("dca_from") + ":"))
        self.dca_year = QComboBox()
        row.addWidget(self.dca_year)
        b = QPushButton(T("dca_calc"))
        b.setStyleSheet("background:%s;color:#06210f;font-weight:bold" % GREEN)
        b.clicked.connect(self._run_dca)
        row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.dca_chart = DualChart()
        lay.addWidget(self.dca_chart, 1)
        self.dca_lbl = QLabel("")
        self.dca_lbl.setStyleSheet("font-size:15px")
        self.dca_lbl.setWordWrap(True)
        lay.addWidget(self.dca_lbl)
        self.dca_inst.currentIndexChanged.connect(self._dca_years)
        self.tabs.addTab(w, T("tab_dca"))
        self._dca_years()

    def _dca_years(self):
        iid = self.dca_inst.currentData()
        s, _ = self._series_for(iid)
        years = sorted({d[:4] for d, _ in s})
        self.dca_year.clear()
        self.dca_year.addItems(years)

    def _run_dca(self):
        iid = self.dca_inst.currentData()
        try:
            amt = float(self.dca_amt.text().replace(",", "."))
        except ValueError:
            return
        yr = self.dca_year.currentText() or "2000"
        r = E.simulate_dca(iid, amt, yr + "-01-01")
        if not r:
            return
        vals = [v for _, _, v in r["timeline"]]
        contribs = [c for _, c, _ in r["timeline"]]
        self.dca_chart.set_data(vals, contribs)
        diff = r["value"] - r["contributed"]
        self.dca_lbl.setText(T("dca_result") % (r["contributed"], r["value"],
                                                diff))

    # ---- events ----
    def _mode_changed(self, idx):
        self.mode_live = (idx == 0)
        self.slider.setVisible(not self.mode_live)
        self.fwd_btn.setVisible(not self.mode_live)
        self._refresh_all()

    def _slider_moved(self, v):
        s, _ = self._series_for(self.cur_id)
        if s:
            v = min(v, len(s) - 1)
            self.sim_date = s[v][0]
        self._refresh_all()

    def _forward(self):
        self.slider.setValue(min(self.slider.maximum(),
                                 self.slider.value() + 90))

    def _inst_changed(self, row):
        it = self.inst_list.item(row)
        if it:
            self.cur_id = it.data(Qt.ItemDataRole.UserRole)
            self._refresh_market()

    def _buy(self):
        try:
            eur = float(self.amount.text().replace(",", "."))
        except ValueError:
            return
        ok, why = self.port.buy(self.cur_id, eur, self.price_of(self.cur_id))
        if ok:
            self.port.save()
            self.msg_lbl.setText(T("bought") % (eur, INST_NAME(self.cur_id)))
        else:
            self.msg_lbl.setText(T("no_funds"))
        self._refresh_all()

    def _sell(self):
        try:
            eur = float(self.amount.text().replace(",", "."))
        except ValueError:
            return
        ok, why = self.port.sell(self.cur_id, eur, self.price_of(self.cur_id))
        if ok:
            self.port.save()
            self.msg_lbl.setText(T("sold") % (eur, INST_NAME(self.cur_id)))
        else:
            self.msg_lbl.setText(T("no_pos"))
        self._refresh_all()

    def _deposit(self):
        self.port.deposit(1000)
        self.port.save()
        self._refresh_all()

    def _reset(self):
        if QMessageBox.question(self, "DraveBeurs", T("reset_q")) == \
                QMessageBox.StandardButton.Yes:
            self.port.reset()
            self.port.save()
            self._refresh_all()

    def _lesson_sel(self, row):
        if 0 <= row < len(E.LESSONS):
            t, b = E.LESSONS[row][LANG]
            self.les_text.setHtml("<h3 style='color:%s'>%s</h3><p>%s</p>"
                                  % (ACCENT, t, b))

    def _load_quiz(self):
        q = E.QUIZ[self.quiz_idx]
        self.q_lbl.setText("%d/%d  %s" % (self.quiz_idx + 1, len(E.QUIZ),
                                          q[LANG][0]))
        opts = q[LANG][1]
        self.q_group.setExclusive(False)
        for i, rb in enumerate(self.q_btns):
            if i < len(opts):
                rb.setText(opts[i])
                rb.setChecked(False)
                rb.setVisible(True)
            else:
                rb.setVisible(False)
        self.q_group.setExclusive(True)
        self.q_fb.setText("")
        self.qscore_lbl.setText("%s: %d" % (T("score"), self.quiz_score))

    def _quiz_check(self):
        q = E.QUIZ[self.quiz_idx]
        chosen = -1
        for i, rb in enumerate(self.q_btns):
            if rb.isChecked():
                chosen = i
        if chosen < 0:
            return
        if chosen == q["answer"]:
            self.quiz_score += 1
            self.q_fb.setText("<b style='color:%s'>%s</b> %s"
                              % (GREEN, T("correct"), q["exp_" + LANG]))
        else:
            self.q_fb.setText("<b style='color:%s'>%s</b> %s"
                              % (RED, T("wrong"), q["exp_" + LANG]))
        self.qscore_lbl.setText("%s: %d" % (T("score"), self.quiz_score))

    def _quiz_next(self):
        self.quiz_idx = (self.quiz_idx + 1) % len(E.QUIZ)
        self._load_quiz()

    # ---- refresh ----
    def _refresh_market(self):
        ins = E.INST_BY_ID[self.cur_id]
        self.name_lbl.setText(ins["name"])
        s, src = self._series_for(self.cur_id)
        if self.mode_live:
            self.chart.set_series(s)
        else:
            d = self._cur_date()
            cut = [(dt, c) for dt, c in s if dt <= d]
            self.chart.set_series(cut or s[:2])
        pr = self.price_of(self.cur_id)
        extra = T("demo_warn") if src == "demo" else ""
        self.price_lbl.setText("%s: %.2f %s   (%s: %s)%s" %
                               (T("price"), pr, ins["cur"], T("source"), src, extra))

    def _refresh_port(self):
        prices = self.prices_held()
        self.table.setRowCount(len(self.port.holdings))
        hv = self.port.holdings_value(prices) or 1.0
        for r, (iid, sh) in enumerate(sorted(self.port.holdings.items())):
            v = sh * prices.get(iid, 0.0)
            vals = [INST_NAME(iid), "%.4f" % sh, "€%.2f" % v,
                    "%.0f%%" % (v / hv * 100)]
            for c, txt in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(txt))
        tot = self.port.total_value(prices)
        pnl = self.port.pnl(prices)
        pct = self.port.pnl_pct(prices)
        col = GREEN if pnl >= 0 else RED
        ur = self.port.unrealized_pnl(prices)
        rl = self.port.realized_pnl()
        cur = GREEN if ur >= 0 else RED
        crl = GREEN if rl >= 0 else RED
        self.sum_lbl.setText(
            "%s: €%.2f    %s: €%.2f    "
            "<span style='color:%s'>%s: €%.2f (%.1f%%)</span><br>"
            "<span style='color:%s'>%s: €%.2f</span>&nbsp;&nbsp;&nbsp;&nbsp;"
            "<span style='color:%s'>%s: €%.2f</span>"
            % (T("cash"), self.port.cash, T("total"), tot, col, T("pnl"),
               pnl, pct, cur, T("unreal"), ur, crl, T("real"), rl))
        self.sum_lbl.setTextFormat(Qt.TextFormat.RichText)
        tips = E.analyze(self.port, prices)
        self.tips_lbl.setText("\n".join("• " + tip_text(t) for t in tips)
                              or "-")

    def _refresh_all(self):
        if not self.mode_live and self.sim_date:
            self.date_lbl.setText("%s: %s" % (T("date"), self.sim_date))
        else:
            self.date_lbl.setText("")
        self.slider.setVisible(not self.mode_live)
        self.fwd_btn.setVisible(not self.mode_live)
        self._refresh_market()
        self._refresh_port()
        prices = self.prices_held()
        tot = self.port.total_value(prices)
        pnl = self.port.pnl(prices)
        col = GREEN if pnl >= 0 else RED
        self.money_lbl.setText(
            "<span>%s: €%.0f</span>   "
            "<span style='color:%s'>%s: €%.0f</span>"
            % (T("total"), tot, col, T("pnl"), pnl))
        self.money_lbl.setTextFormat(Qt.TextFormat.RichText)


def INST_NAME(iid):
    return E.INST_BY_ID[iid]["name"]


def main():
    app = QApplication(sys.argv)
    win = Main()
    win.show()
    try:  # Dravenlock: stille update-check (uit te zetten; Ctrl+Shift+U = met de hand)
        import drave_update
        drave_update.start(win, 'DraveBeurs', '1.0.1')
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
