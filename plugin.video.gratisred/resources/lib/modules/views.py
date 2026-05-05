# -*- coding: utf-8 -*-

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database

from resources.lib.modules import control


def addView(content):
    try:
        skin = control.skin
        record = (skin, content, str(control.getCurrentViewId()))
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.viewsFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS views (""skin TEXT, ""view_type TEXT, ""view_id TEXT, ""UNIQUE(skin, view_type)"");")
        dbcur.execute("DELETE FROM views WHERE skin = '%s' AND view_type = '%s'" % (record[0], record[1]))
        dbcur.execute("INSERT INTO views Values (?, ?, ?)", record)
        dbcon.commit()
        viewName = control.infoLabel('Container.Viewmode')
        skinName = control.addon(skin).getAddonInfo('name')
        skinIcon = control.addon(skin).getAddonInfo('icon')
        control.infoDialog(viewName, heading=skinName, sound=True, icon=skinIcon)
    except:
        return


def setView(content, viewDict=None):
    for i in range(0, 200):
        if control.condVisibility('Container.Content(%s)' % content):
            try:
                skin = control.skin
                record = (skin, content)
                dbcon = database.connect(control.viewsFile)
                dbcur = dbcon.cursor()
                dbcur.execute("SELECT * FROM views WHERE skin = '%s' AND view_type = '%s'" % (record[0], record[1]))
                view = dbcur.fetchone()
                view = view[2]
                if not view:
                    raise Exception()
                return control.execute('Container.SetViewMode(%s)' % str(view))
            except:
                try:
                    return control.execute('Container.SetViewMode(%s)' % str(viewDict[skin]))
                except:
                    return
        control.sleep(100)


def deleteView():
    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.viewsFile)
        dbcur = dbcon.cursor()
        for t in ['views']:
            try:
                dbcur.execute("DROP TABLE IF EXISTS %s" % t)
                dbcur.execute("VACUUM")
                dbcon.commit()
            except:
                pass
    except:
        pass


