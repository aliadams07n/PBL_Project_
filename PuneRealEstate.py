# Importing essential libraries
import numpy as np
import pandas as pd


df = pd.read_csv('Pune_House_Data.csv')
df = df.drop('society', axis='columns')
from math import floor

balcony_median = float(floor(df.balcony.median()))
bath_median = float(floor(df.bath.median()))
df.balcony = df.balcony.fillna(balcony_median)
df.bath = df.bath.fillna(bath_median)
df = df.dropna()
df['bhk'] = df['size'].apply(lambda x: int(x.split(' ')[0]))
df = df.drop('size', axis='columns')


def isFloat(x):
    try:
        float(x)
    except:
        return False
    return True


def convert_sqft_to_num(x):
    tokens = x.split('-')
    if len(tokens) == 2:
        return (float(tokens[0]) + float(tokens[1])) / 2
    try:
        return float(x)
    except:
        return None


df['new_total_sqft'] = df.total_sqft.apply(convert_sqft_to_num)
df = df.drop('total_sqft', axis='columns')
df = df.dropna()
df1 = df.copy()
df1['price_per_sqft'] = (df1['price'] * 100000) / df1['new_total_sqft']
location_stats = df1.groupby('site_location')['site_location'].agg('count').sort_values(ascending=False)
locations_less_than_10 = location_stats[location_stats <= 10]
df1.site_location = df1.site_location.apply(lambda x: 'other' if x in locations_less_than_10 else x)
len(df1.site_location.unique())
dates = df1.groupby('availability')['availability'].agg('count').sort_values(ascending=False)
dates_not_ready = dates[dates < 10000]
df1.availability = df1.availability.apply(lambda x: 'Not Ready' if x in dates_not_ready else x)
df2 = df1[~(df1.new_total_sqft / df1.bhk < 300)]


def remove_pps_outliers(df):
    df_out = pd.DataFrame()

    for key, sub_df in df.groupby('site_location'):
        m = np.mean(sub_df.price_per_sqft)
        sd = np.std(sub_df.price_per_sqft)
        reduce_df = sub_df[(sub_df.price_per_sqft > (m - sd)) & (sub_df.price_per_sqft < (m + sd))]
        df_out = pd.concat([df_out, reduce_df], ignore_index=True)

    return df_out


df3 = remove_pps_outliers(df2)


def remove_bhk_outliers(df):
    exclude_indices = np.array([])

    for site_location, site_location_df in df.groupby('site_location'):
        bhk_stats = {}

        for bhk, bhk_df in site_location_df.groupby('bhk'):
            bhk_stats[bhk] = {
                'mean': np.mean(bhk_df.price_per_sqft),
                'std': np.std(bhk_df.price_per_sqft),
                'count': bhk_df.shape[0]
            }

        for bhk, bhk_df in site_location_df.groupby('bhk'):
            stats = bhk_stats.get(bhk - 1)
            if stats and stats['count'] > 5:
                exclude_indices = np.append(exclude_indices,
                                            bhk_df[bhk_df.price_per_sqft < (stats['mean'])].index.values)

    return df.drop(exclude_indices, axis='index')


df4 = remove_bhk_outliers(df3)

# Removing the rows that have 'bath' greater than 'bhk'+2
df5 = df4[df4.bath < (df4.bhk + 2)]

# Removing the unnecessary columns (columns that were added only for removing the outliers)
df6 = df5.copy()
df6 = df6.drop('price_per_sqft', axis='columns')

"""### **Model Bulding**"""

# Converting the categorical_value into numerical_values using get_dummies method
dummy_cols = pd.get_dummies(df6.site_location)
df6 = pd.concat([df6, dummy_cols], axis='columns')

# Converting the categorical_value into numerical_values using get_dummies method
dummy_cols = pd.get_dummies(df6.availability).drop('Not Ready', axis='columns')
df6 = pd.concat([df6, dummy_cols], axis='columns')

# Converting the categorical_value into numerical_values using get_dummies method
dummy_cols = pd.get_dummies(df6.area_type).drop('Super built-up  Area', axis='columns')
df6 = pd.concat([df6, dummy_cols], axis='columns')

df6.drop(['area_type', 'availability', 'site_location'], axis='columns', inplace=True)
df6.head(10)

# Size of the dataset
df6.shape

# Splitting the dataset into features and label
X = df6.drop('price', axis='columns')
y = df6['price']

"""### *Linear Regression Algorithm*"""

# Splitting the dataset into train and test set
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=20)

# Creating Linear Regression Model
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_train, y_train)

model.score(X_test, y_test)


# Creating a fuction to predict values
def prediction(location, bhk, bath, balcony, sqft, area_type, availability):
    loc_index, area_index, avail_index = -1, -1, -1

    if location != 'other':
        loc_index = int(np.where(X.columns == location)[0][0])

    if area_type != 'Super built-up  Area':
        area_index = np.where(X.columns == area_type)[0][0]

    if availability != 'Not Ready':
        avail_index = np.where(X.columns == availability)[0][0]

    x = np.zeros(len(X.columns))
    x[0] = bath
    x[1] = balcony
    x[2] = bhk
    x[3] = sqft

    if loc_index >= 0:
        x[loc_index] = 1
    if area_index >= 0:
        x[area_index] = 1
    if avail_index >= 0:
        x[avail_index] = 1

    return model.predict([x])[0]

#prediction('Camp', 2, 2, 2, 1000, 'Built-up  Area', 'Ready To Move')
#print(X.columns[:])

import pickle
'''
with open(r'rf.pkl', 'wb') as model_pkl:
    pickle.dump(model, model_pkl)
'''