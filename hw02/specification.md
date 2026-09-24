# HW2 Specification: EDA Script for fact_transactions.csv

## Goal
Write one Python script, `hw02/hw02_eda.py`, that profiles Wildcat Capital's transaction data in a single run. Everything below should happen in that one file, in order, when I run `python hw02/hw02_eda.py` from the repo root. Use pandas and matplotlib.

## What the script should do

1. Load `data/raw/fact_transactions.csv` into a pandas DataFrame.
2. Print the shape of the data (rows and columns).
3. Print every column name with its data type.
4. Print the number of missing values in every column.
5. Print descriptive statistics for all numeric columns: count, mean, standard deviation, min, 25th percentile, median, 75th percentile, and max.
6. Print the value counts for `txn_type` with the percentage each type makes up, sorted from most to least common.
7. Print how many unique clients, advisors, and securities appear in the file.
8. Print the earliest and latest `txn_date`, so I can see the date range the data covers.
9. Check for duplicate `txn_id` values and print how many there are.
10. Print the mean, median, and skewness of the `amount` column.
11. Group the data by `txn_type` and print the count, mean `amount`, and median `amount` for each type, rounded to 2 decimals and sorted by mean amount from highest to lowest.
12. Build a correlation matrix for `shares`, `price`, and `amount`, rounded to 2 decimals. Print it, then list the three strongest correlations between different variables (skip each variable's correlation with itself).
13. For each `txn_type`, print the minimum and maximum `shares` and how many rows have negative `shares`.
14. If the shape is anything other than 298,772 rows by 9 columns, print a clear warning.
15. Save three charts to `hw02/charts/` (create the folder if it doesn't exist):
    - `hist_amount.png`: a histogram of `amount` with vertical lines marking the mean and median, each labeled with its value.
    - `box_amount_by_type.png`: a horizontal box plot of `amount` for each `txn_type`.
    - `scatter_shares_amount.png`: a scatter plot with `shares` on the x-axis and `amount` on the y-axis, with points colored by `txn_type`.
    Every chart needs a title and axis labels.
16. Save a plain-text version of everything from steps 2 through 13 to `hw02/hw02_profile.txt`, so the results can be read without rerunning the script.
17. Put a comment block at the top of the script listing the script name, the dataset, the author (Brandon Le), and the date it was generated.

## Other requirements
- Leave the data as loaded. Do not convert data types, drop rows, or fill in missing values. The point is to see the data exactly as it arrives.
- Label each section of the terminal output clearly so it is easy to match to the steps above.
- Charts should be saved to files, not opened in pop-up windows.
- The script should finish in under a minute on about 300,000 rows.
