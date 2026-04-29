import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import seaborn as sns
import os

# Sidebar
r = st.sidebar.radio('Main Menu', ['Home', 'ExpenseIQ', 'Analysis'])
 

# ---------------- HOME ---------------- #
if r == 'Home':
    st.title('💰 ExpenseIQ - Smart Expense Analyzer')
    st.subheader("Welcome to analyze your bank statement! 🚀")

    st.markdown("""Tips to upload your bank statement: 😎
                
•   Export your bank statement to excel format

•   Remove all the bank logo, name, address details and legend

•   Keep only the table containing transaction data

•   Make sure the Transaction remarks column is named as Description/Narrative/Particulars/Transaction Remarks and amount column is named as Withdrawal Amount(INR) or contains 'debit' or 'withdrawal' in its name

•   In case of any error contact me https://www.linkedin.com/in/durgarmanikandan/

""")

    st.image("Image.jpeg")  # fixed


# ---------------- EXPENSEIQ ---------------- #
if r == 'ExpenseIQ':
    st.title("💰 ExpenseIQ - Smart Expense Analyzer")

    # FIXED path
    model_path = "expense_model2.pkl"

    if not os.path.exists(model_path):
        st.error("Model file not found")
        st.stop()

    model = joblib.load(model_path)

    file = st.file_uploader("Upload Bank Statement", type=["csv", "xlsx"])

    if file:
        # Read file
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        df.columns = df.columns.str.strip()
        st.session_state["df"] = df
        st.session_state["model"] = model 
        
        st.subheader("Raw Data")
        st.write(df.head())

        # Detect columns
        try:
            remarks_col = [c for c in df.columns if c.lower() in
                           ["transaction remarks", "description", "narrative", "particulars"]][0]

            amount_col = [c for c in df.columns if
                          "withdrawal" in c.lower() or "debit" in c.lower()][0]
        except:
            st.error("Required columns not found")
            st.stop()

        # Preprocess
        df[remarks_col] = df[remarks_col].astype(str).str.lower().str.strip()

        # Predict
        df["Category"] = model.predict(df[remarks_col])

        st.subheader("Categorized Data")
        st.write(df.head())

        # Summary
        summary = df.groupby("Category")[amount_col].sum().sort_values(ascending=False)
        st.bar_chart(summary)

        # Insights
        top_category = summary.idxmax()
        top_amount = summary.max()

        st.metric("Total Spend", f"₹{df[amount_col].sum():,.0f}")
        st.write(f"💸 Highest spend: **{top_category}** ₹{top_amount:.0f}")

        # ---------------- OTHERS FIXED ---------------- #
        if "Others" in df["Category"].values:

            st.warning("⚠️ Please classify 'Others' transactions")

            others_df = df[df["Category"] == "Others"]

            categories = [
                "Food", "Transport", "Shopping", "Bills & Payments",
                "Entertainment", "Cash Withdrawal", "Investment", "Income", "Others"
            ]

            updated = {}

            for idx, row in others_df.iterrows():
                choice = st.selectbox(
                    f"{row[remarks_col]} (₹{row[amount_col]})",
                    ["Select"] + categories,
                    key=f"cat_{idx}"
                )
                updated[idx] = choice

            # Apply button
            if st.button("Apply Changes"):

                if "Select" in updated.values():
                    st.error("Please select category for all rows")
                else:
                    for idx, val in updated.items():
                        df.loc[idx, "Category"] = val

                    st.success("Updated successfully!")

                    # Updated summary
                    summary2 = df.groupby("Category")[amount_col].sum().sort_values(ascending=False)
                    st.bar_chart(summary2)

        # Download
        st.download_button(
            "Download Results",
            df.to_csv(index=False),
            file_name="categorized_expenses.csv"
        )

        # Tip
        if top_category in ["Food", "Shopping"]:
            st.info(f"⚡ Save ₹{top_amount*0.2:.0f} by reducing {top_category}")
          
        
if r == 'Analysis':
    st.title("📊 ExpenseIQ - Analysis Dashboard")
    st.write("Detailed analysis of your spendings")
    
    df = st.session_state.get("df")
    st.write(df)
    
    # Group by Category and sum
    category_sum = df.groupby("Category")["Withdrawal Amount(INR)"].sum().reset_index()

    # Get top 5 categories by amount
    top5 = category_sum.sort_values(by="Withdrawal Amount(INR)", ascending=False).head(5)

    # Plot
    fig1, ax = plt.subplots(figsize=(10, 6))

    sns.barplot(
        x="Category",
        y="Withdrawal Amount(INR)",
        data=top5,
        ax=ax
    )

    plt.xticks(rotation=45)

    # Display the plot in Streamlit
    st.pyplot(fig1)
    
    #-----Figure 2-----insights
    # Calculate totals
    st.write("💡 Deposits Vs Withdrawal Insights")
    total_income = df["Deposit Amount(INR)"].sum() 
    total_expense = df["Withdrawal Amount(INR)"].sum()

    # Create dataframe for plotting
    summary_df = {
        "Type": ["Income", "Expense"],
        "Amount": [total_income, total_expense]
    }
    # Plot
    fig2, ax = plt.subplots(figsize=(6, 5))

    sns.barplot(
        x=["Income", "Expense"],
        y=[total_income, total_expense],
        ax=ax
    )

    for i, v in enumerate([total_income, total_expense]):
        ax.text(i, v, f"₹{v:,.0f}", ha='center', va='bottom')

    ax.set_title("💰 Income vs Expense Summary")
    st.pyplot(fig2)
    #-------Figure 3-----
    # Remove Income & Investments
    expense_df = df[~df["Category"].isin(["Income", "Investment"])]
    expense_summary = (
    expense_df
    .groupby("Category")["Withdrawal Amount(INR)"]
    .sum()
    .reset_index()
)

    fig3, ax = plt.subplots(figsize=(7, 7))

    ax.pie(
        expense_summary["Withdrawal Amount(INR)"],
        labels=expense_summary["Category"],
        autopct="%1.1f%%",
        startangle=90
    )

    ax.set_title("Expense Distribution (Excluding Income & Investments)")

    st.pyplot(fig3)