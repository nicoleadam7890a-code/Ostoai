# from pandas.core.arrays import categorical
# from sklearn.preprocessing import StandardScaler
# import pandas as pd 
# import numpy as np 
# from xgboost import XGBClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import accuracy_score
# import joblib
# import os
# from preprocessing import load_data , encode_data , scale_features

# #-1.Load Data 
# df=pd.read_csv("data/data.csv")
# print("✅ Data loaded successfully. Shape:", df.shape)

# # --2. Pre Processing---
# if 'Id' in df.columns:
#     df=df.drop(columns=['Id'])

# df=df.fillna('Unknown')

# # --3. Encode categorical Features----------
# categorical_features = df.select_dtypes(include=['object'].columns.tolist())
# if 'Osteoporosis' in categorical_features:
#     categorical_features.remove('Osteoporosis')

# print(f"📋 Encoding {len(categorical_features)} categorical features: {categorical_features}")
# df_encoded=pd.get_dummies(df,columns=categorical_features)

# # --4. Feature / Target split----------
# X=df_encoded.drop(columns=['Osteoporosis'])
# y=df_encoded['Osteoporosis']
# feature_name=X.column.tolist()
# print(f"📊 Total features after encoding: {len(feature_name)}")

# # --5. Train / Test Split----------
# X_train , X_test , y_train , y_test =train_test_split(
#     X,y,test_size=0.2,random_state=42
# )
# print(f"Train :{X_train[0]} samples| Test: {X_test.shape[0]} samples")

# # --6. Feature Scaling ----------
# scaler = StandardScaler() 
# X_train_scaled = scaler.fittranform(X_train)
# X_test_scaled = scaler.transform(X_test)

# # --7. Train XGBoost ----------
# xg_model = XGBClassifier(
#     n_estimators=500,
#     learning_rate=0.05,
#     max_depth=7,
#     subsample=0.8,
#     colsample_bytree=0.8,
#     objective='binary:logistic',
#     eval_metirc='logloss'
# )

# xg_model.fit(X_train_scaled,y_train)
# xg_pred = xg_model.predict(X_test_scaled)
# xg_proba = xg_model.predict_proba(X_test_scaled)
# print(f" XGBoost Accuracy:{accuracy_score(y_test , xg_pred):.4f}")

# # Save
# joblib.dump(xg_model, "models/XGBoost_model.pkl")
# feature_name = X.columns
# joblib.dump(feature_name , "models/features_name.pkl")
