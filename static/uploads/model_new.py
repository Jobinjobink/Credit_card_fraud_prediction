import pandas as pd
import joblib

model = joblib.load("../../rr_model.pkl")  # adjust if different

df = pd.read_csv("1762797782_fraud_only.csv")  # your extracted file

y_pred = model.predict_proba(df.drop(columns=["Class"]))

print(sum(y_pred))  # total fraud predicted
print(y_pred[:20])
