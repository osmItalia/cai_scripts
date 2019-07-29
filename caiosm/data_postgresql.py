import matplotlib.pyplot as plt
import psycopg2
import geopandas as gpd


class CaiOsmPg():
    """Function to work with route data imported into PostgreSQL/PostGIS
       database with osm2pgsql"""

    def __init__(self, dbconnection, outdir="/tmp", prefix='planet_osm',
                 network='lwn', separator='|', debug=False):
        """Inizialize

        :param obj dbconnection: a psycopg2 connection
        :param str outdir: the directory where to save file with info
        :param str prefix: the prefix used in osm2pgsql
        :param str network: the network tag to consider
        :param str separator: the separator string for CSV output
        :param bool debug: set debug
        """
        self.conn = psycopg2.connect(dbconnection)
        self.outdir = outdir
        self.prefix = prefix
        self.sep = separator
        self.regsql = None
        self.regions = None
        self.cai_where = "route='hiking' and (tags ? 'cai_scale' or operator" \
                         " in ('CAI', 'Club Alpino Italiano') or tags ? " \
                         "'source:ref')"
        if network:
            self.cai_where += " and tags->'network'='{}'".format(network)
        self.debug = debug

    def _execute(self, query):
        """Execute a query using psycopg2 and return value as list

        :param str query: a valid SQL query
        """
        if self.debug:
            print(query)
        cur = self.conn.cursor()
        cur.execute(query)
        out = cur.fetchall()
        cur.close()
        return out

    def set_administrative_bounds(self, adminlevel='4', others="tags ? 'ISO3166-2' and tags ? 'ref:ISTAT'"):
        """Create the SQL query for administrative boundaries

        :param str adminlevel: the OSM admin_level value to query
        :param str others: other SQL where statement additional to
                           admin_level=adminlevel and boundary='administrative'
        """
        sql = "select name as reg, st_union(way) as poly from {pre}_polygon " \
              "where admin_level='{lev}' and boundary='administrative'".format(pre=self.prefix,
              lev=adminlevel)
        if others:
            sql += " and {}".format(others)
        sql += " group by name"
        self.regsql = sql

    def get_administrative_bounds(self, adminlevel=4, others="tags ? 'ISO3166-2' and tags ? 'ref:ISTAT'"):
        """Return a list of tuples containin regions name and geom

        :param str adminlevel: the OSM admin_level value to query
        :param str others: other SQL where statement additional to
                           admin_level=adminlevel and boundary='administrative'
        """
        self.set_administrative_bounds(adminlevel, others)
        self.regions = self._execute(self.regsql)
        return True

    def route_count_lenght(self):
        """Return the count and lenght of routes"""
        if self.regsql:
            sql = "select reg, count(osm_id), round(cast(sum(st_length(" \
                  "ST_Intersection(way, poly))) / 1000 as numeric), 2) as " \
                  "km_CAI from ({reg}) as regioni, (select osm_id, way from " \
                  "{pre}_line where {cai}) as cai where ST_intersects(way, " \
                  "poly) group by reg order by reg".format(reg=self.regsql,
                                                           pre=self.prefix,
                                                           cai=self.cai_where)
        else:
            sql = "select count(osm_id), sum(st_length(way))/1000 as km_cai " \
                  "from {pre}_line where {cai}".format(pre=self.prefix,
                                                       cai=self.cai_where)
        return self._execute(sql)

    def not_route_lenght(self, highways=None):
        """NOT WORKING"""
        if self.regsql:
            sql = "select reg, round(cast(sum(st_length(ST_Intersection(way," \
                  " poly))) / 1000 as numeric), 2) as km_noCAI from ({reg}) " \
                  "as regioni, (select l.way as way from {pre}_line as l," \
                  "(select way from {pre}_line where {cai}) as r where "
            if highways:
                  sql += "l.highway in ({})".format(','.join(highways))
            else:
                  sql += "l.highway is not null"

            sql += " and not ST_Within(l.way, r.way)) as" \
                   " nocai where ST_intersects(nocai.way, poly) group by reg" \
                   " order by reg;"
            sql = sql.format(reg=self.regsql, pre=self.prefix,
                             cai=self.cai_where)
        else:
            sql = "select sum(st_length(l.way))/1000 as km_nocai from " \
                  "{pre}_line as l, (select way from planet_osm_line where " \
                  "{cai}) as r where l.highway is not null and not " \
                  "ST_Within(l.way, r.way);".format(pre=self.prefix,
                                                    cai=self.cai_where)
        return self._execute(sql)

    def print_csv(self, regions=True, total=False, highways=None):
        if not self.regions and regions:
            self.set_administrative_bounds()
        routes = self.route_count_lenght()
        if total:
            noroutes = self.not_route_lenght(highways=highways)
            if len(routes) == len(noroutes):
                for i in range(len(routes)):
                    vals = list(routes[i])
                    vals.append(noroutes[i][1])
                    print(self.sep.join(map(str,vals)))
                return True
        for i in range(len(routes)):
            print(self.sep.join(map(str,routes[i])))
        return True

    def _print(output, base=None, paths=None):
        if base:
            base = base.plot(color='grey', edgecolor='black')
            if paths:
                paths.plot(ax=base, color='red')
        else:
            if paths:
                paths.plot(color='red')
        plt.savefig(output)

    def print_italy(self, fname='cai_map_italy.png'):
        """Create an simple map for the entire Italy with routes"""
        paths = gpd.read_postgis("select * from planet_osm_line where {}".format(self.cai_where),
                                 self.conn, geom_col='way',
                                 crs={'init': u'epsg:32632'})
        region = gpd.read_postgis(self.regsql, self.conn, geom_col='poly',
                                  crs={'init': u'epsg:32632'})
        self._print(region, paths)

    def print_region(self, region):
        """Create an simple map for the selected region with routes"""
        paths = gpd.read_postgis("select distinct cai.* from (select name as "\
                                 "reg, st_union(way) as poly from planet_osm" \
                                 "_polygon where admin_level='4' and boundary" \
                                 "='administrative' and tags ? 'ISO3166-2' " \
                                 "and tags ? 'ref:ISTAT' and name='{REG}' " \
                                 "group by name) as lig, (select * from " \
                                 "planet_osm_line where {CAIWHERE}) as cai " \
                                 "where ST_intersects(way, poly)".format(REG=region,
                                 CAIWHERE=self.cai_where), self.conn,
                                 geom_col='way', crs={'init': u'epsg:32632'})
        region = gpd.read_postgis("select name as reg, st_union(way) as poly" \
                                  " from planet_osm_polygon where admin_level"\
                                  "='4' and boundary='administrative' and " \
                                  "tags ? 'ISO3166-2' and tags ? 'ref:ISTAT' " \
                                  "and name='{REG}' group by name".format(REG=region),
                                  self.conn, geom_col='poly',
                                  crs={'init': u'epsg:32632'})
        self._print(region, paths)

    def print_all_regions(self):
        """Create an simple map for all the regions with routes"""
        if not self.regions:
            self.get_administrative_bounds()
        for region in self.regions:
            self.print_region(region[0])
