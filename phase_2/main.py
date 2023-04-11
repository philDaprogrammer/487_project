import pandas as pd
import numpy as np
import warnings
import matplotlib.pyplot as plt

from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn import svm

"""
Just dump a data frame to stdout 
"""
def _dump_frame(df):
    for row in df.iterrows():
        print(row)


def get_train_and_test_years(results_df):
    years_train = [year for year in results_df['year'].unique() if year < 2018]
    years_test  = [2018]

    return years_train, years_test


"""
Get training and testing data for the naive bayes 
model 
"""
def get_train_and_test_bayes(results_df, years):
    X     = []
    y     = []
    teams = results_df['team'].unique()

    for year in years:
        for team in teams:
            players   = results_df[(results_df['team'] == team) & (results_df['year'] == year)]
            offensive = players[players['position'].isin(["S", "OL", "DT", "DE", "DL", "DB", "CB"])]

            # - sum up total salary for the year
            X.append(offensive['salary'].sum())
            y.append(players['team_record'].unique()[0].split("-")[0])

    return np.array(X).reshape(-1, 1), np.array(y)


"""
Get the training and testing data for the 
Multi-layer perceptron
"""
def get_train_and_test_mlp(results_df, years):
    X      = []
    y      = []
    teams  = results_df['team'].unique()

    for year in years:
        for team in teams:
            players   = results_df[(results_df['team'] == team) & (results_df['year'] == year)]

            offensive = players[players['position'].isin(["WR", "OT", "OG", "C", "TE", "QB", "FB", "RB"])]
            defensive = players[players['position'].isin(["S", "OL", "DT", "DE", "DL", "DB", "CB"])]
            off_tot   = offensive['salary'].sum()
            def_tot   = defensive['salary'].sum()

            y.append(players['team_record'].unique()[0].split("-")[0])
            X.append([off_tot, def_tot])

    return np.array(X), np.array(y)


def get_train_and_test_svm(results_df, years):
    teams = results_df['team'].unique()
    X = []
    y = []

    for team in teams:
        for year in years:
            players = results_df[(results_df['team'] == team) & (results_df['year'] == year)]
            rb_sal  = players[players['position'] == "QB"]['salary'].sum()
            qb_sal  = players[players['position'] == "RB"]['salary'].sum()

            more_than_10 = 1 if int(players['team_record'].unique()[0].split("-")[0]) >= 10 else 0

            X.append([rb_sal, qb_sal])
            y.append(more_than_10)

    return np.array(X), np.array(y)


"""
Run a naive bayes classifier on the  
data set to determine predict the 
number of wins in a season given the amount 
of salary cap spent on defensive positions. 

We expect an increase in games won as 
the defensive spending on players increases  
"""
def naive_bayes(results_df):
    years_train, years_test = get_train_and_test_years(results_df)

    # - get training and testing data
    X_train, Y_train = get_train_and_test_bayes(results_df, years_train)
    X_test, Y_test   = get_train_and_test_bayes(results_df, years_test)

    # - train the naive bayes model
    gnb        = GaussianNB()
    model      = gnb.fit(X_train, Y_train)
    pred_2018  = model.predict(X_test)

    # - create the accuracy distribution
    dist = get_accuracy(pred_2018, Y_test)
    defensive_spending = [val for val in range(1_000_000, 15_000_000, 100_000)]

    trend_data = np.array(defensive_spending).reshape(-1, 1)
    trend      = model.predict(trend_data)

    # - plot the model accuracy distribution
    plt.plot([i for i in range(0, 15)], dist)
    plt.title(f"Absolute difference in predicted vs actual wins during the 2018 regular season")
    plt.xlabel("Absolute difference in wins")
    plt.ylabel("Frequency")
    plt.show()

    # - plot the predicted number of wins given defensive spending
    plt.scatter(trend, defensive_spending)
    plt.title("Relationship of defensive spending and wins per season")
    plt.ylabel("Amount spent on defense (USD)")
    plt.xlabel("Predicted number of wins")
    plt.show()


