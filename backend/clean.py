import pandas as pd

input_file = r"C:\Vault\Projects\food_delivery_analysis\train.csv"

df = pd.read_csv(input_file)

# Remove the Time_taken(min) column
df = df.drop(columns=["Time_taken(min)"])

# Save back to the same CSV
df.to_csv(input_file, index=False)

print("Done!")
print("Removed: Time_taken(min)")
print("Remaining columns:", len(df.columns))
print(df.head())