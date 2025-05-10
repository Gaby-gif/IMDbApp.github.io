import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from itertools import chain  
import math
import os

url = "https://raw.githubusercontent.com/Gaby-gif/IMDbApp.github.io/refs/heads/main/data.csv"
data = pd.read_csv(url)

year_median = pd.to_numeric(data["startYear"], errors="coerce").median()
data["startYear"] = data["startYear"].replace('\\N', str(round(year_median)))

data['startYear'] = data['startYear'].astype(int)    

# Change Music for Musical in 2 steps. I prefer to keep Musical. 
data['genres'] = data['genres'].str.replace('Musical','Music',regex=True)
data['genres'] = data['genres'].str.replace('Music','Musical',regex=True)
genres_list = []
for i in data['genres'].unique():
    genres_list.append(i.split(','))
unique_genres_list = list(chain(*genres_list))
unique_genres = sorted(set(unique_genres_list))



### App Creation 
app = Dash(__name__)

app.layout = html.Div([

                ### Header
                html.Div([
                    html.Div([
                        html.H1("🎬 Movie Analytics Dashboard", style={'margin': '0', 'color': '#fff'}),
                    ], style={'textAlign': 'left'}),
                ], style={'backgroundColor': '#222', 'padding': '20px', 'borderBottom': '4px solid #444', 'marginBottom': '30px','textAlign': 'left'}),
                
                ### Load the data
                dcc.Store(id='filtered-data-store'),

                ### Overview
                html.Div([
                    html.Div([
                        html.H3("Overview"),
                        html.P("In this dashboard, I analyze the Internet Movie Database (IMDb) by year, genre, directors, average ratings and number of votes."),
                        html.P("The purpose of this dashboard is to analyze the evolution of the movies' performance on IMDb through the years. But also to improve my skills in Data Science and Machine Learning by building a full Python Dashboard."),
                        html.P("Warning : The data presented are partial, as the complete volume was too heavy to load on its own.", style={"color": "red"}),
                        html.P("The charts are independent, any action with the charts have no result on the rest. For filtering, please use the filters below.", style={"color": "red"})
                    ])
                ], style={'backgroundColor': '#FFFFFF', 'padding': '20px', 'borderBottom': '4px solid #444', 'marginBottom': '30px','textAlign': 'left'}),

                ### Filters
                html.Div([
                    ### Filter_1
                    html.Div([
                        html.H3("Select your time period (in year)"),
                        dcc.RangeSlider(id='year-slider',
                                       min=data['startYear'].min(),
                                       max=data['startYear'].max(),
                                       value=[data['startYear'].min(), data['startYear'].max()],
                                       marks={year: str(year) for year in range(data['startYear'].min(), data['startYear'].max()+1, round(len(data['startYear'].unique())/5))},
                                       allowCross=False,
                                       tooltip={"placement": "bottom", "always_visible": True},
                                       step=1)
                    ], className="choice-container"),
                    ### Filter_2
                    html.Div([
                        html.H3("Select the genre(s) and analyze the movies which contain this/these genre(s)"),
                        html.H4("(if none selected, you see all)"),
                        dcc.Checklist(id = 'genres-checklist',
                                      options=[{'label': g, 'value': g} for g in unique_genres],
                                      value=[],
                                      labelStyle={'display': 'inline-block', 'margin-right': '10px'})
                    ], className="choice-container"),
                ], className="filter-container"),

                ### KPIs
                html.Div([
                    ### KPI_1
                    html.Div([
                        html.H3("With the current selections, we are analyzing :"),
                        html.P(id='kpi-count', style={"fontSize": 30})
                    ], className="card-container"),
                    ### KPI_2
                    html.Div([
                        html.H3("For which, the average rating is :"),
                        html.P(id='kpi-average', style={"fontSize": 30})
                    ], className="card-container"),
                    html.Div([
                        html.H3("The director with the highest number of votes is :"),
                        html.P(id='kpi-director', style={"fontSize": 30})
                    ], className="card-container"),
                    html.Div([
                        html.H3("The movie with the highest number of votes is :"),
                        html.P(id='kpi-movie', style={"fontSize": 30})
                    ], className="card-container"),
                ], className="kpi-container"),


                ### Graphs + Table section (buttons + charts + table)
                html.Div([
                    # Left column with buttons + main + count graphs
                    html.Div([
                        # Buttons above the charts
                        html.Div([
                            html.Button("Display average ratings", id="button-1", n_clicks=0, className='imdb-button'),
                            html.Button("Display the sum of votes", id="button-2", n_clicks=0, className='imdb-button')
                        ], className = 'button-container'),
                
                        # Stacked charts
                        dcc.Graph(id='main-graph', style={'marginBottom': '30px'}),
                        dcc.Graph(id='count-movie-graph')
                    ], style={'flex': '2', 'minWidth': '400px'}),
                
                    # Right column with the table
                    html.Div([
                        html.H4(html.Br()),
                        dcc.Graph(id='table-vote-top'),
                        dcc.Graph(id='table-rate-top')
                    ], style={'flex': '1', 'minWidth': '300px'}),
                ], style={'display': 'flex', 'gap': '30px', 'marginTop': '30px'}),
            ])

