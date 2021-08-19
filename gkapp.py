from os.path import dirname, join

import pandas as pd
import numpy as np

from bokeh.embed import server_document
from bokeh.layouts import column, layout, row
from bokeh.models import Legend, DataTable, TableColumn, Band, ColumnDataSource, Select, Div
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.io import curdoc


filename =  open(join(dirname(__file__), "data/world_bank_indicators.csv"))
data = pd.read_csv(filename)
comparison_filename =   open(join(dirname(__file__), "data/unicef_indicators.csv"))
comp_data = pd.read_csv(comparison_filename)

indicators = list(set(data['Indicator']))
indicators.sort()
locs = sorted(list(set(data['Location'])))

#Make sure that axis labels correctly correspond to the indicator units
axis_map = data[['Indicator','Indicator units']].drop_duplicates()
axis_map = dict(axis_map.values)

#Input controls
indicator_c = Select(title="Indicator", value="Immunization, DPT", options = indicators, sizing_mode="stretch_width")
location_c = Select(title="Location", value="World", options = locs, sizing_mode="stretch_width")
    
source = ColumnDataSource(data=dict(year=[], world_bank=[], unicef=[]))

TOOLTIPS = [ 
("Year", "@year"),
("World Bank", "@world_bank"),
("Unicef", "@unicef")
]

p = figure(height=600, width=700, sizing_mode='stretch_width', tooltips=TOOLTIPS)
p.y_range.start=0
p.line(x="year", y="world_bank", source=source, color='#002F54', legend_label="World Bank")                      

#Previous year comparisons
p.line(x="year", y="unicef", source=source, color='#00AEEF', legend_label="Unicef")
    
p.legend.location = 'top_center'
p.legend.orientation = 'horizontal'
p.legend.spacing = 10

columns = [TableColumn(field='year', title="Year"), TableColumn(field='world_bank', title="World Bank"),
            TableColumn(field='unicef',  title="Unicef")]
data_table = DataTable(source=source, columns = columns, width=320, sizing_mode='stretch_height', index_position=None)

def select_options():
    location_val = location_c.value
    indicator_val = indicator_c.value
    
    #filter the data to return the dataframe for the selected values
    selected = data[(data['Location']==location_val) & (data['Indicator']==indicator_val)][['Year','Scenario type', 'Mean estimate']].drop_duplicates().pivot(index='Year', columns='Scenario type', values='Mean estimate').reset_index()
    subset2 = comp_data[(comp_data['Location']==location_val) & (comp_data['Indicator']==indicator_val)][['Year','Scenario type', 'Mean estimate']].drop_duplicates().pivot(index='Year', columns='Scenario type', values='Mean estimate').reset_index()
    if subset2.shape[0]>0:
        selected = selected.merge(subset2, on='Year', suffixes=('_wb','_unicef'))
    elif selected.shape[0]==0:
        selected = subset2
        selected.columns=['Year', 'Reference_unicef']
        selected['Reference_wb'] = ''
    else:
        selected.columns = ['Year', 'Reference_wb']
        selected['Reference_unicef'] = ''

    return selected


def update():
    df = select_options()

    p.xaxis.axis_label='Year'
    p.yaxis.axis_label=axis_map[indicator_c.value]
    p.title.text="%s in %s" % (indicator_c.value, location_c.value)
    
    source.data = dict(
        year=df['Year'],
        world_bank=df['Reference_wb'],
        unicef=df['Reference_unicef']
    )

desc = Div(text=open(join(dirname(__file__), "description.html")).read(), sizing_mode="stretch_width")

controls = [indicator_c, location_c]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

inputs = column(*controls, data_table, width=350)

l = column(desc, row(inputs,p), sizing_mode="scale_both")

update()  # initial load of the data

curdoc().add_root(l)
curdoc().title = "Comparing Indicators"