#!/usr/bin/env python3
"""
Main file to run the app. 

'python index.py' will run the app on your local machine.

Auther: Derrick Lewis
"""
import os
from dotenv import load_dotenv
from dash import  dcc, html
from dash.dependencies import Input, Output, State
import dash_auth
import plotly.io as pio
import dash_bootstrap_components as dbc
# from google.cloud import secretmanager
from plotly_theme_light import plotly_light
from main import server, app
from apps import home, page1, page2

pio.templates["plotly_light"] = plotly_light
pio.templates.default = "plotly_light"
load_dotenv()

# Access environment variables

# PROJECT_ID = os.getenv('GCP_PROJECT')
# print(PROJECT_ID)


# def access_secret_version(secret_id, version_id="latest"):
#     client = secretmanager.SecretManagerServiceClient()
#     name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
#     response = client.access_secret_version(name=name)
#     return response.payload.data.decode('UTF-8')


# UN = access_secret_version("UN")
# PW = access_secret_version("PW")

UN = 'admin'
PW = 'admin'

VALID_USERNAME_PASSWORD_PAIRS = {
    UN: PW
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)


COMPANY_LOGO ="DATALOGO.jpg"

# building the navigation bar
# https://github.com/facultyai/dash-bootstrap-components/blob/master/examples/advanced-component-usage/Navbars.py
dropdown_disc = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Home", href="/home"),
        dbc.DropdownMenuItem("Analysis", href="/analysis"),
        dbc.DropdownMenuItem("Dashboard", href="/dashboard")
    ],
    nav=True,
    in_navbar=True,
    label="Pages",
)

navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(
                        html.Img(src=app.get_asset_url(COMPANY_LOGO), height="50px"),
                         ),
                    dbc.Col(
                        dbc.NavbarBrand("Consumer Review Analysis",
                            style={
                            # 'font-family': 'plain',
                            'color': 'grey',
                            'font-weight': 'light',
                            'font-size': '1.9rem',
                            'margin-top': '1rem',
                            'margin-left': '1rem'
                            }
                            )
                    )
                ],
                align="center",
                className="g-0"
            ),
            href="/home",
            style={'text-decoration':'none'}
            ),
        
        dbc.NavbarToggler(id="navbar-toggler2"),
        dbc.Collapse(
            dbc.Nav(
                # right align dropdown menu with ml-auto className
                [],
                className="ml-auto",
                navbar=True),
            id="navbar-collapse2",
            navbar=True,
        ),
        dbc.NavbarToggler(id="navbar-toggler3"),
        dbc.Collapse(
            dbc.Nav(
                # right align dropdown menu with ml-auto className
                [],
                className="ml-auto",
                navbar=True),
            id="navbar-collapse3",
            navbar=True,
        ),
        dbc.NavbarToggler(id="navbar-toggler4"),
        dbc.Collapse(
            dbc.Nav(
                # right align dropdown menu with ml-auto className
                [],
                className="ml-auto",
                navbar=True),
            id="navbar-collapse4",
            navbar=True,
        ),
        dbc.NavbarToggler(id="navbar-toggler5"),
        dbc.Collapse(
            dbc.Nav(
                # right align dropdown menu with ml-auto className
                [dropdown_disc],
                className="ml-auto",
                navbar=True),
            id="navbar-collapse5",
            navbar=True,
        ),
        
    ]),
    color="white",
    dark=False,
    className="mb-4",
)


def toggle_navbar_collapse(n, is_open):
    """Toggle navbar-collapse when clicking on navbar-toggler"""
    if n:
        return not is_open
    return is_open


for i in [2]:
    app.callback(
        Output(f"navbar-collapse{i}", "is_open"),
        [Input(f"navbar-toggler{i}", "n_clicks")],
        [State(f"navbar-collapse{i}", "is_open")],
    )(toggle_navbar_collapse)

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    navbar,
    html.Div(id='page-content', style={
        'margin-right': '70px',
        'margin-left': '50px'
    }),
    html.Div(
        [
            dcc.Markdown("""
                        Updated on November 2023
                        """,
                             style={
                                 'font-family': 'plain',
                                 'color': 'grey',
                                 'font-weight': 'light',
                                 'align': 'right'
                             }),
        ],
        id='footer', style={
        'margin-top': '250px',
        'margin-right': '70px',
        'margin-left': '50px',
        'float': 'right'
    })

] )


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    """
    This function is used to route the user to the correct page based on the url
    """
    print(pathname)
    if pathname == '/':
        return home.layout
    elif pathname == '/home':
        return home.layout
    elif pathname == '/analysis':
        return page1.layout
    elif pathname == '/dashboard':
        return page2.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)