### We filter the data first here based on the filters
### Filtered_Data
@app.callback(
    Output('filtered-data-store', 'data'),
    [Input('year-slider', 'value'),
     Input('genres-checklist', 'value')]
)
def filter_data(year_range, selected_genres):
    filtered = data[
        (data['startYear'] >= year_range[0]) &
        (data['startYear'] <= year_range[1])
    ]
    if selected_genres:
        filtered = filtered[filtered['genres'].apply(lambda genres: all(g in genres for g in selected_genres))]
    return filtered.to_dict('records')

### Dashboard's Creation
### Chart_1 & Chart_2
@app.callback(
    Output('main-graph', 'figure'),
    [Input('button-1', 'n_clicks'),
     Input('button-2', 'n_clicks'),
     Input('filtered-data-store', 'data'),
     Input('genres-checklist', 'value')]
)
def update_graph(n1, n2, stored_data, selected_genres):
    data = pd.DataFrame(stored_data)
    ctx = dash.callback_context

     # 🔒 Si aucun genre sélectionné → afficher un message
    if not selected_genres:   
        if not ctx.triggered:
            button_id = 'button-1'
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
        if button_id == 'button-1':
            fig = px.line(
                round(data.groupby(['startYear'])['averageRating'].mean().reset_index(),1),
                x="startYear",
                y="averageRating",
                markers=True,
                labels={'startYear':'Release Year', 'averageRating': 'Average Rating'},
                title="Evolution of average movie's scores by year"
            )
            fig.update_layout(
                yaxis=dict(
                tickformat=",",  # Format nombre avec séparateur
                ticklabelposition="outside",  # Optionnel
                )
            )
        else:
            fig = px.line(
                data.groupby(['startYear'])['numVotes'].sum().reset_index(),
                x="startYear",
                y="numVotes",
                markers=True,
                labels={'startYear':'Release Year', 'numVotes': '# Votes'},
                title="Evolution of the sum of votes for movie per year"
            )
            fig.update_layout(
                yaxis=dict(
                tickformat=",",  # Format nombre avec séparateur
                ticklabelposition="outside",  # Optionnel
                )
            )

        return fig

    if not ctx.triggered:
        button_id = 'button-1'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'button-1':
        fig = px.line(
            round(data.groupby(['startYear','genres'])['averageRating'].mean().reset_index(),1),
            x="startYear",
            y="averageRating",
            color='genres',
            markers=True,
            labels={'genres':'Type of Movie', 'startYear':'Release Year', 'averageRating': 'Average Rating'},
            title="Evolution of average movie's and short's scores by year"
        )
        fig.update_layout(
            yaxis=dict(
            tickformat=",",  # Format nombre avec séparateur
            ticklabelposition="outside",  # Optionnel
            )
        )
    else:
        fig = px.line(
            data.groupby(['startYear','genres'])['numVotes'].sum().reset_index(),
            x="startYear",
            y="numVotes",
            color='genres',
            markers=True,
            labels={'genres':'Type of Movie', 'startYear':'Release Year', 'numVotes': '# Votes'},
            title="Evolution of the sum of votes for movie and short per year"
        )
        fig.update_layout(
            yaxis=dict(
            tickformat=",",  # Format nombre avec séparateur
            ticklabelposition="outside",  # Optionnel
            )
        )

    return fig

