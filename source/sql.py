import random
import sys
from typing import *
import time
import threading

from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, Qt, QObject, QThread, QAbstractListModel, QByteArray, QModelIndex, QTimer, QVariant
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlDriver
from PyQt5.QtQml import qmlRegisterType

class NotificationDelay(QTimer):
    notification = pyqtSignal(str)
    def __init__(self, parent, table, interval=100):
        super().__init__(parent)
        self.table = table
        self.setSingleShot(True)
        self.setInterval(interval)
        self.timeout.connect(self.onTimeout)

    @pyqtSlot()
    def onTimeout(self):
        self.notification.emit(self.table)

class Database(QObject):
    notification = pyqtSignal(str)
    instance = None
    def __init__(self, parent):
        super().__init__(parent)
        self.db = QSqlDatabase.addDatabase("QSQLITE", "database")
        self.db.setConnectOptions("QSQLITE_OPEN_URI;QSQLITE_ENABLE_SHARED_CACHE")
        self.db.setDatabaseName("file::memory:")
        self.db.open()
        Database.instance = self

        self.timers = {}

    @pyqtSlot(str)
    def onNotification(self, table):
        if not table in self.timers:
            timer = NotificationDelay(None, table)
            timer.notification.connect(self.onDelayNotification)
            self.timers[table] = timer

        if not self.timers[table].isActive():
            self.notification.emit(table)
            self.timers[table].start()

    def onDelayNotification(self, table):
        self.notification.emit(table)

class Connection(QObject):
    notification = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None

    def connect(self):
        name = f"db_{random.randint(0, 2**32)}"
        db = QSqlDatabase.cloneDatabase("database", name)
        db.open()
        db.driver().notification[str].connect(Database.instance.onNotification)
        Database.instance.notification.connect(self.relayNotification)

        self.db = db

    def enableNotifications(self, table):
        if not table in self.db.driver().subscribedToNotifications():
            self.db.driver().subscribeToNotification(table)
    
    def disableNotifications(self, table):
        if table in self.db.driver().subscribedToNotifications():
            self.db.driver().unsubscribeFromNotification(table)

    def doQuery(self, q):
        if type(q) == str:
            query = QSqlQuery(self.db)
            query.prepare(q)
            q = query
        
        ctr = 0
        while not q.exec():
            if ctr > 100:
                print(q.lastQuery(), q.boundValues(), "TIMEOUT")
                break
            if q.lastError().nativeErrorCode() == "6":
                QThread.msleep(10)
                ctr += 1
                continue
            else:
                print(q.lastQuery(), q.boundValues(), q.lastError().text())
                break
        return q

    @pyqtSlot(str)
    def relayNotification(self, table):
        self.notification.emit(table)

class QueryRunnableSignals(QObject):
    done = pyqtSignal(bool, str)
    def __init__(self):
        super().__init__()
    
class QueryRunnable(QThread):
    def __init__(self, query, partial):
        super().__init__()
        self.query = query
        self.signals = QueryRunnableSignals()
        self.errored = None
        self.results = []
        self.partial = partial
        self.stopping = False

    def runQuery(self, query, partial, limit=0):
        q = self.conn.doQuery(query)
        if self.stopping:
            return

        self.errored = q.lastError().isValid()
        if self.errored:
            self.signals.done.emit()
            return
        self.results = []
        while q.next():
            self.results += [q.record()]
        q.finish()

        if self.stopping:
            return
        
        self.signals.done.emit(partial and len(self.results) == limit, self.query)

    def run(self):
        self.conn = Connection()
        self.conn.connect()

        if self.partial:
            limit = 64
            self.runQuery(self.query[:-1] + f" LIMIT {limit};", True, limit)
        else:
            self.runQuery(self.query, False)

    def stop(self):
        self.stopping = True

