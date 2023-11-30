from dash import html, dcc
import dash_bootstrap_components as dbc
from main import app
from dotenv import load_dotenv

load_dotenv()


# Dummy page to get started.
layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            [
                dcc.Markdown(id='intro',
                children = """
                ---
                # Consumer Review Analysis
                ---
                
                Below is a sample exercise to explore the consumer reviews of restaurants for a food vendor. 
                The data is a small sample of reviews from the last Third Quarter of 2023.

                The nature of the project is to explore the data and find trends and topics that are
                insightful and can be used to improve the business.

                > Objectives:
                > - Help proactively identify potential issues with service and/or restaurants
                > - Help coach restaurants more effectively (both positively and negatively)
                > - Help understand consumer sentiment to improve client programs
                """
                ),
            ]
        )
    ]),
    html.Br(),
    html.Br(),
    dbc.Row(
        [
        dbc.Col(width=1),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardImg(src="static/images/pngtree-analysis-icon-for-your-project-png-image_1561759.jpg", top=True, style={'opacity': '0.05'}),
                    dbc.CardImgOverlay(
                    dbc.CardBody(
                        [
                            dcc.Markdown("""
                            ---
                            # Analysis
                            ---

                            A report style analysis with static findings and insights.
                            """,
                                style={
                                    # 'font-family': 'plain',
                                    'color': 'grey',
                                    'font-weight': 'light'
                                }),
                            html.Br(),
                            dbc.Button(
                                'View Page',
                                href='/analysis',
                                style={
                                    'background-color': 'rgba(0, 203, 166, 0.7)',
                                    'border': 'none',
                                    'color': 'white',
                                    'padding': '15px',
                                    'margin-top': '5px',
                                    'margin-bottom': '10px',
                                    'text-align': 'center',
                                    'text-decoration': 'none',
                                    'font-size': '16px',
                                    'border-radius': '26px'
                                }
                            ),
                        ],
                    )
                    )
                ]
            ),
            width=5
        ),
        dbc.Col([
            dbc.Card(
                [
                    dbc.CardImg(src="/static/images/channel.png", top=True, style={'opacity': '0.05'}),
                    dbc.CardImgOverlay(
                        dbc.CardBody(
                            [
                                dcc.Markdown("""
                                    ---
                                    # Dashboard
                                    ---

                                    User interactive dashboard to explore the data.   
                                    """,
                                    style={
                                        # 'font-family': 'plain',
                                        'color': 'grey',
                                        'font-weight': 'light'
                                        # 'font-size': '12px',
                                    }),
                                html.Br(),
                                dbc.Button(
                                    'View Page', 
                                    href='/dashboard',
                                    style={
                                        'background-color': 'rgba(0, 203, 166, 0.7)',
                                        'border': 'none',
                                        'color': 'white',
                                        'padding': '15px',
                                        'margin-top': '5px',
                                        'margin-bottom': '10px',
                                        'text-align': 'center',
                                        'text-decoration': 'none',
                                        'font-size': '16px',
                                        'border-radius': '26px'
                                        }
                                ),
                            ],
                        )
                    )
                ]
            ),
            ], width=5
            ),
        ]
    ),
    dbc.Row([
        dbc.Col(
            [
                dcc.Markdown(id='intro',
                children = """
                ---
                # Issues and Project Questions
                ---

                Lack of data creates a subtle issue in the visualiztions and analysis. A longer time 
                period would be helpful to see trends and patterns.

                In a real world scenario, item_id would be translated for a more readable understanding 
                for the typical user.

                There is no check on overzealous users who may be trying to "complain" their way 
                into a discount offer. Tracking user_id and/or IP address would be helpful to identify any outliers "over-reviewing".
                """
                ),
            ]
        )
    ]),
])
