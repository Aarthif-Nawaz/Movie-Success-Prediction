from __future__ import print_function
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn import preprocessing, tree
from collections import defaultdict
import math
import sys
import json

df = pd.read_csv('./data/Stage2Lower.csv', index_col=0)
tf = pd.read_csv('./data/WithoutGrossLower.csv', index_col=0)

#take inputs

input_string = input("Enter a list numbers or elements separated by ,: ")

listToStr = ' '.join([str(elem) for elem in input_string])
listToStr = listToStr.replace(" ","")
listToStr = listToStr.replace('"','')

print(listToStr) 
userList = listToStr.split(',')
print("user list is ", userList)
actor1 = userList[0].lower()
actor2 = userList[1].lower()
actor3 = userList[2].lower()
director = userList[3].lower()
time = int(userList[4])
budget = int(userList[5])
budget = budget*1000000
faceno = int(userList[6])
duration = int(userList[7])
color = userList[8].lower()
c_rating = userList[9].lower()
genres = userList[10].lower()
language = userList[11].lower()
score = float(userList[12])
aspect_ratio = float(userList[13])



# director gross and imdb score
director_entries = df['director_name'] == director
movies_before_time = df['title_year'] < time

director_avg_gross = df[director_entries & movies_before_time]['gross'].aggregate(np.mean)

director_avg_score = df[director_entries & movies_before_time]['imdb_score'].aggregate(np.mean)

director_movies = df[director_entries & movies_before_time].shape[0]

# if any column is null or person not found make it zero so it wont affect the calculation
if math.isnan(director_avg_gross):
    director_avg_gross = 0
if math.isnan(director_avg_score):
    director_avg_score = 0
if math.isnan(director_movies):
    director_movies = 0


# average score/ gross and movies done by actors according to their history in datasets
def actor_data(actor, time):

    #getting movies before the release year and getting the actor from the 3 actor columns
    actor_movies = df['title_year'] < time
    actor_in_1 = df['actor_1_name'] == actor
    actor_in_2 = df['actor_2_name'] == actor
    actor_in_3 = df['actor_3_name'] == actor

    # score gross and movies if he was in 1st column
    actor_score_1 = df[actor_in_1 & actor_movies]['imdb_score'].aggregate(np.mean)
    actor_gross_1 = df[actor_in_1 & actor_movies]['gross'].aggregate(np.mean)
    actor_movie_1 = df[actor_in_1 & actor_movies].shape[0]
    # score gross and movies if he was in 2st column
    actor_score_2 = df[actor_in_2 & actor_movies]['imdb_score'].aggregate(np.mean)
    actor_gross_2 = df[actor_in_2 & actor_movies]['gross'].aggregate(np.mean)
    actor_movie_2 = df[actor_in_2 & actor_movies].shape[0]
    # score gross and movies if he was in 3rd column
    actor_score_3 = df[actor_in_3 & actor_movies]['imdb_score'].aggregate(np.mean)
    actor_gross_3 = df[actor_in_3 & actor_movies]['gross'].aggregate(np.mean)
    actor_movie_3 = df[actor_in_3 & actor_movies].shape[0]

    # setting values zero if not found so it wont afect calculations
    if math.isnan(actor_score_1):
        actor_score_1 = 0
    if math.isnan(actor_score_2):
        actor_score_2 = 0
    if math.isnan(actor_score_3):
        actor_score_3 = 0
    if math.isnan(actor_gross_1):
        actor_gross_1 = 0
    if math.isnan(actor_gross_2):
        actor_gross_2 = 0
    if math.isnan(actor_gross_3):
        actor_gross_3 = 0
    if math.isnan(actor_movie_1):
        actor_movie_1 = 0
    if math.isnan(actor_movie_2):
        actor_movie_2 = 0
    if math.isnan(actor_movie_3):
        actor_movie_3 = 0

    #getting averages
    actor_avg_score = (actor_score_1 + actor_score_2 + actor_score_3) / 3

    actor_avg_gross = (actor_gross_1 + actor_gross_2 + actor_gross_3) / 3

    actor_movie = actor_movie_1 + actor_movie_2 + actor_movie_3
    # setting zero to avoid error in calcuation and make it unaffecting
    if math.isnan(actor_avg_score):
        actor_avg_score = 0
    if math.isnan(actor_avg_gross):
        actor_avg_gross = 0
    if math.isnan(actor_movie):
        actor_movie = 0

    return actor_avg_score, actor_avg_gross, actor_movie