def support_vector_machine(results_df):
    train_years, test_years = get_train_and_test_years(results_df)
    X_train, y_train        = get_train_and_test_svm(results_df, train_years)
    X_test, y_test          = get_train_and_test_svm(results_df, test_years)

    clf   = svm.SVC(kernel="rbf")
    model = clf.fit(X_train, y_train)
    pred  = model.predict(X_test)

    accuracy = (pred == y_test).sum() / len(pred)
    print(accuracy)

    qb_true  = []
    rb_true  = []
    qb_false = []
    rb_false = []

    for x, label in zip(X_test, pred):
        if label == 1:
            qb_true.append(x[0])
            rb_true.append(x[1])
        else:
            qb_false.append(x[0])
            rb_false.append(x[1])

    plt.scatter(qb_true, rb_true, marker="o")
    plt.scatter(qb_false, rb_false, marker="^")
    plt.xlabel("QB salary")
    plt.ylabel("RB salary")
    plt.show()


def get_accuracy(predictions, actuals):
    dist = [0] * 15

    for pred, acc in zip(predictions, actuals):
        diff = abs(int(acc) - int(pred))
        dist[diff] += 1

    return dist


""" 
try and get some optimal hyper parameters for the model 
"""
def get_mean_errors(X_train, Y_train, X_test, Y_test):
    warnings.filterwarnings("ignore")
    solvers    = ["sgd", "lbfgs", "adam"]
    activators = ["logistic", "tanh", "identity", "relu"]

    for solver in solvers:
        for activator in activators:
            mlp  = MLPClassifier(solver=solver, activation=activator, random_state=1, max_iter=10_000)
            pred = mlp.fit(X_train, Y_train).predict(X_test)

            # - get accuracy distribution
            dist  = get_accuracy(pred, Y_test)
            total = 0

            for i, ent in enumerate(dist):
                total += i * ent

            print(f"MlpClassifier(solver={solver}, activation={activator}) mean error {total / 14}")

    print()


def multi_layer_perceptron(results_df, mean_errors=False):
    years_train, years_test = get_train_and_test_years(results_df)

    X_train, Y_train = get_train_and_test_mlp(results_df, years_train)
    X_test, Y_test   = get_train_and_test_mlp(results_df, years_test)

    # - Try and find some optimality for our MLP hyper-parameters
    # - Set mean_errors to true if you want to see the mean errors
    # - for different hyper-parameters
    if mean_errors:
        get_mean_errors(X_train, Y_train, X_test, Y_test)

    mlp = MLPClassifier(solver="sgd", activation="logistic", random_state=1, max_iter=500)
    classifier = mlp.fit(X_train, Y_train)

    pred_2018  = classifier.predict(X_test)
    dist       = get_accuracy(pred_2018, Y_test)

    plt.plot([i for i in range(0, 15)], dist)
    plt.title(f"Absolute difference in predicted vs actual wins during the 2018 regular season (MLP)")
    plt.xlabel("Absolute difference in wins")
    plt.ylabel("Frequency")
    plt.show()

    cap = 30_000_000
    defensive_cap  = []
    offensive_cap  = []
    predictions    = []

    for i in range(1_000_000, 30_000_000, 1_000_000):
        cap_dist   = np.array([cap - i, i]).reshape(1, -1)
        prediction = classifier.predict(cap_dist)

        offensive_cap.append(cap - i)
        defensive_cap.append(i)
        predictions.append(int(prediction[0]))

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(offensive_cap, defensive_cap, predictions)

    ax.set_xlabel('Offensive cap')
    ax.set_ylabel('Defensive cap')
    ax.set_zlabel('Games won')

    plt.show()


def main():
    results_df = pd.read_csv("../data_sets/results.csv")

    # - run ML algos on the dataset
    naive_bayes(results_df)
    multi_layer_perceptron(results_df)
    support_vector_machine(results_df)
    return


if __name__ == "__main__":
    main()
