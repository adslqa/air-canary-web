from __future__ import print_function
from flask.ext.script import Command
from model.models import AirNowForecastArea, AirNowMonitoringSite, AirNowHourly, AirNowReportingArea, Area
from geoalchemy2 import Geometry
import sqlalchemy.orm
from sqlalchemy.exc import IntegrityError

class ParseCommand(Command):
    tmpdir = '/tmp'
    cache_days = 1

    def run(self):

        from db import Session
        session = Session()

        # Special filename for most recent file
        if self.filename == 'recent':
            self.filename = self.recent()

        lines = self.get_lines()
        attrs = self.attributes()

        try:
            for line in lines:
                vals = line.strip().split('|')
                kvals = dict(zip(attrs, vals))

                model_inst = self.model()
                for col, val in kvals.items():
                    val = self.cleanval(col, val)
                    setattr(model_inst, col, val)
                
                try:
                    session.merge(model_inst)
                    session.commit()
                    print('.', end='')
                except Exception as inst:
                    session.rollback()
                    print('x', end='')
                    raise inst

        except Exception as inst:
            session.close()
            raise inst

        session.close()
        print('\nDone')


    def attributes(self):
        return [prop.key for prop in sqlalchemy.orm.class_mapper(self.model).iterate_properties
                if isinstance(prop, sqlalchemy.orm.ColumnProperty)]

    def get_lines(self):

        import datetime
        import os

        filepath = '{0}/{1}'.format(self.tmpdir, self.filename)

        if not os.path.isfile(filepath):
            print('Downloading file')
            self.download_file()
        else:
            today = datetime.datetime.today()
            modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            duration = today - modified_date
            if duration.days > self.cache_days:
                print('Downloading file')
                self.download_file()

        content = []
        with open(filepath) as f:
            content = f.readlines()

        return content

    def download_file(self):
        ftp = self.ftp()
        ftp.cwd(self.ftp_dir)
        ftp.retrbinary('RETR {0}'.format(self.filename), open('{0}/{1}'.format(self.tmpdir, self.filename), 'wb').write)
        ftp.quit()

    def ftp(self):

        from ftplib import FTP
        import AcConfiguration
        c = AcConfiguration.AcConfiguration()
        ftp_user = c.settings['airnow']['username']
        ftp_pass = c.settings['airnow']['password']

        ftp = FTP('ftp.airnowapi.org', ftp_user, ftp_pass)
        return ftp

    def recent(self):

        ftp = self.ftp()
        files = ftp.nlst(self.ftp_dir)
        ftp.quit()
        
        files = [f for f in files if f[-4:] == '.dat']

        files.sort()
        return files.pop()

    def cleanval(self, col, val):

        if col == 'valid_time' and val == '':
            return '00:00:00'

        # mm/dd/yy
        import re
        m = re.match(r'([0-9]{2})/([0-9]{2})/([0-9]{2})', val)
        if m is not None:
            val = '20{0}'.format('-'.join([m.group(3), m.group(1), m.group(2)]))
        return val if len(val) > 0 else None
        

class ForecastAreas(ParseCommand):
    " Parse air now forecast areas - actual areas"
    ftp_dir = 'Locations'
    filename = 'reporting_area_locations_v2.dat'
    model = AirNowForecastArea

class MonitoringSites(ParseCommand):
    " Parse air now monitoring sites "
    ftp_dir = 'Locations'
    filename = 'monitoring_site_locations.dat'
    model = AirNowMonitoringSite

class Hourly(ParseCommand):
    " Parse air now hourly data "
    ftp_dir = 'HourlyData'
    filename = 'recent'
    model = AirNowHourly

class ReportingAreas(ParseCommand):
    " Parse air now reporting areas - individual reports "
    ftp_dir = 'ReportingArea'
    filename = 'reportingarea.dat'
    model = AirNowReportingArea

class LoadAreas(Command):

    def run(self):

        from db import Session
        session = Session()

        an_areas = session.query(AirNowForecastArea)
        for a in an_areas:

            area = Area()
            area.name = a.reporting_area
            area.country_iso = a.country_code
            area.state_province = a.state_code
            txt = 'POINT({} {})'.format(a.longitude, a.latitude)
            area.location = Geometry('Point').bind_expression(txt)

            try:
                session.merge(area)
                session.commit()
                print('.', end='')
            except IntegrityError as inst:
                session.rollback()
                print('-', end='')
            except Exception as inst:
                session.rollback()
                print('x', end='')
                raise inst


         
        #from db import engine
        #engine.execute("""
        #    INSERT INTO area (name, country_iso, state_province, location)
        #    SELECT reporting_area, country_code, state_code, ST_GeomFromText('POINT(' || longitude || ' ' || latitude || ')')
        #    FROM air_now_forecast_area
        #""")

class LoadAreaData(Command):

    def run(self):
        
        pass
