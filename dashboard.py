import dash
import dash_core_components as dcc
import dash_html_components as html
import datetime as dt
import pandas as pd
import numpy as np
import urllib
import zipfile
from plotly import graph_objs as go
import plotly.express as px
from dash.dependencies import Input, Output, State

# SETUP ------------------------------------------------------------------

external_stylesheets = ['https://codepen.io/amyoshino/pen/jzXypZ.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.title = "NYC After New Year's Eve Yellow Taxi Trip Data"
mapbox_access_token = "pk.eyJ1IjoiYmlja2JhY2siLCJhIjoiY2s0d212ZjNoMGJuZjNxcGdubzR5ZGY3bSJ9.rEq_TEbvKdQJKyUTZihO8w"

zone_data = pd.read_csv("taxi_zones.csv")
#taxi_data = pd.read_csv("yellow_tripdata_2019-01.csv",nrows=189254)
taxi_data = pd.read_csv("taxi_data.csv")

colors = {
    'black': '#111111',
    'text': '#cd5c5c',
    'title' : '#FF2E01' 
}


taxi_data["tpep_pickup_datetime"] = pd.to_datetime(taxi_data["tpep_pickup_datetime"])
taxi_data["tpep_pickup_datetime"] = taxi_data["tpep_pickup_datetime"].dt.hour

taxi_data["tpep_dropoff_datetime"] = pd.to_datetime(taxi_data["tpep_dropoff_datetime"])
taxi_data["tpep_dropoff_datetime"] = taxi_data["tpep_dropoff_datetime"].dt.hour

hours = range(0,23)

# PREPROCESSING THE DATA ------------------------------------------------
# preprocessed data : yellow_tripdata_2019-01.csv
# resulted data     : tax_data.csv (includes only January 1st 2019)   

'''
taxi_data = taxi_data[["tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID", "fare_amount", "tip_amount", "passenger_count","trip_distance"]]
taxi_data["tpep_pickup_datetime"] = pd.to_datetime(taxi_data["tpep_pickup_datetime"], format="%Y-%m-%d %H:%M:%S")
taxi_data["tpep_dropoff_datetime"] = pd.to_datetime(taxi_data["tpep_dropoff_datetime"], format="%Y-%m-%d %H:%M:%S")

zone_dict = {} 

for i in zone_data.index:
    valID = zone_data.at[i,'LocationID']
    valx = zone_data.at[i,'X']
    valy = zone_data.at[i,'Y']
    zone_dict[valID] = (valx, valy)

taxi_data['X'] = 0.0
taxi_data['Y'] = 0.0

taxi_data['X_d'] = 0.0
taxi_data['Y_d'] = 0.0

for i in taxi_data.index:
    valID = taxi_data.at[i,'PULocationID']
    valIDd = taxi_data.at[i,'DOLocationID']

    if valID > 263:
        valID = 263
    elif valID == 57:
        valID = 56

    if valIDd > 263:
        valIDd = 263
    elif valIDd == 57:
        valIDd = 56
    print(i)
    (valy, valx) = zone_dict[valID]
    (valyd, valxd) = zone_dict[valIDd]
    taxi_data.at[i,'Y'] = valy
    taxi_data.at[i,'X'] = valx
    taxi_data.at[i,'Y_d'] = valyd
    taxi_data.at[i,'X_d'] = valxd

taxi_data.to_csv('taxi_data2.csv',index=False)
'''

# DASH LAYOUTS, CALLBACKS AND FUNCTIONS --------------------------------

app.layout = html.Div(
    html.Div([
        html.Div(
            [
                html.H1(children="Taxi Trip Data of NYC after  New Year's Eve (1st January) by Egemen Kopuz", className='nine rows'),
            ],className="row"),
        html.Div(
            [
                html.Div(
                [
                     html.Div(
                        [
                            dcc.RangeSlider(
                                id='time-ranger',
                                marks={i: '{}:00'.format(i) for i in range(25)},
                                min=0,
                                max=24,
                                value=[0,24],
                            ),
                        ], className= 'twelve columns'),

                    html.Div(
                        [
                        html.Div(
                            [
                                dcc.Graph(
                                    id = "bar-graph",
                                )
                            ], className= 'six columns'),
                        html.Div(
                            [
                                dcc.Graph(
                                    id = "line-graph",
                                )
                            ], className= 'six columns'),
                        ], className="row"),
                    
                    html.Div(
                       [
                        dcc.RadioItems(
                            id = "radio",
                            options=[
                                {'label': 'Pick-up', 'value': 0},
                                {'label': 'Drop-off', 'value': 1}
                            ],
                            value=0
                        )
                    ], className = 'one columns'),
                    html.Div(
                       [
                        dcc.Graph(
                            id='map-graph',
                            animate=False,
                        )
                    ], className = 'five columns'),
                    html.Div(
                        [
                            dcc.Graph(
                                id = "pie-chart",
                            )
                        ], className= 'six columns'
                    )
               ], className="row"),
            ],
        )
    ], className='ten columns offset-by-one'))
@app.callback(
    Output('line-graph', 'figure'),
    [Input('time-ranger', 'value')])
def line_selection(value):
    value = list(range(value[0],value[1],1))
    dff = taxi_data.loc[taxi_data['tpep_pickup_datetime'].isin(value)]

    layout = go.Layout(
        dragmode="select",
        xaxis=dict(
            title = 'Hours of day',
            showgrid=False,
            nticks = len(value),
        ),
        yaxis=dict(
            title = 'Average Distance Taken (km)',
            showticklabels=True,
            showgrid=False,
        ),
    )

    data = [
        go.Scatter(
            x=dff.groupby("tpep_pickup_datetime", as_index=False).count()["tpep_pickup_datetime"],
            y=dff.groupby("tpep_pickup_datetime", as_index=False).mean()["trip_distance"],
            marker_color='indianred',
            mode='lines+markers'
        )
    ]
    return go.Figure(data=data, layout=layout)


@app.callback(
    Output('map-graph', 'figure'),
    [Input('time-ranger', 'value'),
    Input('radio','value')])
def map_selection(value,valueradio):
    value = list(range(value[0],value[1],1))
    dff = taxi_data[taxi_data['tpep_pickup_datetime'].isin(value)].copy()

    if valueradio == 0:
        mdata = dff.groupby(['X','Y'],as_index=False,sort=False)["fare_amount"].count()
        coordinatesY = mdata['X']
        coordinatesX = mdata['Y']
    else:
        mdata = dff.groupby(['X_d','Y_d'],as_index=False,sort=False)["fare_amount"].count()
        coordinatesY = mdata['X_d']
        coordinatesX = mdata['Y_d']

    magnitudes = mdata['fare_amount']
    
    layout_map = dict(
        autosize=True,
        height=500,
        font=dict(color=colors['black']),
        titlefont=dict(color=colors['black'], size='14'),
        margin=dict(
            l=35,
            r=35,
            b=35,
            t=35
        ),
        hovermode="closest",
        plot_bgcolor='#fffcfc',
        paper_bgcolor='#fffcfc',
        legend=dict(font=dict(size=10), orientation='h'),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style="dark",
            center=dict(
                lon=-73.91251,
                lat=40.7342
            ),
            zoom=9,
        )
    )

    if valueradio == 0:
        colorscale = "Hot"
    else:
        colorscale = "Viridis"

    return {
        "data" :[{
            "type": "densitymapbox",
            "colorbar" : {
                "title" : {
                    "text" : "Number of Rides",
                },
            },
            "lon": coordinatesX,
            "lat": coordinatesY,
            "z" : magnitudes,
            "hoverinfo": "z",
            "mode": "markers",
            "marker": {
                'color': 'rgb(0,0,0)',
                "size": 1,
                "opacity": 0.0001,
            },
            "autocolorscale" : False,
            "zmax" : 500,
            "zmin" : 0,
            "colorscale" : colorscale
        }],
        "layout" : layout_map,
    }

