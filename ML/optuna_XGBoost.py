import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.metrics import f1_score, precision_score
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import recall_score
from sklearn.metrics import accuracy_score
import warnings
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import shared
shared.init()
warnings.filterwarnings("ignore")

data_path = shared.DATA_PATH


def objective(trial, df, y):
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'subsample': trial.suggest_uniform('subsample', 0.5, 1),
        'learning_rate': trial.suggest_uniform('learning_rate', 1e-5, 1),
        'gamma': trial.suggest_loguniform('gamma', 1e-8, 1e2),
        'lambda': trial.suggest_loguniform('lambda', 1e-8, 1e2),
        'alpha': trial.suggest_loguniform('alpha', 1e-8, 1e2)
    }
    kf = StratifiedKFold(n_splits=5, random_state=15, shuffle=True)

    y_hats = []
    y_tests = []

    for train_index, test_index in kf.split(df, y):
        X_train, X_test = df.iloc[train_index], df.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        y_hats += model.predict(X_test).tolist()
        y_tests += y_test.tolist()

    return f1_score(y_tests, y_hats)


X = pd.read_csv(shared.DATA_PATH+"/X.csv")
X = X.set_index("token_address")
labels = pd.read_csv(data_path+"/labeled_list.csv", index_col="token_address")
X = X.merge(labels['label'], left_index=True, right_index=True)
X = X.reset_index()
df = X.drop_duplicates(subset=['token_address'])
X = X.set_index("token_address")
lock_features = pd.read_csv(data_path+"/token_lock_features.csv", index_col="token_address") #! Where do they get this from?
# X = X.merge(lock_features, how='left', left_index=True, right_index=True)
optuna.logging.set_verbosity(optuna.logging.WARNING)

ids = []
total_probs = []
confidences = []
quarter = []
total_targets = []

skfolds = StratifiedKFold(n_splits=5, shuffle=True, random_state=2)
for fold, (t, v) in enumerate(skfolds.split(df['token_address'], df['label'])):

    ids_train = df['token_address'].iloc[t]
    df_train = X.loc[ids_train]
    ids_test = df['token_address'].iloc[v]
    df_test = X.loc[ids_test]

    X_train, y_train = df_train.drop(["label", "eval_block"], axis=1), df_train['label']
    X_test, y_test = df_test.drop(["label", "eval_block"], axis=1), df_test['label']

    columns = X_train.columns

    func = lambda trial: objective(trial, X_train.copy(), y_train.copy())
    study = optuna.create_study(direction='maximize')
    study.optimize(func, n_trials=100)

    model = xgb.XGBClassifier(**study.best_params)
    model.fit(X_train, y_train)
    preds_scorings = model.predict_proba(X_test)

    preds = model.predict(X_test)

    c =np.zeros_like(preds, dtype=preds_scorings.dtype)
    c[preds == 0] = preds_scorings[preds == 0, 0]  # Assign values from the first column of 'a' where 'b' is 0
    c[preds == 1] = preds_scorings[preds == 1, 1]  # Assign values from the second column of 'a' where 'b' is 1

    # if pred==1 then we grab the probability of being 1 else we grab the probability of being 0
    preds_scorings_max = preds_scorings.max(axis=1)
    # Calculate quartiles
    q1_0 = np.percentile(c[preds == 0], 25)
    q2_0 = np.percentile(c[preds == 0], 50)
    q3_0 = np.percentile(c[preds == 0], 75)

    q1_1 = np.percentile(c[preds == 1], 25)
    q2_1 = np.percentile(c[preds == 1], 50)
    q3_1 = np.percentile(c[preds == 1], 75)

    # Determine quartile of each value
    quartile_of_data = np.zeros_like(c, dtype=int)
    t = quartile_of_data[preds == 0]
    t[c[preds == 0] <= q1_0] = -1
    t[(c[preds == 0] > q1_0) & (c[preds == 0] <= q2_0)] = -2
    t[(c[preds == 0] > q2_0) & (c[preds == 0] <= q3_0)] = -3
    t[c[preds == 0] > q3_0] = -4
    quartile_of_data[preds == 0] = t
    t = quartile_of_data[preds == 1]
    t[c[preds == 1] <= q1_1] = 1
    t[(c[preds == 1] > q1_1) & (c[preds == 1] <= q2_1)] = 2
    t[(c[preds == 1] > q2_1) & (c[preds == 1] <= q3_1)] = 3
    t[c[preds == 1] > q3_1] = 4
    quartile_of_data[preds == 1] = t

    f1 = f1_score(y_test, preds)
    sensibilitat = recall_score(y_test, preds)
    precisio = precision_score(y_test, preds)
    accuracy = accuracy_score(y_test, preds)
    print("{},{},{},{},{}".format(accuracy, sensibilitat, precisio, f1, fold))
    if fold == 4:
        model.save_model("./models/model_{}.json".format(precisio))
    ids += X_test.index.tolist()#.append("-----Fold {}-----".format(fold))
    ids += ["-----fold {}-----".format(fold)]
    total_probs += preds.tolist()#.append("-----Fold {}-----".format(fold))
    total_probs += ["-----Fold {}-----".format(fold)]
    confidences += preds_scorings_max.tolist()#.append("-----Fold {}-----".format(fold))
    confidences += ["-----Fold {}-----".format(fold)]
    quarter += quartile_of_data.tolist()#.append("-----Fold {}-----".format(fold))
    quarter += ["-----Fold {}-----".format(fold)]
    total_targets += y_test.tolist()#.append("-----Fold {}-----".format(fold))
    total_targets += ["-----Fold {}-----".format(fold)]

final_df = pd.DataFrame({'ids': ids, 'Pred': total_probs, 'Label': total_targets, 'Confidence': confidences, 'Quartile:': quarter})\
    .to_csv("Results_XGBoost.csv", index=False)
