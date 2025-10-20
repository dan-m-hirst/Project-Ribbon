# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 22:54:22 2025

@author: Daniel
"""

# Webapp time. Want to be able to generate visuals for comparing cohorts of 
# players in FM, preferably on scatterplots. Could have scatterplots of 
# metrics with dot colour by league strength. 
# Could also have percentile performance vs percentile cost, with a guide at 
# x=y.
# Maybe add tabs?
# go to http://localhost:8050/ for locally-hosted dashboard
# plots are plotly. Info here: https://plotly.com/python/

# TO-DO:
# 2. ADD SECOND STAT SCATTER FOR TAB 1
# 3. GET THE UPDATING UPLOAD WORKING
# 4. GET LEAGUE FILTER (OR SLIDER) WORKING
# 5. ANOTHER TAB FOR SEARCHABLE TABLE

import pandas as pd
from dash import Dash, dcc, html, Input, Output, callback, dash_table
import os
import plotly.express as px
import plotly.graph_objects as go
import statistics as st
import numpy as np
from matplotlib.colors import to_hex
from data_import import data_import, get_statcols, do_all
from sys import argv
from weblaunch import launch_localhost

#region ########## Colour palette ###############
s_bgcolor = "#001101"
s_pointcolor = "" # Probably want these R->G gradient-ed by league ranking. color='league_weight' in px.scatter
s_linecolor = "#699269"
s_textcolor = "#FFFFFF"
s_axiscolor = "#006800"
s_gridcolor = "#006800"
s_boxcolor = "#9ACA90"
#endregion ######################################

#region ############ DATA LOAD ##################

debugpath = os.path.join(
    r"\Users\Daniel\Documents\Sports Interactive",
    "Football Manager 2024","JP_DM_scout.html"
    )


if not (len(argv) -1):          # checks for no-args run, i.e. VS Code run rather than CLI
    datapath = debugpath 
    chrome_path = os.path.join(
        r"C:\Program Files (x86)\Google\Chrome",
        "Application\chrome.exe"
        )
    exclude_free_agents = False
else:
    datapath = argv[1]      # only use argument when we have it
    chrome_path = argv[2]
    exclude_free_agents = argv[3]

if exclude_free_agents == 'TRUE':
    data = do_all(datapath).query('AP > 0')
else:
    data = do_all(datapath)
statcols = get_statcols(data)

## use dcc.Upload for this??????
# Data clean occurs in data_import module upstream

#endregion #######################################


#region ########### GRAPH CREATORS ###############
def create_dynamic_scatter(data,x_var,y_var,ttl):
    
    fig = px.scatter(
        data, x = x_var, y = y_var,
        hover_data={"Name":True,"Division":True,
                    "Age":True, "Mins":True,
                     x_var:True, y_var:True}, 
        title = ttl,
        color = 'League Strength', 
        color_continuous_scale = 'temps_r'
        )
    fig.update_traces(textposition='top center')
    fig.add_vline(x=np.median(data[x_var]).astype('float'), line_color = s_linecolor)
    fig.add_hline(y=np.median(data[y_var]).astype('float'), line_color = s_linecolor)
    fig.update_layout(plot_bgcolor = s_bgcolor)
    fig.update_layout(paper_bgcolor = s_bgcolor)
    fig.update_layout(font_color = s_textcolor)
    fig.update_layout(title_font_color = s_textcolor)
    fig.update_xaxes(
        showline = True, linewidth = 2, 
        linecolor = s_gridcolor, gridcolor = s_gridcolor, 
        mirror = True, zeroline = False
        )
    fig.update_yaxes(
        showline = True, linewidth = 2, 
        linecolor = s_gridcolor, gridcolor = s_gridcolor, 
        mirror = True, zeroline = False
        )
    return fig

############## MONEYLINE ####################

def create_perc_scatter(data, minstrength, ttl):

    fig = px.scatter(
        data[data['League Strength'] >= minstrength], 
        x = 'Perc_Cost', y = 'Perc_Score',
        hover_data={
            "Name":True,"Division":True,
            "Age":True, "Mins":True,
            'AP':True, 'Projected Cost':True,
            'Perc_Cost':True, 'Perc_Score':True
            }, 
        title = ttl,
        color = 'League Strength', 
        color_continuous_scale = 'temps_r'
        )
    fig.update_traces(textposition='top center')
    fig.add_trace(
        go.Scatter(
            x = data['Perc_Cost'], y = data['Perc_Cost'], 
            name = "Value Line", line_shape = 'linear',
            line_color = s_linecolor
            )
        )
    fig.update_layout(plot_bgcolor = s_bgcolor)
    fig.update_layout(paper_bgcolor = s_bgcolor)
    fig.update_layout(font_color = s_textcolor)
    fig.update_layout(title_font_color = s_textcolor)
    fig.update_xaxes(
        showline = True, linewidth = 2, 
        linecolor = s_gridcolor, gridcolor = s_gridcolor, 
        mirror = True, zeroline = False
        )
    fig.update_yaxes(
        showline = True, linewidth = 2, 
        linecolor = s_gridcolor, gridcolor = s_gridcolor, 
        mirror = True, zeroline = False
        )
    return fig

#endregion ######################################

fig1 = create_dynamic_scatter(data,statcols[0],statcols[1],"Dummyfig1")
fig2 = create_perc_scatter(data, 1, 'Percentile Cost vs Score')

#region ############## APP LAYOUT ###############

app = Dash(__name__)

app.layout = html.Div(style={'backgroundColor':s_bgcolor,'color':s_textcolor},
    children=[
        html.H1(
            children="Moneyball App test", 
            className='app-header',
            style={
                'border-color':'black', 'border-bottom':'3px solid white',
                #width':'100%', 'backgroundColor':'black'
            }
            ),
        html.H1(children="     ", id='dummyheader'),
        html.Br(),
        html.Br(),
        html.Br(),
            html.P(children=[html.Br(),(
            "Analyse the performance of various players"
            f" from the file {datapath}"
            )]),
            dcc.Upload(
                id='upload-data',
                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                    'textAlign': 'center','margin': '10px'
                },
                multiple=False
            ),
            html.Div(id='output-data-upload'),    
        # html.Div() #league filtering goes here once I figure out the UI design and how to re-filter data
        # league ranking slider?
        dcc.Tabs([
            dcc.Tab(
                label='Stat Scatters',
                children=[
                    html.Div([
                        dcc.Dropdown(
                            get_statcols(data),
                            id = 'x-axis-dd',
                            value = get_statcols(data)[0],
                            clearable = False,
                            style = {'backgroundColor':s_boxcolor,
                                     'color':'black'}
                        ),
                        dcc.Dropdown(
                            get_statcols(data),
                            id = 'y-axis-dd',
                            value = get_statcols(data)[1],
                            clearable = False,
                            style = {'backgroundColor':s_boxcolor,
                                     'color':'black'}
                        )
                    ],
                    style = {'width':'10%'}
                    ),
                    dcc.Graph(
                        figure = fig1, 
                        id = "first-graph",
                        style = {'width':'50%'}
                        )
                ],
                selected_style = {'backgroundColor':s_gridcolor,'color':'white'}
            ),
            dcc.Tab(
                label = 'Overall Percentile Cost and Score',
                children = [dcc.Graph(figure=fig2)],
                selected_style = {'backgroundColor':s_gridcolor,'color':'white'}
            ),
            dcc.Tab(
                label = 'Table of Scouted Players',
                children = [dash_table.DataTable(
                    id='player_table',
                    data = data.to_dict("records"),
                    columns = [{"name": str(i), "id": str(i)} for i in data.columns],
                    virtualization = True,
                    sort_action = 'native',
                    filter_action = 'native',
                    filter_options = {'case':'insensitive'},
                    fixed_rows = {'headers': True},
                    page_size = 50,
                    style_table = {'height': '1500px'},
                    style_header = {
                        'backgroundColor': s_gridcolor, 'color': 'white',
                        'border-color':'white'
                    },
                    style_filter = {
                        'backgroundColor': s_bgcolor, 'color': 'white', 
                        'border-color':'white'
                    },
                    style_data = {
                        'width': '150px', 'minWidth': '150px', 
                        'maxWidth': '150px','overflow': 'hidden','textOverflow': 'ellipsis',
                        'backgroundColor': s_bgcolor, 'color': s_gridcolor, 
                        'border-color': s_gridcolor
                    }
                )
                ],
                selected_style = {'backgroundColor':s_gridcolor,'color':'white'}
            )
        ],
        colors={'primary':s_gridcolor,'border':s_gridcolor,'background':s_bgcolor},
        style={'backgroundColor':s_bgcolor}
        ), 
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    ],
)

#endregion ######################################

print("Launching visualisations in browser...")

@callback(
    Output('first-graph','figure'),
    Input('x-axis-dd','value'),
    Input('y-axis-dd','value')
)
def update_graph(xaxis_column_name, yaxis_column_name):
    return create_dynamic_scatter(
        data,
        xaxis_column_name,
        yaxis_column_name,
        f'{xaxis_column_name} vs {yaxis_column_name}'
        )

#@callback(
#    Output('output-data-upload','children'),
#    Input('upload-data', 'contents')
#)

# need to build out def update_output(file, leagues):
# need to add league filtration and data upload/clean into here?


print("App initialised. Opening visualisations in Chrome...")

launch_localhost(chrome_path)

if __name__ == "__main__":
    #original was app.run(debug=True) # seems to run things twice
    app.run(debug=False)

print("Ready to go!")

# go to http://localhost:8050/
# plots are plotly. Info here: https://plotly.com/python/