### Chart_3
@app.callback(
    Output('count-movie-graph', 'figure'),
    Input('filtered-data-store', 'data')
)
def movie_count_graph(stored_data):
    data = pd.DataFrame(stored_data)
    fig = px.bar(
        data.groupby(['startYear'])['primaryTitle'].count().reset_index(),
        x='startYear', 
        y='primaryTitle',
        labels={'primaryTitle':'# Movie', 'startYear':'Release Year'},
        title="Evolution of the number of movies released per year"
    )
    fig.update_layout(
        yaxis=dict(
            tickformat=",",  # Format nombre avec séparateur
            ticklabelposition="outside",  # Optionnel
        )
    )
    return fig

### KPIs
### kpi
@app.callback(
    [Output('kpi-count', 'children'),
    Output('kpi-average','children'),
    Output('kpi-director','children'),
    Output('kpi-movie','children')],
    [Input('filtered-data-store', 'data')]
)
def update_kpis(filtered_data):
    if not filtered_data or len(filtered_data) == 0:
        return "0", "N/A", "N/A", "N/A"
    data = pd.DataFrame(filtered_data)
    ###KPI_1
    count = f"{len(data):,} movies"
    ###KPI_2
    average = f"{data['averageRating'].mean():.0f}"
    ###KPI_3
    df1 = data.groupby(['directors'])['numVotes'].sum().reset_index()
    top_director_df = df1.sort_values("numVotes", ascending=False).reset_index()
    top_director = top_director_df["directors"][0]
    ###KPI_4
    df1 = data.groupby(['primaryTitle'])['numVotes'].sum().reset_index()
    top_movie_df = df1.sort_values("numVotes", ascending=False).reset_index()
    top_movie = top_movie_df["primaryTitle"][0]
    return count, average, top_director, top_movie

### Table
@app.callback(
    [Output('table-vote-top', 'figure'),
     Output('table-rate-top', 'figure')],
    Input('filtered-data-store', 'data')
)
def table(filtered_data):
    data = pd.DataFrame(filtered_data)
    df1 = data.groupby(['primaryTitle','directors','averageRating'])['numVotes'].sum().reset_index()
    top_10_movie = (df1.sort_values("numVotes", ascending=False).reset_index().head(10)
                    .rename(columns={"index": "Rank", "primaryTitle":"Movie", "directors":"Directors", "numVotes":"# Votes", "averageRating":"Average Rating"})
                    .iloc[:, [0, 1, 2, 4, 3]]
                   )
    top_10_movie['Rank'] = top_10_movie['# Votes'].rank(ascending=False).map(int)
    top_10_movie['# Votes'] = top_10_movie['# Votes'].apply(lambda x: f"{x:,}")
    fig_vote = go.Figure(data=[
        go.Table(
            header=dict(
                values=list(top_10_movie.columns),
                fill_color="#f5c518", 
                font=dict(color='black', size=14),
                line_color='darkgray'
            ),
            cells=dict(
                values=[top_10_movie[col] for col in top_10_movie.columns],
                fill_color='white',
                align=['left', 'right', 'right'],
                font=dict(color='black', size=13),
                line_color='lightgray',
                height=30
            )
        )]
    )
    fig_vote.update_layout(title_text = "Top 10 movies and their directors per number of votes")

    df2 = data.groupby(['primaryTitle','directors','numVotes'])['averageRating'].mean().reset_index()
    top_10_rate = (df2.sort_values("averageRating", ascending=False).reset_index().head(10)
                   .rename(columns={"index": "Rank", "primaryTitle":"Movie", "directors":"Directors", "averageRating":"Average Rating", "numVotes":"# Votes"}))
    top_10_rate['Rank'] = top_10_rate['Average Rating'].rank(ascending=False).map(int)
    fig_rate = go.Figure(data=[
        go.Table(
            header=dict(
                values=list(top_10_rate.columns),
                fill_color="#f5c518", 
                font=dict(color='black', size=14),
                line_color='darkgray'
            ),
            cells=dict(
                values=[top_10_rate[col] for col in top_10_rate.columns],
                fill_color='white',
                align=['left', 'right', 'right'],
                font=dict(color='black', size=13),
                line_color='lightgray',
                height=30
            )
        )]
    )
    fig_rate.update_layout(title_text = "Top 10 movies and their directors per average rating")
    return fig_vote, fig_rate

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
