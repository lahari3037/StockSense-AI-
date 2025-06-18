
# Main setup script

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'services'))

from backend.database import run_database_setup
from backend.services.stock_data_loader import run_stock_data_loader

def main():
    print("FinanceAI - Complete Database Setup")
    print("=" * 40)
    
    print("Step 1: Creating all database tables...")
    if not run_database_setup():
        print("Database setup failed")
        return False
    
    print("Step 2: Loading real stock company data...")
    if not run_stock_data_loader():
        print("Stock data loading failed")
        return False
    
    print("Setup completed successfully")
    print("Database now contains:")
    print("- Users table")
    print("- Transactions table") 
    print("- Budgets table")
    print("- Stocks table with real S&P 500 companies")
    print("- User_Stocks table")
    print("- AI_Insights table")
    print("- Files table")
    
    return True


if __name__ == "__main__":
    success = main()
    
    if not success:
        print("Setup failed")
        sys.exit(1)