class Sql(QAbstractListModel):
    queryChanged = pyqtSignal()
    resultsChanged = pyqtSignal()
    partialChanged = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)

        self.results = []

        self.conn = Connection(self)
        self.conn.connect()
        self.conn.notification.connect(self.onNotification)

        self.errored = False
        self.currentQuery = ""
        self.fieldNames: Dict[int, QByteArray] = {}

        self.reloadTimer = QTimer(self)
        self.reloadTimer.setSingleShot(True)
        self.reloadTimer.timeout.connect(self.reload)

        self.runnable = None

        self._partial = False 
        self._debug = False

    @pyqtProperty(bool, notify=queryChanged)
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        
    @pyqtProperty(str, notify=queryChanged)
    def query(self):
        return self.currentQuery

    @query.setter
    def query(self, value):
        if value == self.currentQuery:
            return
        self.setQuery(value)

    def setQuery(self, value):
        different = (value != self.currentQuery)
        if different:
            self.queryChanged.emit()

        self.currentQuery = value
        if not value:
            self.reset()
            return
        
        if self._debug:
            print("RUN")

        self.runQuery(self.currentQuery, different)

    def runQuery(self, query, partial):
        if self.runnable:
            self.runnable.stop()
        self.runnable = QueryRunnable(query, partial)
        self.runnable.signals.done.connect(self.onDone)
        self.runnable.start()

    @pyqtSlot(bool, str)
    def onDone(self, partial, query):
        if query != self.currentQuery:
            print("STALE")
            print(query, self.currentQuery)
            return

        self.errored = self.runnable.errored
        if self.errored:
            self.reset()
            return
        
        self._partial = partial
        self.partialChanged.emit()

        newResults = self.runnable.results

        if self._debug:
            print(len(self.results), len(newResults), query)

        self.updateResults(newResults)
        self.roleNames()

        if partial:
            self.runQuery(self.currentQuery, False)
    
    def updateResults(self, newResults):
        def find(a, b):
            for i, e in enumerate(a):
                if e == b:
                    return i
            return -1

        if newResults:
            self.updateFieldNames(newResults[0])
        else:
            self.fieldNames = {}
        
        if len(self.results) == 0 and len(newResults) != 0:
            self.beginInsertRows(QModelIndex(), 0, len(newResults)-1)
            self.results = newResults
            self.endInsertRows()
            self.resultsChanged.emit()
            return

        if len(self.results) != 0 and len(newResults) == 0:
            self.beginRemoveRows(QModelIndex(), 0, len(self.results)-1)
            self.results = []
            self.endRemoveRows()
            self.resultsChanged.emit()
            return

        totalResults = len(newResults)

        changed = False
        i = 0
        while newResults and i < len(self.results):
            if self.results[i] == newResults[0]:
                newResults.pop(0)
                i += 1
                continue

            srcIdx = find(self.results[i:], newResults[0])
            dstIdx = find(newResults, self.results[i])
            if srcIdx == -1 and dstIdx == -1:
                self.results[i] = newResults.pop(0)
                self.dataChanged.emit(self.index(i), self.index(i))
                changed = True
                i += 1
                continue
            
            if srcIdx > 0:
                self.beginRemoveRows(QModelIndex(), i, i+srcIdx-1)
                self.results = self.results[:i] + self.results[i+srcIdx:]
                self.endRemoveRows()
                changed = True
        
            if dstIdx > 0:
                self.beginInsertRows(QModelIndex(), i, i+dstIdx-1)
                self.results = self.results[:i] + newResults[:dstIdx] + self.results[i:]
                self.endInsertRows()
                changed = True
                newResults = newResults[dstIdx:]
                i += dstIdx

        if newResults:
            self.beginInsertRows(QModelIndex(), i, i+len(newResults)-1)
            self.results += newResults
            self.endInsertRows()
            changed = True
        
        if len(self.results) > totalResults:
            self.beginRemoveRows(QModelIndex(), totalResults, len(self.results))
            self.results = self.results[:totalResults]
            self.endRemoveRows()
            changed = True

        if changed:
            self.resultsChanged.emit()

    def data(self, index, role):
        value = QVariant()
        if role > Qt.UserRole:
            column = role - Qt.UserRole - 1
            row = index.row()
            if row < len(self.results):
                value = self.results[row].value(column)
        elif role == Qt.UserRole:
            row = index.row()
            if row < len(self.results):
                value = self.results[row].value(0)
        return value

    @pyqtSlot(int, result='QVariant')
    def get(self, index):
        if len(self.results) <= index:
            return None

        out = {}
        record = self.results[index]
        for i in range(len(record)):
            out[record.fieldName(i)] = record.value(i)
        return out
    
    @pyqtProperty(int, notify=resultsChanged)
    def length(self):
        return len(self.results)

    def updateFieldNames(self, record):
        self.fieldNames = {}
        self.fieldNames[Qt.UserRole] = QByteArray(("modelData").encode("utf-8"))
        for i in range(len(record)):
            self.fieldNames[Qt.UserRole + i + 1] = QByteArray(("sql_" + record.fieldName(i)).encode("utf-8"))

    def roleNames(self):
        return self.fieldNames

    def rowCount(self, parent):
        return len(self.results)

    def reset(self):
        self.beginResetModel()
        self.fieldNames = {}
        self.results = []
        self.endResetModel()

    @pyqtSlot()
    def forceReset(self):
        self.beginResetModel()
        self.endResetModel()

    @pyqtSlot(str)
    def onNotification(self, table):
        if table in self.currentQuery:
            if not self.reloadTimer.isActive():
                self.reloadTimer.start(random.randint(50,150))

    @pyqtSlot()
    def reload(self):
        self.setQuery(self.currentQuery)

    @pyqtProperty(bool, notify=partialChanged)
    def partial(self):
        return self._partial

def registerTypes():
    qmlRegisterType(Sql, "gui", 1, 0, "Sql")