@app.callback(
    Output('pie-chart', 'figure'),
    [Input('time-ranger', 'value')])
def pie_selection(value):
    value = list(range(value[0],value[1],1))
    dff = taxi_data[taxi_data['tpep_pickup_datetime'].isin(value)]

    labels = ['1','2', '3', '4', '5', '6 and more']

    values = [
        (dff['passenger_count'] == 1).sum(),\
        (dff['passenger_count'] == 2).sum(),\
        (dff['passenger_count'] == 3).sum(),\
        (dff['passenger_count'] == 4).sum(),\
        (dff['passenger_count'] == 5).sum(),\
        (dff['passenger_count'] > 5).sum()
    ]
    layout = go.Layout(
        showlegend=True,
        dragmode="select",
        title="Overall number of passengers ",

    )

    dataPieChart = [
        {
        'values': values,
        'type': 'pie',
        'labels' : labels,
        },
    ]

    return go.Figure(data=dataPieChart, layout=layout)

@app.callback(
    Output('bar-graph', 'figure'),
    [Input('time-ranger', 'value')])
def hist_selection(value):
    value = list(range(value[0],value[1],1))
    dff = taxi_data.loc[taxi_data['tpep_pickup_datetime'].isin(value)]
    dff2 = dff[dff['tip_amount'] > 0.0]

    layout = go.Layout(
        barmode='stack',
        showlegend=True,
        dragmode="select",
        xaxis=dict(
            title = 'Hours of day',
            showgrid=False,
            nticks = len(value),
            fixedrange=False
        ),
        yaxis=dict(
            title = 'Number Of Rides',
            showticklabels=True,
            showgrid=False,
            fixedrange=False,
            rangemode='nonnegative',
        )
    )

    data = [
        go.Bar(
            name="Total Rides",
            x=dff.groupby("tpep_pickup_datetime", as_index=False).count()["tpep_pickup_datetime"],
            y=dff.groupby("tpep_pickup_datetime", as_index=False).count()["fare_amount"],
            marker_color='indianred',
        ),
        go.Bar(
            name="Driver received a tip",
            x=dff2.groupby("tpep_pickup_datetime", as_index=False).count()["tpep_pickup_datetime"],
            y=dff2.groupby("tpep_pickup_datetime", as_index=False).count()["tip_amount"],
            marker_color='lightsalmon'
        ),
    ]
    return go.Figure(data=data, layout=layout)

if  __name__ == '__main__':
    app.run_server(debug=True)