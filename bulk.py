import pandas as pd

def filter_fraud_transactions(file_path):
    # Load the dataset
    df = pd.read_csv(file_path)

    # Filter transactions that are either TRANSFER or CASH_OUT
    transfer_cashout = df[df['type'].isin(['TRANSFER', 'CASH_OUT'])]

    # Sort by step and ensure we are looking for transactions where cash_out comes after transfer
    transfer_cashout = transfer_cashout.sort_values(by=['step', 'amount', 'type'])

    # Group by 'step' and 'amount' to find matching transactions
    def filter_matching_transactions(group):
        # Ensure both TRANSFER and CASH_OUT exist in the group
        if 'TRANSFER' in group['type'].values and 'CASH_OUT' in group['type'].values:
            # Get the first TRANSFER and all CASH_OUT transactions that follow it
            transfer_idx = group.index[group['type'] == 'TRANSFER'][0]
            cash_out_after_transfer = group[(group.index > transfer_idx) & (group['type'] == 'CASH_OUT')]
            
            # Filter based on the amount being less than or equal to oldbalanceOrg
            transfer_cash_out_filtered = pd.concat([group.loc[[transfer_idx]], cash_out_after_transfer])
            amount_check = transfer_cash_out_filtered[
                transfer_cash_out_filtered['amount'] <= transfer_cash_out_filtered['oldbalanceOrg']
            ]
            
            # Also filter for zero balance conditions
            zero_balance_check = group[
                (group['oldbalanceOrg'] == 0) & (group['newbalanceOrig'] == 0) |
                (group['oldbalanceDest'] == 0) & (group['newbalanceDest'] == 0)
            ]
            
            # Combine both criteria
            return pd.concat([amount_check, zero_balance_check]).drop_duplicates()
        
        return pd.DataFrame()  # Return an empty DataFrame if no match

    # Apply the filter to each group of 'step' and 'amount'
    matching_transactions_6 = transfer_cashout.groupby(['step', 'amount'], group_keys=False).apply(filter_matching_transactions)

    # Optionally, save the filtered dataset to a new CSV
    filtered_file_path = '/path/to/save/matching_transactions_6.csv'
    matching_transactions_6.to_csv(filtered_file_path, index=False)

    # Return the path of the filtered file or the filtered dataframe
    return filtered_file_path
