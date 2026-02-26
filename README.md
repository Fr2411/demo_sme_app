# SME Asset Manager Demo

## How to Run

1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Streamlit app:
   ```bash
   streamlit run app.py
   ```
4. Login with:
   - Username: `admin`
   - Password: `admin123`
5. Add purchased products and see dashboard update in real-time.

## Notes

- Products are stored in `products.csv`
- Users stored in `users.csv`
- Total asset value is calculated automatically
- Bar chart shows value per product
