from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime

def create_dropdown(id, names, default_values):
    dropdown= dcc.Dropdown(
        id=id,
        options=[{'label': name.split(':', 1)[0], 'value': name.split(':', 1)[0], 'search': name} for name in names],
        value=default_values,
        multi=True,
        style={'margin-bottom': '20px'}
    )
    return dropdown
# Function to create date picker
def create_date_picker(id):
    return dcc.DatePickerRange(
        id=id,
        min_date_allowed=datetime(2013, 1, 1),
        max_date_allowed=datetime.today(),
        initial_visible_month=datetime.today(),
        start_date=datetime(2020, 6, 1),
        end_date=datetime(2022, 6, 1),
        style={'margin-bottom': '20px'}
    )

def create_button_with_loading(button_id, button_label, loading_id):
    return dbc.Col(
        html.Div([
            dbc.Button(button_label, id=button_id, color="primary"),
            dcc.Loading(id=f"loading-{loading_id}", children=[html.Div(id=f"loading-output-{loading_id}")], type="cube", fullscreen=False)
        ]),
        width="auto",
        style={'overflow': 'visible', 'text-align': 'left'}
    )

def create_slider(id_, min_, max_, step, value):
    return dbc.Col([
        html.Div(
            id=id_+"-value",
            style={
                'text-align': 'center',
                'vertical-align': 'top',
                'line-height': '1',
            }
        ),
        html.Div(
            dcc.Slider(
                id=id_,
                min=min_,
                max=max_,
                step=step,
                value=value,
                marks=None
            ),
            style={
                'width': '95%',
                'margin': '0 auto',
                'transform': 'scale(1.2)',
                'vertical-align': 'bottom',
                'height': '150%',
                'padding-top': '15px',
                'padding-bottom': '0px',
                'padding-left': '0px',
                'padding-right': '0px',
            }
        ),
    ], width=2)

def date_handler(date):
    try:
        date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        try:
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
        except:
            date = date
    return date

def str_to_date(s):
    return datetime.strptime(s, "%Y-%m-%d")

def get_all_clustering_results(misc_connect, n=0):
    if n is not None and n != 0:
        options = []
        dict_ = misc_connect.get_all_clustering_results()
        for document in dict_:
            method = document['method']
            start_date = document['start_date']
            end_date = document['end_date']
            label = f'{method}:{start_date}:{end_date}'
            options.append({'label': label, 'value': label, 'search': label})
        return options
    else:
        return [] 
    

def create_divider():
    return html.Hr(style={
                'borderTop': '1px solid #7B9EB0', 
                'width': '100%',                   
                'margin-top': '50px',             
                'margin-bottom': '75px'           
            })