actor_1_avg_score, actor_1_avg_gross, actor_1_movies = actor_data(actor1, time)
actor_2_avg_score, actor_2_avg_gross, actor_2_movies = actor_data(actor2, time)
actor_3_avg_score, actor_3_avg_gross, actor_3_movies = actor_data(actor3, time)

average_score_actors = (actor_1_avg_score + actor_2_avg_score + actor_3_avg_score) / 3
average_gross_actors = (actor_1_avg_gross + actor_2_avg_gross + actor_3_avg_gross) / 3
total_movies = actor_1_movies+actor_2_movies+actor_3_movies

#appending the new data to train and predict
cf = tf.copy()

cf = cf.append(
{'color': color, 'duration': duration, 'genres': genres, 'facenumber_in_poster': faceno, 'language': language,
     'content_rating': c_rating, 'budget': budget, 'title_year': time, 'imdb_score': score,
     'aspect_ratio': aspect_ratio, 'director_avg_gross': director_avg_gross, 'director_movies': director_movies,
     'director_avg_score': director_avg_score, 'actor_average_score': average_score_actors,
     'actor_average_gross': average_gross_actors, 'actor_movies': total_movies}, ignore_index=True)

genre = cf['genres']
genre_num = pd.DataFrame()
del cf['genres']
#splitting the genres and count of it
count = 0
for i in genre:
    s = i.split('|')
    for j in s:
        genre_num.at[count,j] = 1
        count = count + 1

genre_num = genre_num.fillna('0')

le = defaultdict(preprocessing.LabelEncoder)

encode_list = cf.select_dtypes(include=['object']).copy()

encode_data = pd.DataFrame()
encode_data = pd.get_dummies(encode_list)

#remove unaffecting columns
del cf['color']
del cf['language']
del cf['content_rating']
cf = cf.join(encode_data)
cf = cf.reset_index(drop=True)
cf = cf.join(genre_num)
print("Encoding Complete")
print("Applying Algorithm and predicting")

#applying random forest regression
pres = pd.DataFrame()
pres = pres.append(cf[len(cf)-1:], ignore_index=True)
cf = cf.drop(cf.index[len(cf) - 1])
y = cf.gross_class
x = cf.drop('gross_class', axis=1)
x.isna().sum()

pres = pres.drop('gross_class', axis = 1)
algo = RandomForestRegressor(n_estimators=1000,max_depth=10)
algo = algo.fit(x, y)
y_1 = algo.predict(pres)


# the classes of gross calculations
GROSS_CLASS = y_1[0]
gross = ""
if GROSS_CLASS <= 1:
    gross = "Upto 1 Million Dollars"
if GROSS_CLASS > 1 and GROSS_CLASS <= 2:
    gross = "1 to 10 Million Dollars"
if GROSS_CLASS > 2 and GROSS_CLASS <= 3:
    gross = "10 to 20 Million Dollars"
if GROSS_CLASS > 3 and GROSS_CLASS <= 4:
    gross = "20 to 40 Million Dollars"
if GROSS_CLASS > 4 and GROSS_CLASS <= 5:
    gross = "40 to 65 Million Dollars"
if GROSS_CLASS > 5 and GROSS_CLASS <= 6:
    gross = "65 to 100  Million Dollars"
if GROSS_CLASS > 6 and GROSS_CLASS <= 7:
    gross = "100 to 150 Million Dollars"
if GROSS_CLASS > 7 and GROSS_CLASS <= 8:
    gross = "150 to 200 Million Dollars"
if GROSS_CLASS > 8 and GROSS_CLASS <= 9:
    gross = "200+ Million Dollars"
print("The predicted approximate gross revenue of the movie is:")
print(gross)
