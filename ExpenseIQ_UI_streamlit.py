import streamlit as st
import pandas as pd
import joblib
import os

# Sidebar navigation
r = st.sidebar.radio('Main Menu', ['Home', 'ExpenseIQ', 'Analysis'])

# ---------------- HOME ---------------- #
if r == 'Home':
    st.title('💰 ExpenseIQ - Smart Expense Analyzer')
    st.subheader("Welcome to analyze your bank statement! 🚀")

    st.markdown("""Tips to upload your bank statement: 😎
                
• Export your bank statement to excel format  
• Remove bank logo, name, address, legend  
• Keep only transaction table  
• Column should be named like Description/Narrative/Particulars/Transaction Remarks  
• For issues: https://www.linkedin.com/in/durgarmanikandan/
""")

    # FIXED: relative path
    st.image("assets/Image.jpeg")


# ---------------- EXPENSEIQ ---------------- #
if r == 'ExpenseIQ':
    st.title("💰 ExpenseIQ - Smart Expense Analyzer")

    # FIXED: correct model path
    model_path = os.path.join("models", "expense_model2.pkl")

    if not os.path.exists(model_path):
        st.error("Model file not found. Please check path.")
        st.stop()

    model = joblib.load(model_path)

    # Upload file
    file = st.file_uploader("Upload Bank Statement", type=["csv", "xlsx"])

    if file:
        # Read file
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df.columns = df.columns.str.strip()

        st.subheader("Raw Data")
        st.write(df.head())

        # ---------------- DYNAMIC COLUMN DETECTION ---------------- #
        try:
            remarks_col = [col for col in df.columns if col.lower() in
                           ["transaction remarks", "description", "narrative", "particulars"]][0]

            amount_col = [col for col in df.columns if
                          "withdrawal" in col.lower() or "debit" in col.lower()][0]
        except:
            st.error("Required columns not found. Please check your file format.")
            st.stop()

        # ---------------- PREPROCESSING ---------------- #
        df[remarks_col] = df[remarks_col].astype(str).str.lower().str.strip()

        # ---------------- PREDICTION ---------------- #
        df["Category"] = model.predict(df[remarks_col])

        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(df[remarks_col])
            df["Confidence"] = probs.max(axis=1)

        # ---------------- OUTPUT ---------------- #
        st.subheader("Categorized Data")
        st.write(df.head())

        # ---------------- SUMMARY ---------------- #
        st.subheader("Category Summary")
        summary = df.groupby("Category")[amount_col].sum().sort_values(ascending=False)
        st.bar_chart(summary)

        # ---------------- INSIGHTS ---------------- #
        st.subheader("Insights")

        top_category = summary.idxmax()
        top_amount = summary.max()

        st.metric("Total Spend", f"₹{df[amount_col].sum():,.0f}")
        st.write(f"💸 You spend most on **{top_category}**: ₹{top_amount:.0f}")

        st.write(df[df["Category"] == top_category][[remarks_col, amount_col]])

        # ---------------- OTHERS HANDLING ---------------- #
        if "Others" in df["Category"].values:
            st.warning("Some transactions are categorized as 'Others'.")

            others_df = df[df["Category"] == "Others"].copy()

            st.write("### Uncategorized Transactions")

            categories = [
                "Food", "Transport", "Shopping", "Bills & Payments",
                "Entertainment", "Cash Withdrawal", "Investment", "Income", "Others"
            ]

            # Add editable category column
            others_df["New_Category"] = others_df["Category"]

            edited_df = st.data_editor(others_df[[remarks_col, "New_Category"]], key="editor")

            # Update main df
            for i in edited_df.index:
                df.loc[i, "Category"] = edited_df.loc[i, "New_Category"]

            # ---------------- UPDATED SUMMARY ---------------- #
            st.subheader("Updated Category Summary")
            summary2 = df.groupby("Category")[amount_col].sum().sort_values(ascending=False)
            st.bar_chart(summary2)

        # ---------------- DOWNLOAD ---------------- #
        st.download_button(
            "Download Results",
            df.to_csv(index=False),
            file_name="categorized_expenses.csv"
        )

        # ---------------- SMART TIP ---------------- #
        if top_category in ["Food", "Shopping"]:
            st.info(f"⚡ Reducing {top_category} by 20% can save ₹{top_amount * 0.2:.0f}")
        else:
            st.info(f"⚡ Review your {top_category} expenses to optimize savings")

        # ---------------- SAVE FEEDBACK ---------------- #
        df.to_csv("user_corrected_data.csv", mode="a", header=False, index=False)